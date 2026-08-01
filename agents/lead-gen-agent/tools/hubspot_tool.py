"""
HubSpot CRM tool — full CRUD for contacts and deals.
Uses HubSpot Private App API key (no OAuth needed).
Docs: https://developers.hubspot.com/docs/api/crm/contacts
"""
import logging
import certifi
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.context import get_key

logger = logging.getLogger(__name__)
HUBSPOT_BASE = "https://api.hubapi.com"

CONTACT_PROPERTIES = "email,firstname,lastname,jobtitle,company,website,city,hs_lead_status,icp_score,linkedin_url,createdate"


def _headers() -> dict:
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _lead_to_properties(lead: dict) -> dict:
    props = {
        "email":          lead.get("email", ""),
        "firstname":      lead.get("first_name", ""),
        "lastname":       lead.get("last_name", ""),
        "jobtitle":       lead.get("title", ""),
        "company":        lead.get("company", ""),
        "website":        lead.get("company_domain", ""),
        "city":           lead.get("location", ""),
        "hs_lead_status": "NEW",
        "lead_source":    "Orcha Lead Gen Agent",
        "icp_score":      str(lead.get("icp_score", "")),
        "linkedin_url":   lead.get("linkedin_url", ""),
    }
    return {k: v for k, v in props.items() if v}


def _parse_contact(data: dict) -> dict:
    props = data.get("properties", {})
    return {
        "hubspot_id":  data.get("id"),
        "email":       props.get("email"),
        "first_name":  props.get("firstname"),
        "last_name":   props.get("lastname"),
        "title":       props.get("jobtitle"),
        "company":     props.get("company"),
        "website":     props.get("website"),
        "location":    props.get("city"),
        "lead_status": props.get("hs_lead_status"),
        "icp_score":   props.get("icp_score"),
        "linkedin_url": props.get("linkedin_url"),
        "created_at":  props.get("createdate"),
        "url":         f"https://app.hubspot.com/contacts/{data.get('id')}",
    }


# ── Contacts ──────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)))
async def upsert_contact(lead: dict) -> dict:
    """Create or update a HubSpot contact. Deduplicates by email."""
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        logger.warning("HUBSPOT_API_KEY not set — mock CRM write")
        return {"hubspot_id": f"mock_{lead.get('email','')}", "created": True, "url": "#"}

    email = lead.get("email")
    if not email:
        return {"hubspot_id": None, "created": False, "error": "no_email"}

    properties = _lead_to_properties(lead)

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        create_resp = await client.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            headers=_headers(), json={"properties": properties},
        )

        if create_resp.status_code == 409:
            existing = await _get_contact_by_email(client, email)
            if existing:
                cid = existing["id"]
                await client.patch(
                    f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{cid}",
                    headers=_headers(), json={"properties": properties},
                )
                return {"hubspot_id": cid, "created": False, "url": f"https://app.hubspot.com/contacts/{cid}"}

        if create_resp.status_code in (401, 403):
            return {"hubspot_id": None, "created": False, "error": f"HubSpot auth error {create_resp.status_code}"}

        create_resp.raise_for_status()
        cid = create_resp.json()["id"]
        logger.info("Created HubSpot contact %s → id=%s", email, cid)
        return {"hubspot_id": cid, "created": True, "url": f"https://app.hubspot.com/contacts/{cid}"}


async def bulk_upsert_contacts(leads: list[dict]) -> list[dict]:
    results = []
    for lead in leads:
        result = await upsert_contact(lead)
        results.append({**lead, "crm_result": result})
    return results


async def get_contact(email_or_id: str) -> dict | None:
    """Get a single contact by email or HubSpot ID."""
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return None
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        for id_prop in [None, "email"]:
            params = {"properties": CONTACT_PROPERTIES}
            if id_prop:
                params["idProperty"] = id_prop
            resp = await client.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{email_or_id}",
                headers=_headers(), params=params,
            )
            if resp.status_code == 200:
                return _parse_contact(resp.json())
    return None


async def search_contacts(query: str = "", filters: list[dict] | None = None, limit: int = 20) -> list[dict]:
    """
    Search contacts by keyword or property filters.
    filters example: [{"propertyName": "hs_lead_status", "operator": "EQ", "value": "NEW"}]
    """
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return []

    body: dict = {
        "properties": CONTACT_PROPERTIES.split(","),
        "limit": limit,
    }
    if filters:
        body["filterGroups"] = [{"filters": filters}]
    if query:
        body["query"] = query

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
            headers=_headers(), json=body,
        )
        if not resp.is_success:
            logger.warning("HubSpot search failed: %d %s", resp.status_code, resp.text[:200])
            return []
        return [_parse_contact(r) for r in resp.json().get("results", [])]


async def update_contact(contact_id: str, properties: dict) -> dict:
    """
    Update specific fields on a contact.
    Common properties: hs_lead_status, jobtitle, company, notes_last_updated
    Lead statuses: NEW, OPEN, IN_PROGRESS, OPEN_DEAL, UNQUALIFIED, ATTEMPTED_TO_CONTACT, CONNECTED, BAD_TIMING
    """
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return {"error": "no_hubspot_token"}

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.patch(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
            headers=_headers(), json={"properties": properties},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text[:200]}
        return {"updated": True, "hubspot_id": contact_id, "url": f"https://app.hubspot.com/contacts/{contact_id}"}


async def delete_contact(contact_id: str) -> dict:
    """Archive (soft-delete) a contact. Can be restored from HubSpot UI."""
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return {"error": "no_hubspot_token"}

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.delete(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
            headers=_headers(),
        )
        if resp.status_code == 204:
            return {"deleted": True, "hubspot_id": contact_id}
        return {"error": f"HTTP {resp.status_code}"}


# ── Deals ─────────────────────────────────────────────────────────────────────

async def list_pipeline_stages(pipeline_id: str = "default") -> list[dict]:
    """Get available deal stages for a pipeline."""
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return []
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.get(
            f"{HUBSPOT_BASE}/crm/v3/pipelines/deals/{pipeline_id}/stages",
            headers=_headers(),
        )
        if not resp.is_success:
            return []
        return [
            {
                "id": s["id"],
                "label": s["label"],
                "probability": s.get("metadata", {}).get("probability"),
            }
            for s in resp.json().get("results", [])
        ]


async def create_deal(
    deal_name: str,
    contact_id: str | None = None,
    pipeline: str = "default",
    stage: str = "appointmentscheduled",
    amount: float | None = None,
    close_date: str | None = None,
    extra_properties: dict | None = None,
) -> dict:
    """
    Create a deal and associate it with a contact.
    Common stages: appointmentscheduled, qualifiedtobuy, presentationscheduled,
                   decisionmakerboughtin, contractsent, closedwon, closedlost
    """
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return {"error": "no_hubspot_token"}

    properties: dict = {"dealname": deal_name, "pipeline": pipeline, "dealstage": stage}
    if amount is not None:
        properties["amount"] = str(amount)
    if close_date:
        properties["closedate"] = close_date
    if extra_properties:
        properties.update(extra_properties)

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/deals",
            headers=_headers(), json={"properties": properties},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text[:200]}
        deal_id = resp.json()["id"]
        logger.info("Created deal %s id=%s", deal_name, deal_id)

        if contact_id:
            assoc = await client.put(
                f"{HUBSPOT_BASE}/crm/v4/objects/deals/{deal_id}/associations/contacts/{contact_id}",
                headers=_headers(),
                json=[{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
            )
            if not assoc.is_success:
                logger.warning("Deal-contact association failed: %s", assoc.text[:200])

        return {"deal_id": deal_id, "created": True, "url": f"https://app.hubspot.com/deals/{deal_id}"}


async def update_deal(deal_id: str, properties: dict) -> dict:
    """
    Update deal stage, amount, or any property.
    Common: {"dealstage": "closedwon"} or {"amount": "5000"}
    """
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return {"error": "no_hubspot_token"}
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.patch(
            f"{HUBSPOT_BASE}/crm/v3/objects/deals/{deal_id}",
            headers=_headers(), json={"properties": properties},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text[:200]}
        return {"updated": True, "deal_id": deal_id, "url": f"https://app.hubspot.com/deals/{deal_id}"}


async def get_deals_for_contact(contact_id: str) -> list[dict]:
    """Get all deals associated with a contact."""
    token = get_key("HUBSPOT_API_KEY")
    if not token:
        return []
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        assoc = await client.get(
            f"{HUBSPOT_BASE}/crm/v4/objects/contacts/{contact_id}/associations/deals",
            headers=_headers(),
        )
        if not assoc.is_success:
            return []
        deal_ids = [r["toObjectId"] for r in assoc.json().get("results", [])]

        deals = []
        for did in deal_ids[:10]:
            resp = await client.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/deals/{did}",
                headers=_headers(),
                params={"properties": "dealname,dealstage,amount,closedate,pipeline,createdate"},
            )
            if resp.is_success:
                d = resp.json()
                p = d.get("properties", {})
                deals.append({
                    "deal_id":    d["id"],
                    "name":       p.get("dealname"),
                    "stage":      p.get("dealstage"),
                    "amount":     p.get("amount"),
                    "close_date": p.get("closedate"),
                    "url":        f"https://app.hubspot.com/deals/{d['id']}",
                })
        return deals


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_contact_by_email(client: httpx.AsyncClient, email: str) -> dict | None:
    resp = await client.get(
        f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{email}",
        headers=_headers(), params={"idProperty": "email"},
    )
    return resp.json() if resp.status_code == 200 else None
