"""
Hunter.io tool — finds and verifies professional email addresses.
Primary prospect search via domain-search; email finder/verifier as secondary.
Docs: https://hunter.io/api-documentation
"""
import asyncio
import logging
import re
from urllib.parse import urlparse

import certifi
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.context import get_key

logger = logging.getLogger(__name__)

HUNTER_BASE = "https://api.hunter.io/v2"

_BLOCKED_HUNTER_HOSTS = frozenset({
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "googlegroups.com", "tinyurl.com",
})


def _normalize_domain_argument(domain: str) -> tuple[str, str]:
    """
    Normalize company domain from Apollo/UI (`stripe.com`, `https://stripe.com/about`).
    Returns (clean_domain_host, error_status). nonempty error_status => skip Hunter.
    """
    raw = ((domain or "").strip().replace("\\", "/"))
    if not raw:
        return "", "no_domain"
    if "@" in raw and not raw.startswith("@"):
        raw = raw.rsplit("@", 1)[-1].strip()

    if raw.startswith(("http://", "https://")):
        host = urlparse(raw).hostname
    elif "://" in raw:
        host = urlparse(raw).hostname
    else:
        host = raw.split("/")[0].strip() or None
    if not host:
        return "", "invalid_domain"
    hl = host.lower().removeprefix("www.").strip(".")
    if hl.startswith("@"):
        hl = hl.lstrip("@")
    if "." not in hl:
        return "", "invalid_domain"
    if hl in _BLOCKED_HUNTER_HOSTS:
        return "", "blocked_host"
    return hl, ""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
)
async def find_email(
    first_name: str,
    last_name: str,
    domain: str,
) -> dict:
    """
    Find email for a person at a given domain.
    Returns {email, confidence, status} or {email: None} if not found.
    """
    api_key = get_key("HUNTER_API_KEY")
    if not api_key:
        logger.warning("HUNTER_API_KEY not set — returning no result")
        return {"email": None, "confidence": 0, "status": "no_key"}

    domain_clean, dom_err = _normalize_domain_argument(domain)
    if dom_err:
        logger.info(
            "Hunter skipped — domain normalization: %s (input=%r)", dom_err, domain[:120]
        )
        return {"email": None, "confidence": 0, "status": dom_err}

    logger.info(f"Hunter lookup: {first_name} {last_name} @ {domain_clean}")

    async with httpx.AsyncClient(timeout=10.0, verify=certifi.where()) as client:
        response = await client.get(
            f"{HUNTER_BASE}/email-finder",
            params={
                "domain": domain_clean,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": api_key,
            },
        )

    if response.status_code == 404:
        return {"email": None, "confidence": 0, "status": "not_found"}

    if response.status_code >= 400:
        body = response.text[:300] if response.text else ""
        logger.warning(
            "Hunter email-finder HTTP %s for domain=%s: %s",
            response.status_code,
            domain_clean,
            body,
        )
        return {
            "email": None,
            "confidence": 0,
            "status": "hunter_http_error",
            "http_status": response.status_code,
        }

    try:
        data = response.json().get("data", {})
    except Exception:
        logger.warning("Hunter email-finder invalid JSON")
        return {"email": None, "confidence": 0, "status": "invalid_response"}

    result = {
        "email": data.get("email"),
        "confidence": data.get("score", 0),
        "status": data.get("status", "unknown"),
    }
    logger.info(f"Hunter result: {result['email']} (confidence: {result['confidence']})")
    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
)
async def verify_email(email: str) -> dict:
    """Verify if an existing email address is deliverable."""
    api_key = get_key("HUNTER_API_KEY")
    if not api_key:
        logger.warning("HUNTER_API_KEY not set — skipping email verification")
        return {"email": email, "status": "unverified", "score": 0}

    async with httpx.AsyncClient(timeout=10.0, verify=certifi.where()) as client:
        response = await client.get(
            f"{HUNTER_BASE}/email-verifier",
            params={"email": email, "api_key": api_key},
        )
        response.raise_for_status()

    data = response.json().get("data", {})
    return {
        "email": email,
        "status": data.get("status", "unknown"),
        "score": data.get("score", 0),
    }


def _mock_email(first_name: str, last_name: str, domain: str) -> dict:
    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
    return {"email": email, "confidence": 75, "status": "valid"}


# ── Prospect search via domain-search ─────────────────────────────────────────

# ── Multi-industry domain database ────────────────────────────────────────────
# Hunter domain-search returns real crawled emails. We pick domains based on
# the requested industry so results are relevant to the caller's query.
_INDUSTRY_DOMAINS: dict[str, list[str]] = {
    "saas": [
        "activepieces.com", "trigger.dev", "windmill.dev", "buildship.com",
        "relay.app", "lindy.ai", "inngest.com", "novu.co", "sequin.io",
        "superblocks.com", "langfuse.com", "agentops.ai", "e2b.dev",
        "retool.com", "bubble.io", "webflow.com", "airtable.com", "notion.so",
        "zapier.com", "make.com", "monday.com", "clickup.com", "linear.app",
        "figma.com", "loom.com", "miro.com", "calendly.com", "typeform.com",
        "intercom.com", "freshworks.com", "zendesk.com", "hubspot.com",
        "pipedrive.com", "close.com", "lemlist.com", "apollo.io",
    ],
    "fintech": [
        "stripe.com", "brex.com", "mercury.com", "ramp.com", "pilot.com",
        "rippling.com", "gusto.com", "plaid.com", "unit.co", "column.com",
        "lithic.com", "modern-treasury.com", "synctera.com", "treasuryprime.com",
        "marqeta.com", "adyen.com", "checkout.com", "payoneer.com",
        "wise.com", "revolut.com", "monzo.com", "n26.com", "chime.com",
    ],
    "healthcare": [
        "abridge.com", "nuance.com", "doximity.com", "athenahealth.com",
        "healthgrades.com", "zocdoc.com", "teladoc.com", "hims.com",
        "ro.co", "cohere.health", "collectivemedical.com", "arcadian.ai",
        "aidoc.com", "intelerad.com", "ambra.com", "weave.com",
        "patientco.com", "phynd.com", "experity.com",
    ],
    "ecommerce": [
        "shopify.com", "bigcommerce.com", "woocommerce.com", "klaviyo.com",
        "gorgias.com", "recharge.com", "yotpo.com", "loop.com",
        "netsuite.com", "brightpearl.com", "skubana.com", "linnworks.com",
        "brightpearl.com", "cin7.com", "extensiv.com",
    ],
    "marketing": [
        "semrush.com", "ahrefs.com", "moz.com", "sproutsocial.com",
        "hootsuite.com", "buffer.com", "later.com", "brandwatch.com",
        "mention.com", "conductor.com", "brightedge.com", "bazaarvoice.com",
        "contentful.com", "sitecore.com", "optimizely.com", "unbounce.com",
    ],
    "logistics": [
        "flexport.com", "shipbob.com", "easypost.com", "shipstation.com",
        "aftership.com", "project44.com", "fourkites.com", "turvo.com",
        "transfix.com", "convoy.com", "loadsmart.com", "echo.com",
    ],
    "cybersecurity": [
        "crowdstrike.com", "sentinelone.com", "lacework.com", "orca.security",
        "wiz.io", "snyk.io", "veracode.com", "checkmarx.com",
        "noname.security", "apiiro.com", "armorcode.com", "brinqa.com",
        "axonius.com", "armis.com", "claroty.com", "dragos.com",
    ],
    "hr": [
        "greenhouse.io", "lever.co", "workday.com", "bamboohr.com",
        "lattice.com", "culture-amp.com", "leapsome.com", "betterworks.com",
        "15five.com", "visier.com", "personio.com", "hibob.com",
        "deel.com", "remote.com", "multiplier.com", "oysterhr.com",
    ],
    "devtools": [
        "github.com", "gitlab.com", "circleci.com", "travis-ci.com",
        "datadog.com", "grafana.com", "pagerduty.com", "opsgenie.com",
        "sentry.io", "honeycomb.io", "lightstep.com", "newrelic.com",
        "hashicorp.com", "chef.io", "puppet.com", "ansible.com",
        "pulumi.com", "env0.com", "spacelift.io", "atlantis.run",
    ],
    "ai": [
        "openai.com", "anthropic.com", "cohere.com", "ai21.com",
        "huggingface.co", "scale.com", "labelbox.com", "snorkel.ai",
        "weights-and-biases.com", "determined.ai", "predibase.com",
        "together.ai", "anyscale.com", "modal.com", "banana.dev",
        "replicate.com", "runwayml.com", "stability.ai", "midjourney.com",
    ],
    "consulting": [
        "mckinsey.com", "bcg.com", "bain.com", "accenture.com", "deloitte.com",
        "kpmg.com", "ey.com", "pwc.com", "slalom.com", "cognizant.com",
        "infosys.com", "wipro.com", "tcs.com", "thoughtworks.com",
    ],
    "real_estate": [
        "cbre.com", "jll.com", "cushwake.com", "colliers.com",
        "redfin.com", "compass.com", "opendoor.com", "offerpad.com",
        "costar.com", "loopnet.com", "crexi.com", "buildout.com",
    ],
    "manufacturing": [
        "ptc.com", "rockwellautomation.com", "honeywell.com", "ge.com",
        "siemens.com", "abb.com", "schneider-electric.com", "emerson.com",
        "netsol.com", "plex.com", "epicor.com", "infor.com",
    ],
    "education": [
        "coursera.com", "udemy.com", "canvas.instructure.com", "edx.org",
        "duolingo.com", "chegg.com", "quizlet.com", "instructure.com",
        "blackboard.com", "d2l.com", "schoology.com", "powerschool.com",
    ],
}

# Default fallback: mix of general B2B tech companies
_DEFAULT_DOMAINS = (
    _INDUSTRY_DOMAINS["saas"][:15] +
    _INDUSTRY_DOMAINS["fintech"][:5] +
    _INDUSTRY_DOMAINS["devtools"][:5] +
    _INDUSTRY_DOMAINS["ai"][:5]
)

_TITLE_KEYWORDS = [
    "cto", "chief technology officer",
    "ceo", "chief executive officer",
    "coo", "chief operating officer",
    "cfo", "chief financial officer",
    "cmo", "chief marketing officer",
    "founder", "co-founder", "cofounder",
    "vp", "vice president",
    "director", "head of",
    "manager", "lead",
    "owner", "president",
]


def _title_matches(position: str | None, person_titles: list[str]) -> bool:
    if not position:
        return False
    pos_lower = position.lower()
    # If caller provided specific titles, match those; else fall back to generic exec keywords
    targets = [t.lower() for t in (person_titles or [])] + _TITLE_KEYWORDS
    return any(re.search(r'\b' + re.escape(t) + r'\b', pos_lower) for t in targets)


def _domains_for_industries(industries: list[str] | None, n: int) -> list[str]:
    """Pick up to n company domains relevant to the requested industries."""
    if not industries:
        return _DEFAULT_DOMAINS[:n]

    picked: list[str] = []
    seen: set[str] = set()
    for industry in industries:
        ind_lower = industry.lower()
        # Find matching key(s) in our database
        for key, domains in _INDUSTRY_DOMAINS.items():
            if key in ind_lower or ind_lower in key or any(
                syn in ind_lower for syn in [key.replace("_", " "), key.replace("_", "")]
            ):
                for d in domains:
                    if d not in seen:
                        seen.add(d)
                        picked.append(d)
    if not picked:
        picked = _DEFAULT_DOMAINS
    return picked[:n]


async def _domain_search(domain: str, api_key: str, limit: int = 10) -> list[dict]:
    """Run Hunter domain-search for one domain, return raw email dicts."""
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=certifi.where()) as client:
            resp = await client.get(
                f"{HUNTER_BASE}/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": limit},
            )
        if resp.status_code != 200:
            logger.warning("Hunter domain-search %s → HTTP %d", domain, resp.status_code)
            return []
        return resp.json().get("data", {}).get("emails", [])
    except Exception as exc:
        logger.warning("Hunter domain-search %s failed: %s", domain, exc)
        return []


async def search_prospects(
    person_titles: list[str] | None = None,
    industries: list[str] | None = None,
    geographies: list[str] | None = None,
    company_size_min: int | None = None,
    company_size_max: int | None = None,
    per_page: int = 10,
) -> list[dict]:
    """
    Search for real prospects using Hunter domain-search across industry-matched company domains.
    Filters by title, deduplicates, returns in Apollo-compatible format.
    Automatically selects relevant company domains based on the industries parameter.
    """
    api_key = get_key("HUNTER_API_KEY")
    if not api_key:
        logger.warning("HUNTER_API_KEY not set — returning empty results (no mock)")
        return []

    person_titles = list(person_titles or [])
    domains_to_search = _domains_for_industries(industries, n=max(20, per_page * 3))
    logger.info(
        "Hunter prospect search: titles=%s industries=%s domains=%d per_page=%d",
        person_titles, industries, len(domains_to_search), per_page,
    )

    strict_titles = list(person_titles or [])

    def _compile_from_results(
        titles_filter: list[str],
        cap: int,
    ) -> list[dict]:
        out: list[dict] = []
        seen: set[str] = set()
        for domain, emails in zip(domains_to_search, all_results):
            industry_label = (industries[0] if industries else "Technology")
            company_name = domain.split(".")[0].replace("-", " ").title()
            for e in emails:
                email_addr = e.get("value", "")
                position = e.get("position", "")
                if not email_addr or email_addr in seen:
                    continue
                if titles_filter and not _title_matches(position, titles_filter):
                    continue
                seen.add(email_addr)
                first = e.get("first_name", "")
                last = e.get("last_name", "")
                out.append({
                    "id": f"hunter_{re.sub(r'[^a-z0-9]', '_', email_addr)}",
                    "first_name": first,
                    "last_name": last,
                    "full_name": f"{first} {last}".strip(),
                    "title": position,
                    "company": company_name,
                    "company_domain": f"https://{domain}",
                    "company_size": None,
                    "industry": industry_label,
                    "location": "",
                    "email": email_addr,
                    "email_status": "verified" if e.get("confidence", 0) >= 70 else "guessed",
                    "linkedin_url": e.get("linkedin", ""),
                    "source": "hunter",
                })
                if len(out) >= cap:
                    return out
            if len(out) >= cap:
                break
        return out

    tasks = [_domain_search(domain, api_key) for domain in domains_to_search]
    all_results = await asyncio.gather(*tasks)

    prospects = _compile_from_results(strict_titles, per_page)
    if not prospects and strict_titles:
        logger.info(
            "Hunter: title filter excluded all emails — retrying without title filter"
        )
        prospects = _compile_from_results([], max(per_page, 15))

    logger.info("Hunter prospect search: found %d real prospects", len(prospects))
    return prospects
