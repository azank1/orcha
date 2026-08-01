"""
ICP scoring tool — scores each prospect against the Ideal Customer Profile.
Pure Python, no external calls. Fast and deterministic.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ICPConfig:
    target_roles: list[str] = field(default_factory=lambda: [
        "CTO", "VP Engineering", "Head of Engineering", "Engineering Manager",
        "CEO", "COO", "Operations Manager", "Director of Operations",
        "IT Manager", "IT Director", "VP Technology", "Digital Transformation",
        "Owner", "Founder", "President", "Managing Director",
    ])
    industries: list[str] = field(default_factory=lambda: [
        "SaaS", "Software", "Technology", "FinTech",
        "Manufacturing", "Retail", "Healthcare", "Logistics",
        "Professional Services", "Consulting", "Legal", "Accounting",
        "Real Estate", "Construction", "Distribution", "Wholesale",
        # SMB / traditional
        "Agriculture", "Farming", "Food & Beverage", "Hospitality",
        "Beauty & Wellness", "Education", "Religious", "Trades",
        "Auto Repair", "Cleaning Services", "Pet Services",
    ])
    # 1 = sole traders qualify; previously 10 which excluded SMBs
    company_size_min: int = 1
    company_size_max: int = 5000
    # Open to worldwide — agent restricts geography via query/geographies arg
    geographies: list[str] = field(default_factory=list)
    # False: local businesses (Maps) almost never have a crawlable email
    required_email: bool = False
    min_score: int = 50
    # 15 = phone-only rural business qualifies (phone=15 pts)
    local_min_score: int = 15

    @classmethod
    def from_dict(cls, d: dict) -> "ICPConfig":
        return cls(
            target_roles=d.get("target_roles", cls.__dataclass_fields__["target_roles"].default_factory()),
            industries=d.get("industries", cls.__dataclass_fields__["industries"].default_factory()),
            company_size_min=d.get("company_size_min", 1),
            company_size_max=d.get("company_size_max", 5000),
            geographies=d.get("geographies", []),
            required_email=d.get("required_email", False),
            min_score=d.get("min_score", 50),
            local_min_score=d.get("local_min_score", 15),
        )


def _local_breakdown(business: dict) -> dict:
    """
    Shared scoring breakdown for local/Maps businesses.
    Rural or newly-opened businesses often have few reviews — give 5 pts for
    any reviews at all so a phone-only store with 3 reviews still qualifies.

    Max = 100:  rating 40 + reviews 25 + website 20 + phone 15
    """
    rating = business.get("rating")
    reviews = int(business.get("review_count") or 0)

    return {
        "rating":  round((float(rating) / 5.0) * 40) if rating is not None else 0,
        "reviews": (
            25 if reviews >= 100
            else 18 if reviews >= 50
            else 10 if reviews >= 10
            else 5  if reviews >= 1   # any reviews = contactable, active business
            else 0
        ),
        "website": 20 if business.get("website") else 0,
        "phone":   15 if business.get("phone") else 0,
    }


def score_lead(lead: dict, icp: ICPConfig) -> dict:
    """
    Score a lead against the ICP. Returns lead dict with icp_score and score_breakdown.

    Google Maps (local) results are scored on local_score (rating, reviews, website, phone).
    B2B (Apollo/Hunter) results are scored on role, industry, company size, email.
    Max score = 100 for both paths.

    Scoring breakdown (B2B):
      - Role match:         40 pts (exact) / 20 pts (partial)
      - Industry match:     25 pts
      - Company size:       20 pts
      - Email verified:     15 pts
    """
    # ── Local business path (Google Maps results) ────────────────────────────
    if lead.get("source") in ("google_maps",):
        breakdown = _local_breakdown(lead)
        local_score = sum(breakdown.values())
        # Unreachable businesses (no phone AND no website) can't be contacted
        if not lead.get("website") and not lead.get("phone"):
            local_score = min(local_score, icp.local_min_score - 1)
        result = {
            **lead,
            "icp_score": local_score,
            "score_breakdown": breakdown,
            "qualified": local_score >= icp.local_min_score,
        }
        logger.debug(
            "Local score %s: %d/100 (rating=%s reviews=%s)",
            lead.get("name"), local_score, lead.get("rating"), lead.get("review_count"),
        )
        return result

    # ── B2B path (Apollo / Hunter results) ───────────────────────────────────
    score = 0
    breakdown = {}

    # --- Role match (40 pts) ---
    title = (lead.get("title") or "").lower()
    role_score = 0
    for role in icp.target_roles:
        if role.lower() == title:
            role_score = 40
            break
        elif role.lower() in title or title in role.lower():
            role_score = max(role_score, 20)
    score += role_score
    breakdown["role"] = role_score

    # --- Industry match (25 pts) ---
    industry = (lead.get("industry") or "").lower()
    ind_score = 0
    for ind in icp.industries:
        if ind.lower() in industry or industry in ind.lower():
            ind_score = 25
            break
    score += ind_score
    breakdown["industry"] = ind_score

    # --- Company size (20 pts) ---
    headcount = lead.get("company_size")
    size_score = 0
    if headcount is not None:
        if icp.company_size_min <= int(headcount) <= icp.company_size_max:
            size_score = 20
        elif int(headcount) < icp.company_size_min * 0.5 or int(headcount) > icp.company_size_max * 2:
            size_score = 0
        else:
            size_score = 10  # partial credit for near-miss
    score += size_score
    breakdown["company_size"] = size_score

    # --- Email (15 pts) ---
    email = lead.get("email")
    email_status = lead.get("email_status", "unknown")
    email_score = 0
    if email and email_status in ("verified", "valid"):
        email_score = 15
    elif email:
        email_score = 8
    score += email_score
    breakdown["email"] = email_score

    qualified = score >= icp.min_score and (not icp.required_email or bool(email))
    result = {
        **lead,
        "icp_score": score,
        "score_breakdown": breakdown,
        "qualified": qualified,
    }

    logger.debug(f"Scored {lead.get('full_name')} @ {lead.get('company')}: {score}/100 {breakdown}")
    return result


def score_and_filter(leads: list[dict], icp: ICPConfig) -> tuple[list[dict], list[dict]]:
    """
    Score all leads, return (qualified, disqualified) sorted by score descending.
    """
    scored = [score_lead(lead, icp) for lead in leads]
    qualified = sorted([l for l in scored if l["qualified"]], key=lambda x: x["icp_score"], reverse=True)
    disqualified = sorted([l for l in scored if not l["qualified"]], key=lambda x: x["icp_score"], reverse=True)
    logger.info(f"Scoring: {len(leads)} leads → {len(qualified)} qualified, {len(disqualified)} disqualified")
    return qualified, disqualified


def deduplicate(leads: list[dict], existing_emails: set[str] | None = None) -> list[dict]:
    """Remove duplicates within the list and optionally against known CRM emails."""
    seen_emails: set[str] = set(existing_emails or [])
    unique = []
    for lead in leads:
        email = (lead.get("email") or "").lower()
        if email and email in seen_emails:
            logger.debug(f"Dedup: skipping {email} (already seen)")
            continue
        if email:
            seen_emails.add(email)
        unique.append(lead)
    return unique
