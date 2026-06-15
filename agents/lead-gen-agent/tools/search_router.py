"""
Smart search router — routes queries to the right source(s) and falls back
when the primary returns too few results.

Priority chain:
  Local / SMB / Traditional query:
    1. Google Maps  (primary)
    2. Apollo       (secondary — catches SMBs that have a LinkedIn presence)
    3. Maps retry   (broader query if both above return < MIN_RESULTS)

  Global / B2B query:
    1. Apollo + Hunter (parallel)
    2. If Apollo returns zero: Google Maps + Hunter (relaxed titles) immediately
    3. Extra Maps / relaxed Hunter rounds if merged count stays low

  Hunter also retries without title filters when strict titles match no emails.

No source ever returns mock data.  Empty list = genuinely no results.
"""
import asyncio
import re
import logging
from typing import Literal

from core.context import get_key

logger = logging.getLogger(__name__)

# Minimum results before we try to broaden the search
_MIN_RESULTS = 3

# ── Mode detection signals ────────────────────────────────────────────────────
# Ordered from most specific to most general.
# Score: each matching pattern adds weight to local or global.

_LOCAL_GEOGRAPHY = [
    # Named cities / regions (expanded beyond original)
    r"\b(lahore|karachi|islamabad|rawalpindi|faisalabad|multan|peshawar|quetta)\b",
    r"\b(dubai|abu dhabi|sharjah|riyadh|jeddah|doha|muscat|kuwait)\b",
    r"\b(london|manchester|birmingham|glasgow|edinburgh|leeds|bristol|liverpool)\b",
    r"\b(delhi|mumbai|bangalore|hyderabad|chennai|pune|kolkata|ahmedabad|surat)\b",
    r"\b(new york|los angeles|chicago|houston|phoenix|dallas|san antonio|seattle|boston)\b",
    r"\b(toronto|montreal|vancouver|calgary|ottawa|edmonton|winnipeg)\b",
    r"\b(sydney|melbourne|brisbane|perth|adelaide|auckland|christchurch)\b",
    r"\b(berlin|munich|hamburg|frankfurt|paris|amsterdam|madrid|rome|barcelona)\b",
    r"\b(nairobi|lagos|accra|johannesburg|cape town|casablanca|cairo|addis ababa)\b",
    r"\b(dhaka|colombo|kathmandu|yangon|jakarta|manila|bangkok|ho chi minh)\b",
    # Generic location indicators
    r"\bin\s+[\w\s]{2,30}(?:,\s*[\w\s]{2,20})?\b",  # "in Austin, Texas"
    r"\bnear\s+\w+\b",
    r"\bnearby\b",
    r"\blocal\b",
    r"\bmy (city|town|area|region|neighbourhood|neighborhood|county|district)\b",
    r"\brural\b",
    r"\bsmall.?town\b",
    r"\bvillage\b",
    r"\bsuburb(an|s)?\b",
    r"\bdowntown\b",
    r"\bright\s+here\b",
]

_LOCAL_BUSINESS_TYPES = [
    # Food & hospitality
    r"\b(restaurants?|cafes?|coffee shops?|bakeries?|diners?|eateries?|takeaways?)\b",
    r"\b(hotels?|motels?|guesthouses?|lodges?|resorts?|bed.and.breakfasts?|b&bs?)\b",
    r"\b(bars?|pubs?|taverns?|nightclubs?|lounges?)\b",
    # Health & wellness
    r"\b(clinics?|hospitals?|pharmacies?|dentists?|opticians?|chiropractors?|therapists?)\b",
    r"\b(gyms?|fitness centres?|yoga studios?|pilates?|personal trainers?)\b",
    r"\b(spas?|beauty salons?|hair salons?|barbershops?|nail salons?)\b",
    # Retail & trades
    r"\b(shops?|stores?|boutiques?|outlets?|markets?|supermarkets?)\b",
    r"\b(plumbers?|electricians?|contractors?|builders?|roofers?|painters?|handymen?)\b",
    r"\b(mechanics?|garages?|auto repair|car repair|body shops?)\b",
    r"\b(florists?|nurseries?|garden centres?)\b",
    # Professional local services
    r"\b(law firms?|solicitors?|attorneys?|legal offices?)\b",
    r"\b(accountants?|bookkeepers?|cpas?|tax advisors?)\b",
    r"\b(real estate agents?|property dealers?|estate agents?|realtors?)\b",
    r"\b(insurance agents?|financial advisors?|mortgage brokers?)\b",
    # Education & community
    r"\b(schools?|academies?|colleges?|tutors?|coaching centres?|nurseries?|daycares?)\b",
    r"\b(churches?|mosques?|temples?|synagogues?|religious organisations?)\b",
    r"\b(gyms?|sports clubs?|recreational centres?)\b",
    # Agriculture & rural
    r"\b(farms?|farmers?|ranches?|dairies?|orchards?|vineyards?|greenhouses?)\b",
    r"\b(agricultural|farming|livestock|poultry|fisheries?|fishing)\b",
    r"\b(feed stores?|grain elevators?|co-ops?|cooperatives?)\b",
    # SMB / traditional
    r"\b(smbs?|small businesses?|local businesses?|family businesses?|independent businesses?)\b",
    r"\b(sole traders?|freelancers?|self.employed|solopreneurs?)\b",
    r"\b(tradespeople|tradesman|craftsmen?|artisans?)\b",
    r"\b(manufacturers?|workshops?|factories?|fabricators?)\b",
    r"\b(wholesalers?|distributors?|suppliers?|vendors?)\b",
    r"\b(cleaning services?|laundries?|dry cleaners?|pest control)\b",
    r"\b(funeral homes?|cemeteries?|crematoriums?)\b",
    r"\b(vets?|veterinarians?|animal clinics?|pet shops?)\b",
]

_GLOBAL_ROLE = [
    r"\b(cto|ceo|cfo|coo|ciso|cmo|cpo|cdo)\b",
    r"\b(vp|svp|evp|avp)\s+\w+",
    r"\b(director|head of|chief|officer)\b",
    r"\b(founder|co-founder|cofounder)\b",
    r"\b(engineer|developer|architect|data scientist)\b",
    r"\b(decision maker|executive|c-suite|c suite|leadership team)\b",
    r"\b(sales manager|marketing manager|product manager|account executive)\b",
]

_SMB_SIGNALS = [
    r"\bsmb\b", r"\bsme\b",
    r"\bsmall.?medium\b",
    r"\btraditional\b",
    r"\bestablished\b",
    r"\brick.and.mortar\b",
    r"\bbrick and mortar\b",
    r"\bnon.?tech\b",
    r"\bnot.?tech\b",
    r"\bno.?tech\b",
    r"\bold.?school\b",
    r"\boffline\b",
]

_LOCAL_COMPILED  = [re.compile(p, re.IGNORECASE) for p in _LOCAL_GEOGRAPHY + _LOCAL_BUSINESS_TYPES]
_GLOBAL_COMPILED = [re.compile(p, re.IGNORECASE) for p in _GLOBAL_ROLE]
_SMB_COMPILED    = [re.compile(p, re.IGNORECASE) for p in _SMB_SIGNALS]

# Outreach intent signals → prefer global/Hunter even for "local business" queries
# because Hunter finds decision-maker emails; Maps finds no emails at all.
_OUTREACH_SIGNALS = [re.compile(p, re.IGNORECASE) for p in [
    r"\bemail\b", r"\boutreach\b", r"\bcontact\b", r"\bpitch\b", r"\breach out\b",
    r"\bsend.*email\b", r"\bemail.*them\b", r"\bcold email\b",
]]


def detect_mode(query: str) -> Literal["local", "global"]:
    """
    Determine whether a query targets local/SMB businesses or global B2B professionals.

    SMB / traditional / rural signals force local mode regardless of role mentions,
    because someone asking for "small manufacturing firms in Detroit" is not doing
    a typical Apollo B2B search.

    Exception: queries with email/outreach intent route to global even for local
    business targets, because Hunter finds emails and Maps does not.
    """
    smb_hits      = sum(1 for p in _SMB_COMPILED      if p.search(query))
    local_hits    = sum(1 for p in _LOCAL_COMPILED    if p.search(query))
    global_hits   = sum(1 for p in _GLOBAL_COMPILED   if p.search(query))
    outreach_hits = sum(1 for p in _OUTREACH_SIGNALS  if p.search(query))

    # SMB/traditional keywords strongly bias toward local/Maps
    if smb_hits > 0:
        local_hits += smb_hits * 2

    # Outreach intent shifts toward global: Hunter finds emails, Maps doesn't
    if outreach_hits > 0:
        global_hits += outreach_hits * 3

    mode: Literal["local", "global"] = "local" if local_hits > global_hits else "global"
    logger.info(
        "detect_mode: '%s' → %s (local=%d global=%d smb=%d outreach=%d)",
        query[:60], mode, local_hits, global_hits, smb_hits, outreach_hits,
    )
    return mode


# ── Individual source wrappers ────────────────────────────────────────────────

async def _apollo(kwargs: dict) -> list[dict]:
    try:
        from tools.apollo_tool import search_prospects
        results = await search_prospects(
            person_titles=kwargs.get("person_titles") or [],
            industries=kwargs.get("industries"),
            geographies=kwargs.get("geographies"),
            company_size_min=kwargs.get("company_size_min"),
            company_size_max=kwargs.get("company_size_max"),
            per_page=kwargs.get("per_page", 25),
        )
        logger.info("Apollo: %d results", len(results))
        return results
    except Exception as exc:
        logger.warning("Apollo failed: %s", exc)
        return []


async def _hunter(kwargs: dict) -> list[dict]:
    try:
        from tools.hunter_tool import search_prospects
        results = await search_prospects(
            person_titles=kwargs.get("person_titles") or [],
            industries=kwargs.get("industries"),
            geographies=kwargs.get("geographies"),
            company_size_min=kwargs.get("company_size_min"),
            company_size_max=kwargs.get("company_size_max"),
            per_page=kwargs.get("per_page", 25),
        )
        logger.info("Hunter: %d results", len(results))
        return results
    except Exception as exc:
        logger.warning("Hunter failed: %s", exc)
        return []


async def _google_maps(query: str, kwargs: dict) -> list[dict]:
    try:
        from tools.google_maps_tool import search_local_businesses
        results = await search_local_businesses(
            query=query,
            max_results=kwargs.get("max_results", 20),
        )
        logger.info("Google Maps: %d results", len(results))
        return results
    except Exception as exc:
        logger.warning("Google Maps failed: %s", exc)
        return []


def _broaden_query(query: str) -> str | None:
    """
    Strip the most specific location term to broaden a query.
    "plumbers in Springfield, Illinois" → "plumbers in Illinois"
    "farms in rural Iowa County Wisconsin" → "farms in Wisconsin"
    Returns None if can't meaningfully broaden.
    """
    # Remove city/town (text before comma in "X in City, State")
    m = re.search(r"(in|near)\s+([\w\s]+),\s*([\w\s]+)", query, re.IGNORECASE)
    if m:
        broadened = f"{query[:m.start()]}{m.group(1)} {m.group(3).strip()}"
        if broadened.strip().lower() != query.strip().lower():
            return broadened.strip()

    # Remove "rural", "small", "local" qualifiers
    stripped = re.sub(r"\b(rural|local|small.?town|nearby|traditional)\b\s*", "", query, flags=re.IGNORECASE).strip()
    if stripped.lower() != query.lower():
        return stripped

    return None


# ── Merge & deduplicate ───────────────────────────────────────────────────────

def _dedup_key(lead: dict) -> str:
    email   = (lead.get("email") or "").strip().lower()
    if email:
        return email
    name    = (lead.get("full_name") or lead.get("name") or "").strip().lower()
    company = (lead.get("company") or "").strip().lower()
    phone   = (lead.get("phone") or "").strip()
    # For local businesses without email, phone is the best dedup key
    if phone:
        return f"phone:{phone}"
    return f"{name}|{company}"


def _merge(priority_order: list[list[dict]]) -> list[dict]:
    seen: set[str] = set()
    merged: list[dict] = []
    for batch in priority_order:
        for lead in batch:
            key = _dedup_key(lead)
            if key and key not in seen:
                seen.add(key)
                merged.append(lead)
    return merged


def _source_append(sources: list[str], name: str) -> None:
    if name not in sources:
        sources.append(name)


# ── Main router ───────────────────────────────────────────────────────────────

async def smart_search(query: str, **kwargs) -> dict:
    """
    Adaptive search with fallback chain.

    Local / SMB / Traditional mode:
      Round 1 — Google Maps (primary) + Apollo in parallel
      Round 2 — broaden Maps query
      Round 3 — type-only Maps query
      Round 4 — Hunter (universal fallback — always has data)

    Global B2B mode:
      Round 1 — Apollo + Hunter in parallel (Hunter auto-relaxes titles if needed)
      If Apollo yields zero rows: Google Maps + optional relaxed Hunter merge right away
      Further Maps / Hunter rounds while merged count stays below MIN_RESULTS
    """
    mode          = detect_mode(query)
    fallback_used = False
    sources_hit: list[str] = []

    if mode == "local":
        # ── Round 1: Maps primary ──────────────────────────────────────────
        maps_r1, apollo_r1 = await asyncio.gather(
            _google_maps(query, kwargs),
            _apollo({**kwargs, "per_page": kwargs.get("per_page", 15)}),
        )
        merged = _merge([maps_r1, apollo_r1])
        if maps_r1:
            sources_hit.append("google_maps")
        if apollo_r1:
            sources_hit.append("apollo")

        # ── Round 2: broaden Maps query ────────────────────────────────────
        if len(merged) < _MIN_RESULTS:
            broader = _broaden_query(query)
            if broader and broader != query:
                logger.info("smart_search: local round-2 broader query: '%s'", broader)
                maps_r2 = await _google_maps(broader, kwargs)
                merged  = _merge([merged, maps_r2])
                if maps_r2:
                    fallback_used = True

        # ── Round 3: type-only Maps search ────────────────────────────────
        if len(merged) < _MIN_RESULTS:
            stripped = re.sub(
                r"\b(in|near|around|from|at)\b\s+[\w\s,]{2,40}",
                "", query, flags=re.IGNORECASE,
            ).strip()
            if stripped and stripped.lower() != query.lower():
                logger.info("smart_search: local round-3 type-only query: '%s'", stripped)
                maps_r3 = await _google_maps(stripped, {**kwargs, "max_results": 20})
                merged  = _merge([merged, maps_r3])
                if maps_r3:
                    fallback_used = True

        # ── Round 4: Hunter fallback (always has data) ─────────────────────
        if len(merged) < _MIN_RESULTS:
            logger.info("smart_search: local round-4 Hunter fallback for query: '%s'", query)
            hunter_r4 = await _hunter(kwargs)
            merged     = _merge([merged, hunter_r4])
            if hunter_r4:
                fallback_used = True
                sources_hit.append("hunter")

        logger.info(
            "smart_search [local]: maps=%d apollo=%d merged=%d fallback=%s",
            len(maps_r1), len(apollo_r1), len(merged), fallback_used,
        )

    else:
        # ── Round 1: Apollo + Hunter primary ──────────────────────────────
        apollo_r1, hunter_r1 = await asyncio.gather(
            _apollo(kwargs),
            _hunter(kwargs),
        )
        merged = _merge([apollo_r1, hunter_r1])
        if apollo_r1:
            _source_append(sources_hit, "apollo")
        if hunter_r1:
            _source_append(sources_hit, "hunter")

        apollo_empty = len(apollo_r1) == 0
        maps_added_round2 = False
        did_relaxed_hunter = False

        # Apollo miss — immediately blend Maps + (if needed) relaxed Hunter
        if apollo_empty:
            pp = max(int(kwargs.get("per_page") or 25), 15)
            maps_boost = await _google_maps(query, kwargs)
            merged = _merge([merged, maps_boost])
            if maps_boost:
                _source_append(sources_hit, "google_maps")
                maps_added_round2 = True
                fallback_used = True
            relaxed_kw = {
                **kwargs,
                "person_titles": [],
                "per_page": pp,
            }
            if (not hunter_r1) or len(merged) < _MIN_RESULTS:
                logger.info(
                    "smart_search: Apollo returned 0 — merging relaxed Hunter fallback"
                )
                hunter_boost = await _hunter(relaxed_kw)
                merged = _merge([merged, hunter_boost])
                if hunter_boost:
                    _source_append(sources_hit, "hunter")
                    fallback_used = True
                did_relaxed_hunter = True

        # Maps when merge count still low (and we did not already add Maps via Apollo empty path)
        if len(merged) < _MIN_RESULTS and not maps_added_round2:
            logger.info("smart_search: global Maps fallback for low merge count")
            maps_r2 = await _google_maps(query, kwargs)
            merged = _merge([merged, maps_r2])
            if maps_r2:
                _source_append(sources_hit, "google_maps")
                fallback_used = True

        if len(merged) < _MIN_RESULTS and not did_relaxed_hunter:
            logger.info("smart_search: global Hunter without title filter")
            relaxed = {k: v for k, v in kwargs.items() if k != "person_titles"}
            hunter_r3 = await _hunter(relaxed)
            merged = _merge([merged, hunter_r3])
            if hunter_r3:
                _source_append(sources_hit, "hunter")
                fallback_used = True

        logger.info(
            "smart_search [global]: apollo=%d hunter=%d merged=%d fallback=%s",
            len(apollo_r1), len(hunter_r1), len(merged), fallback_used,
        )

    notes: list[str] = []
    apollo_ok = bool(get_key("APOLLO_API_KEY"))
    hunter_ok = bool(get_key("HUNTER_API_KEY"))
    if not apollo_ok:
        notes.append(
            "Apollo.io is not configured (APOLLO_API_KEY missing); "
            "results rely on Hunter.io and/or Google Maps when available."
        )
    elif (
        hunter_ok and mode == "global" and "apollo" not in sources_hit and merged
    ):
        notes.append(
            "Apollo returned no usable rows this run — leads came from `sources` "
            "(typically hunter via domain-search and/or google_maps). "
            "In your summary, reflect those providers; do not describe this as "
            "\"no results\" while `count` is positive."
        )

    if not merged:
        logger.warning(
            "smart_search: all sources returned 0 for query='%s' — "
            "check: Google Maps billing enabled? Apollo paid plan? Hunter API key valid?",
            query[:80],
        )

    return {
        "mode":               mode,
        "sources":            sources_hit,
        "results":            merged,
        "count":              len(merged),
        "query":              query,
        "fallback_used":      fallback_used,
        "apollo_key_present": bool(get_key("APOLLO_API_KEY")),
        "hunter_key_present": bool(get_key("HUNTER_API_KEY")),
        "search_notes":       notes,
    }
