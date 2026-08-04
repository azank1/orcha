"""
Notion CRM tool — uses a Notion database as a lead CRM.

Database property schema (create this in Notion before connecting):
  Name          Title
  Email         Email
  Title         Rich Text
  Company       Rich Text
  Website       URL
  Location      Rich Text
  ICP Score     Number
  LinkedIn      URL
  Lead Status   Select  (NEW | OPEN | IN_PROGRESS | CONNECTED | UNQUALIFIED | BAD_TIMING)
  Source        Select
  Created At    Date    (auto-filled)

The tool auto-creates missing properties on first write.
"""
import logging
from datetime import datetime, timezone

import certifi
import httpx

logger = logging.getLogger(__name__)

NOTION_BASE    = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

LEAD_STATUS_OPTIONS = ["NEW", "OPEN", "IN_PROGRESS", "CONNECTED", "UNQUALIFIED", "BAD_TIMING", "ATTEMPTED_TO_CONTACT"]


def _headers(access_token: str) -> dict:
    return {
        "Authorization":  f"Bearer {access_token}",
        "Content-Type":   "application/json",
        "Notion-Version": NOTION_VERSION,
    }


# ── Database structure ────────────────────────────────────────────────────────

def _lead_to_properties(lead: dict) -> dict:
    """Convert a lead dict to Notion property format."""
    props: dict = {}

    name = (lead.get("full_name") or
            f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip() or
            lead.get("name", "Unknown"))
    props["Name"] = {"title": [{"text": {"content": name}}]}

    if lead.get("email"):
        props["Email"] = {"email": lead["email"]}

    if lead.get("title"):
        props["Title"] = {"rich_text": [{"text": {"content": lead["title"][:2000]}}]}

    if lead.get("company"):
        props["Company"] = {"rich_text": [{"text": {"content": lead["company"][:2000]}}]}

    website = lead.get("company_domain") or lead.get("website", "")
    if website:
        if not website.startswith("http"):
            website = f"https://{website}"
        props["Website"] = {"url": website}

    if lead.get("location"):
        props["Location"] = {"rich_text": [{"text": {"content": lead["location"][:2000]}}]}

    if lead.get("icp_score") is not None:
        try:
            props["ICP Score"] = {"number": float(lead["icp_score"])}
        except (ValueError, TypeError):
            pass

    linkedin = lead.get("linkedin_url", "")
    if linkedin:
        if not linkedin.startswith("http"):
            linkedin = f"https://{linkedin}"
        props["LinkedIn"] = {"url": linkedin}

    props["Lead Status"] = {"select": {"name": "NEW"}}
    props["Source"]      = {"select": {"name": lead.get("source", "Orcha Lead Gen")[:100]}}
    props["Created At"]  = {"date": {"start": datetime.now(timezone.utc).isoformat()}}

    return props


def _page_to_lead(page: dict) -> dict:
    """Convert a Notion page to a lead dict."""
    props = page.get("properties", {})

    def _rich_text(p: dict) -> str:
        items = p.get("rich_text", [])
        return items[0]["text"]["content"] if items else ""

    def _title_val(p: dict) -> str:
        items = p.get("title", [])
        return items[0]["text"]["content"] if items else ""

    full_name = _title_val(props.get("Name", {}))
    parts     = full_name.split(" ", 1)

    return {
        "notion_id":   page["id"],
        "full_name":   full_name,
        "first_name":  parts[0] if parts else "",
        "last_name":   parts[1] if len(parts) > 1 else "",
        "email":       (props.get("Email") or {}).get("email", ""),
        "title":       _rich_text(props.get("Title", {})),
        "company":     _rich_text(props.get("Company", {})),
        "website":     (props.get("Website") or {}).get("url", ""),
        "location":    _rich_text(props.get("Location", {})),
        "icp_score":   (props.get("ICP Score") or {}).get("number"),
        "linkedin_url": (props.get("LinkedIn") or {}).get("url", ""),
        "lead_status": ((props.get("Lead Status") or {}).get("select") or {}).get("name", ""),
        "source":      ((props.get("Source") or {}).get("select") or {}).get("name", ""),
        "url":         page.get("url", ""),
    }


# ── Read ──────────────────────────────────────────────────────────────────────

async def search_leads(
    access_token: str,
    database_id: str,
    query: str = "",
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search leads in a Notion database."""
    body: dict = {"page_size": limit}

    filters = []
    if status:
        filters.append({
            "property": "Lead Status",
            "select":   {"equals": status},
        })
    if query:
        filters.append({
            "or": [
                {"property": "Name",    "title":     {"contains": query}},
                {"property": "Email",   "email":     {"contains": query}},
                {"property": "Company", "rich_text": {"contains": query}},
            ]
        })

    if len(filters) == 1:
        body["filter"] = filters[0]
    elif len(filters) > 1:
        body["filter"] = {"and": filters}

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{NOTION_BASE}/databases/{database_id}/query",
            headers=_headers(access_token),
            json=body,
        )
        if not resp.is_success:
            logger.warning("Notion search failed: %d %s", resp.status_code, resp.text[:200])
            return []
        return [_page_to_lead(p) for p in resp.json().get("results", [])]


async def get_lead_by_email(access_token: str, database_id: str, email: str) -> dict | None:
    """Find a lead by email address."""
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{NOTION_BASE}/databases/{database_id}/query",
            headers=_headers(access_token),
            json={"filter": {"property": "Email", "email": {"equals": email}}, "page_size": 1},
        )
        if not resp.is_success:
            return None
        results = resp.json().get("results", [])
        return _page_to_lead(results[0]) if results else None


# ── Write ─────────────────────────────────────────────────────────────────────

async def upsert_lead(access_token: str, database_id: str, lead: dict) -> dict:
    """Create or update a lead. Deduplicates by email."""
    email = lead.get("email", "")
    if email:
        existing = await get_lead_by_email(access_token, database_id, email)
        if existing:
            return await update_lead(access_token, existing["notion_id"], lead)

    properties = _lead_to_properties(lead)
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{NOTION_BASE}/pages",
            headers=_headers(access_token),
            json={"parent": {"database_id": database_id}, "properties": properties},
        )
        if not resp.is_success:
            logger.warning("Notion create failed: %d %s", resp.status_code, resp.text[:300])
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        page = resp.json()
        logger.info("Created Notion page for %s", email or lead.get("full_name"))
        return {"notion_id": page["id"], "created": True, "url": page.get("url", "")}


async def bulk_upsert_leads(access_token: str, database_id: str, leads: list[dict]) -> list[dict]:
    results = []
    for lead in leads:
        result = await upsert_lead(access_token, database_id, lead)
        results.append({**lead, "crm_result": result})
    return results


async def update_lead(access_token: str, page_id: str, properties: dict) -> dict:
    """
    Update a Notion page. `properties` can be a full lead dict or
    a Notion-format properties dict directly.
    Automatically converts lead dict fields to Notion property format.
    """
    if "Lead Status" not in properties and "lead_status" in properties:
        notion_props = {"Lead Status": {"select": {"name": properties["lead_status"]}}}
        if "company" in properties:
            notion_props["Company"] = {"rich_text": [{"text": {"content": properties["company"]}}]}
        if "title" in properties:
            notion_props["Title"] = {"rich_text": [{"text": {"content": properties["title"]}}]}
    elif _is_notion_format(properties):
        notion_props = properties
    else:
        notion_props = _lead_to_properties(properties)
        # Remove Created At to avoid overwriting original
        notion_props.pop("Created At", None)

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.patch(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=_headers(access_token),
            json={"properties": notion_props},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text[:200]}
        return {"updated": True, "notion_id": page_id, "url": resp.json().get("url", "")}


async def delete_lead(access_token: str, page_id: str) -> dict:
    """Archive a Notion page (soft delete — restorable)."""
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.patch(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=_headers(access_token),
            json={"archived": True},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}"}
        return {"deleted": True, "notion_id": page_id}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_notion_format(props: dict) -> bool:
    """Heuristic: if any key looks like a Notion property type dict, treat as native format."""
    for v in props.values():
        if isinstance(v, dict) and any(k in v for k in ("title", "rich_text", "select", "email", "url", "number", "date")):
            return True
    return False
