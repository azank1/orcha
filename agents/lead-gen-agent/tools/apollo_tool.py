"""
Apollo.io tool — searches 270M+ contact database by role, industry, location, company size.
Docs: https://apolloio.github.io/apollo-api-docs/
"""
import asyncio
import hashlib
import json
import logging
import os
from urllib.parse import urlparse

import certifi
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.context import get_key

logger = logging.getLogger(__name__)

# Current People API Search (header auth only — never put the API key in the query string).
APOLLO_NEW_BASE = os.getenv(
    "APOLLO_API_BASE_URL", "https://api.apollo.io/api/v1"
).rstrip("/")
APOLLO_LEGACY_BASE = "https://api.apollo.io/v1"
APOLLO_LEGACY_PATH = "/mixed_people/search"
APOLLO_NEW_PATH = "/mixed_people/api_search"

# Simple in-process cache: cache_key → list[dict]
_cache: dict[str, list[dict]] = {}


class ApolloRateLimitError(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Apollo rate limited — retry after {retry_after}s")


# ── Apollo industry taxonomy mapper ──────────────────────────────────────────
# Apollo uses specific industry strings. Free-text industry names from the LLM
# often don't match, causing 0 results. Map common synonyms → Apollo values.

_INDUSTRY_MAP: list[tuple[list[str], str]] = [
    # Food & Beverage
    (["food manufacturing", "food production", "food processing", "food & bev",
      "food and beverage", "fmcg", "consumer goods", "packaged food", "beverages",
      "food industry", "food companies"], "food & beverages"),
    # Manufacturing
    (["manufacturing", "industrial manufacturing", "factory", "factories",
      "discrete manufacturing", "process manufacturing", "light manufacturing",
      "heavy manufacturing", "automotive", "aerospace"], "mechanical or industrial engineering"),
    # Retail
    (["retail", "ecommerce", "e-commerce", "online retail", "omnichannel",
      "consumer retail", "brick and mortar"], "retail"),
    # Wholesale / Distribution
    (["wholesale", "distribution", "wholesale distribution", "distributor",
      "supply chain distribution"], "wholesale"),
    # Logistics & Transport
    (["logistics", "supply chain", "freight", "shipping", "transportation",
      "trucking", "3pl", "warehousing"], "logistics and supply chain"),
    # Healthcare
    (["healthcare", "health care", "medical", "hospital", "clinic",
      "health services", "health system"], "hospital & health care"),
    # Pharma
    (["pharmaceutical", "pharma", "drug", "biotech", "biotechnology",
      "life sciences"], "pharmaceuticals"),
    # Construction / Real Estate
    (["construction", "building", "contractor", "general contractor",
      "engineering and construction"], "construction"),
    (["real estate", "property", "commercial real estate", "residential real estate",
      "realty", "property management"], "real estate"),
    # Legal
    (["legal", "law firm", "attorney", "law practice"], "legal services"),
    # Accounting / Finance
    (["accounting", "bookkeeping", "cpa", "audit"], "accounting"),
    (["finance", "financial services", "banking", "insurance",
      "investment", "asset management"], "financial services"),
    # Tech / SaaS
    (["saas", "software as a service", "software", "tech startup",
      "technology startup"], "computer software"),
    (["information technology", "it services", "managed services",
      "it consulting", "information technology and services"], "information technology and services"),
    # Professional Services
    (["professional services", "consulting", "management consulting",
      "business services", "advisory"], "management consulting"),
    # Education
    (["education", "edtech", "higher education", "k-12", "e-learning",
      "training"], "education management"),
    # Non-profit
    (["non-profit", "nonprofit", "ngo", "charity", "foundation"], "non-profit organization management"),
    # Hospitality
    (["hospitality", "hotel", "restaurant", "food service",
      "travel", "tourism"], "hospitality"),
    # Media
    (["media", "publishing", "advertising", "marketing agency",
      "digital marketing", "pr agency"], "marketing and advertising"),
    # Telecom
    (["telecom", "telecommunications", "wireless", "internet provider"], "telecommunications"),
    # Energy
    (["energy", "oil and gas", "utilities", "renewable energy",
      "solar", "wind energy"], "oil & energy"),
]

def _map_industries(industries: list[str]) -> list[str]:
    """
    Translate free-text industry names to Apollo's taxonomy strings.
    Passes through any value that already looks like an Apollo industry.
    """
    if not industries:
        return []
    mapped: list[str] = []
    for raw in industries:
        raw_lower = raw.lower().strip()
        hit = None
        for synonyms, apollo_value in _INDUSTRY_MAP:
            if any(syn in raw_lower or raw_lower in syn for syn in synonyms):
                hit = apollo_value
                break
        if hit:
            if hit not in mapped:
                mapped.append(hit)
            logger.info("Industry mapped: '%s' → '%s'", raw, hit)
        else:
            # Pass through unchanged — may already be valid Apollo taxonomy
            if raw not in mapped:
                mapped.append(raw)
    return mapped


def _apollo_headers(api_key: str) -> dict[str, str]:
    """
    Apollo.io: put the API key ONLY in HTTP headers (never as a URL/query parameter).

    Docs: Cache-Control no-cache + x-api-key + Content-Type.
    """
    key = (api_key or "").strip()
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "x-api-key": key,
    }


def _query_params_api_search(
    *,
    person_titles: list[str],
    mapped_industries: list[str],
    geographies: list[str],
    employee_ranges: list[str],
    page: int,
    per_page: int,
) -> list[tuple[str, str]]:
    """
    Filters for POST .../mixed_people/api_search (query string; API key stays in headers).

    https://docs.apollo.io/docs/find-people-using-filters
    """
    qp: list[tuple[str, str]] = []
    for t in person_titles:
        t = (t or "").strip()
        if t:
            qp.append(("person_titles[]", t))
    for loc in geographies or []:
        loc = (loc or "").strip()
        if loc:
            qp.append(("person_locations[]", loc))
    for ind in mapped_industries or []:
        ind = (ind or "").strip()
        if ind:
            qp.append(("q_organization_industries[]", ind))
    for er in employee_ranges or []:
        er = (er or "").strip()
        if er:
            qp.append(("organization_num_employees_ranges[]", er))
    qp.append(("page", str(max(1, page))))
    qp.append(("per_page", str(min(100, max(1, per_page)))))
    return qp


_SOCIAL_EMAIL_HOSTS = frozenset({
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "linktr.ee", "crunchbase.com",
})


def _hostname_only(raw: str) -> str:
    """Bare hostname suitable for Hunter email-finder (no scheme, lowercase, strip www.)."""
    s = (raw or "").strip()
    if not s:
        return ""
    # Already something like domain.com/foo without scheme → take first segment as host-ish
    if "://" not in s and "/" not in s:
        host = s.split("@")[-1]  # allow accidental pasted email-ish
        return host.strip().lower().removeprefix("www.")
    parsed = urlparse(s if "://" in s else f"https://{s}")
    host = (parsed.netloc or parsed.path.split("/")[0]).strip().lower()
    return host.removeprefix("www.") if host else ""


def _pick_company_hostname(org: dict, person: dict) -> str:
    """
    Prefer company email domain sources over Apollo's website_url, which often points at
    LinkedIn or marketing pages — Hunter cannot derive work emails from those hosts.
    """
    candidates = [
        org.get("primary_domain"),
        org.get("domain"),
        person.get("organization_domain"),
        org.get("website_url"),
    ]
    seen: list[str] = []
    for c in candidates:
        if not c:
            continue
        host = _hostname_only(str(c))
        if host and "." in host and host not in _SOCIAL_EMAIL_HOSTS:
            seen.append(host)
    return seen[0] if seen else ""


def _format_company_domain(org: dict, person: dict) -> str:
    """Canonical company web domain/host for enrichment + CRM (prefer real mail domain host)."""
    host = _pick_company_hostname(org, person)
    return host if host else ""


def _normalize_apollo_people(people: list[dict]) -> list[dict]:
    """Map Apollo people payloads (legacy or api_search) to Lead Gen lead dicts."""
    results: list[dict] = []
    for p in people:
        org = p.get("organization") or {}
        fn = (p.get("first_name") or "").strip()
        ln = (p.get("last_name") or "").strip()
        if not ln and p.get("last_name_obfuscated"):
            ln = str(p.get("last_name_obfuscated") or "").strip()
        results.append({
            "id": p.get("id"),
            "first_name": fn,
            "last_name": ln,
            "full_name": f"{fn} {ln}".strip(),
            "title": p.get("title", ""),
            "company": org.get("name", p.get("organization_name", "")),
            "company_domain": _format_company_domain(org, p),
            "company_size": org.get("estimated_num_employees"),
            "industry": org.get("industry", ""),
            "location": p.get("city", "") + (f", {p.get('country')}" if p.get("country") else ""),
            "email": p.get("email"),
            "email_status": p.get("email_status", "unknown"),
            "linkedin_url": p.get("linkedin_url", ""),
            "source": "apollo",
        })
    return results


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(min=2, max=60),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, ApolloRateLimitError)),
)
async def search_prospects(
    person_titles: list[str] | None = None,
    industries: list[str] | None = None,
    geographies: list[str] | None = None,
    company_size_min: int | None = None,
    company_size_max: int | None = None,
    per_page: int = 10,
) -> list[dict]:
    """
    Search Apollo for prospects matching the given criteria.
    Returns list of prospect dicts. Returns [] if no results — never returns mock data.
    """
    api_key = get_key("APOLLO_API_KEY")
    if not api_key:
        logger.warning("APOLLO_API_KEY not set — returning empty results (no mock)")
        return []

    # Normalise — caller may pass None when no titles are required
    person_titles = list(person_titles or [])

    # Map industry names to Apollo's taxonomy before searching
    mapped_industries = _map_industries(industries or [])

    # Cache check
    cache_key = hashlib.md5(
        json.dumps({
            "titles": sorted(person_titles),
            "industries": sorted(mapped_industries),
            "geo": sorted(geographies or []),
            "size_min": company_size_min,
            "size_max": company_size_max,
            "per_page": per_page,
        }, sort_keys=True).encode()
    ).hexdigest()

    if cache_key in _cache:
        logger.info("Apollo cache hit — skipping API call")
        return _cache[cache_key]

    employee_ranges: list[str] = []
    if company_size_min is not None and company_size_max is not None:
        employee_ranges = [f"{company_size_min},{company_size_max}"]

    search_mode = os.getenv("APOLLO_SEARCH_MODE", "auto").strip().lower()
    use_new = search_mode in ("auto", "new")
    use_legacy = search_mode in ("auto", "legacy")

    logger.info(
        "Apollo search: mode=%s titles=%s geo=%s industries_raw=%s industries_mapped=%s per_page=%d",
        search_mode,
        person_titles,
        geographies,
        industries,
        mapped_industries,
        per_page,
    )

    hdrs = _apollo_headers(api_key)
    payload_legacy = {
        "q_organization_industries": mapped_industries,
        "person_titles": person_titles,
        "person_locations": geographies or [],
        "organization_num_employees_ranges": employee_ranges,
        "per_page": per_page,
        "page": 1,
    }

    def _apollo_inaccessible_message(txt: str) -> bool:
        t = txt.lower()
        return "api_inaccessible" in t or "not accessible with this api_key" in t

    async def _post_json(url: str, body: dict) -> tuple[int, dict]:
        async with httpx.AsyncClient(timeout=30.0, verify=certifi.where()) as client:
            resp = await client.post(url, json=body, headers=hdrs)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            logger.warning("Apollo rate limited (429) — waiting %ds before retry", retry_after)
            await asyncio.sleep(min(retry_after, 60))
            raise ApolloRateLimitError(retry_after)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        return resp.status_code, data

    async def _post_api_search(qp: list[tuple[str, str]]) -> tuple[int, dict, str]:
        """People API Search — filters as query params; api key ONLY in headers."""
        async with httpx.AsyncClient(timeout=30.0, verify=certifi.where()) as client:
            resp = await client.post(
                f"{APOLLO_NEW_BASE}{APOLLO_NEW_PATH}",
                headers=hdrs,
                params=qp,
            )
        raw_txt = resp.text[:500] if resp.text else ""
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            logger.warning("Apollo rate limited (429) — waiting %ds before retry", retry_after)
            await asyncio.sleep(min(retry_after, 60))
            raise ApolloRateLimitError(retry_after)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        return resp.status_code, data, raw_txt

    people_raw: list[dict] = []

    if use_new:
        qp_full = _query_params_api_search(
            person_titles=person_titles,
            mapped_industries=mapped_industries,
            geographies=geographies or [],
            employee_ranges=employee_ranges,
            page=1,
            per_page=per_page,
        )
        status, data, txt = await _post_api_search(qp_full)

        if status in (401, 403):
            err = json.dumps(data) if data else txt
            if isinstance(data, dict) and data.get("error_code") == "API_INACCESSIBLE":
                logger.error(
                    "Apollo People API Search not permitted for this API key — "
                    "create a Master API key with api_search scope (Apollo Settings → API), "
                    "or use APOLLO_SEARCH_MODE=legacy if your key only supports the older endpoint."
                )
            elif _apollo_inaccessible_message(err):
                logger.warning(
                    "mixed_people/api_search not accessible for this key — will try legacy if enabled"
                )
            else:
                logger.error(
                    "Apollo api_search rejected (%s): %s", status, err[:280]
                )
            if search_mode == "new":
                return []

        if status >= 400 and search_mode == "new":
            logger.warning("Apollo api_search HTTP %s: %s", status, txt[:300])
            return []

        if status == 200:
            people_raw = list(data.get("people") or [])

        if status == 200 and not people_raw and mapped_industries:
            logger.info(
                "Apollo api_search returned 0 with industry filters — retrying without industries"
            )
            qp_broad = _query_params_api_search(
                person_titles=person_titles,
                mapped_industries=[],
                geographies=geographies or [],
                employee_ranges=employee_ranges,
                page=1,
                per_page=per_page,
            )
            st2, data2, txt2 = await _post_api_search(qp_broad)
            if st2 == 200:
                people_raw = list(data2.get("people") or [])
                if not people_raw:
                    logger.info("Apollo broader api_search still 0 prospects: %s", txt2[:200])

        if people_raw:
            results = _normalize_apollo_people(people_raw)
            logger.info(
                "Apollo api_search returned %d prospects for industries=%s",
                len(results),
                mapped_industries,
            )
            _cache[cache_key] = results
            return results

        if search_mode == "new":
            logger.info("Apollo api_search yielded no prospects")
            return []
        logger.info("Falling back to legacy POST %s%s", APOLLO_LEGACY_BASE, APOLLO_LEGACY_PATH)

    if use_legacy:
        st, pdata = await _post_json(
            f"{APOLLO_LEGACY_BASE}{APOLLO_LEGACY_PATH}",
            payload_legacy,
        )

        if st in (401, 403):
            body = pdata
            if body.get("error_code") == "API_INACCESSIBLE":
                logger.error(
                    "Apollo legacy search endpoint not accessible — upgrade plan "
                    "or configure Hunter/Google Maps fallback."
                )
            else:
                logger.error(
                    "Apollo legacy auth error %s — verify APOLLO_API_KEY and API access",
                    st,
                )
            return []

        if not (200 <= st < 300):
            logger.warning("Apollo legacy API returned %s: %s", st, json.dumps(pdata)[:300])
            return []

        people_raw = list(pdata.get("people") or [])
        logger.info(
            "Apollo legacy returned %d prospects for industries=%s",
            len(people_raw),
            mapped_industries,
        )

        if not people_raw and mapped_industries:
            logger.info(
                "Apollo legacy returned 0 with industry filter — retrying without industry constraint"
            )
            broader = {k: v for k, v in payload_legacy.items() if k != "q_organization_industries"}
            st2, pdata2 = await _post_json(
                f"{APOLLO_LEGACY_BASE}{APOLLO_LEGACY_PATH}",
                broader,
            )
            if 200 <= st2 < 300:
                people_raw = list(pdata2.get("people") or [])
                logger.info("Apollo legacy broader search returned %d prospects", len(people_raw))

        if not people_raw:
            logger.info("Apollo (all modes) returned 0 results — returning empty list (no mock)")
            return []

        results = _normalize_apollo_people(people_raw)
        _cache[cache_key] = results
        return results

    return []
