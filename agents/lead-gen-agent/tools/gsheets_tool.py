"""
Google Sheets CRM tool — use a Google Sheet as a lightweight CRM.

Sheet structure (auto-created on first write):
  Row 1: headers
  Row 2+: one lead per row

Columns: ID | First Name | Last Name | Email | Title | Company | Website |
         Location | ICP Score | LinkedIn | Lead Status | Source | Created At
"""
import logging
from datetime import datetime, timezone

import certifi
import httpx

logger = logging.getLogger(__name__)

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
SHEET_NAME  = "Leads"

HEADERS = [
    "ID", "First Name", "Last Name", "Email", "Title", "Company",
    "Website", "Location", "ICP Score", "LinkedIn", "Lead Status",
    "Source", "Created At",
]


def _auth(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


# ── Sheet creation ────────────────────────────────────────────────────────────

async def create_spreadsheet(access_token: str, title: str = "Orcha Leads") -> str:
    """Create a new Google Sheet and return its spreadsheet_id."""
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            SHEETS_BASE,
            headers=_auth(access_token),
            json={"properties": {"title": title}},
        )
        resp.raise_for_status()
        sid = resp.json()["spreadsheetId"]
        logger.info("Created new Google Sheet '%s': %s", title, sid)
        return sid


# ── Sheet initialisation ──────────────────────────────────────────────────────

async def ensure_headers(access_token: str, spreadsheet_id: str) -> bool:
    """Write the header row if the sheet is empty. Returns True if headers were written."""
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.get(
            f"{SHEETS_BASE}/{spreadsheet_id}/values/{SHEET_NAME}!A1:M1",
            headers=_auth(access_token),
        )
        if resp.is_success and resp.json().get("values"):
            return False
        await client.put(
            f"{SHEETS_BASE}/{spreadsheet_id}/values/{SHEET_NAME}!A1:M1",
            headers=_auth(access_token),
            params={"valueInputOption": "RAW"},
            json={"values": [HEADERS]},
        )
        logger.info("Wrote header row to sheet %s", spreadsheet_id)
        return True


# ── Read ──────────────────────────────────────────────────────────────────────

async def read_all_leads(access_token: str, spreadsheet_id: str) -> list[dict]:
    """Read all rows from the sheet. Returns list of lead dicts."""
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.get(
            f"{SHEETS_BASE}/{spreadsheet_id}/values/{SHEET_NAME}",
            headers=_auth(access_token),
        )
        if not resp.is_success:
            logger.warning("Sheets read failed: %d %s", resp.status_code, resp.text[:200])
            return []
        rows = resp.json().get("values", [])
        if len(rows) < 2:
            return []
        header = rows[0]
        return [_row_to_dict(header, row, idx + 2) for idx, row in enumerate(rows[1:])]


async def search_leads_in_sheet(
    access_token: str,
    spreadsheet_id: str,
    query: str = "",
    status: str | None = None,
) -> list[dict]:
    """Search leads by keyword (name/email/company) or status filter."""
    leads = await read_all_leads(access_token, spreadsheet_id)
    q = query.lower()

    results = []
    for lead in leads:
        if status and lead.get("lead_status", "").upper() != status.upper():
            continue
        if q:
            searchable = " ".join([
                lead.get("email", ""), lead.get("company", ""),
                lead.get("first_name", ""), lead.get("last_name", ""),
            ]).lower()
            if q not in searchable:
                continue
        results.append(lead)
    return results


# ── Write ─────────────────────────────────────────────────────────────────────

async def upsert_lead(access_token: str, spreadsheet_id: str, lead: dict) -> dict:
    """
    Add or update a lead. Deduplicates by email — updates the row if email exists.
    Returns {row_index, created: bool}.
    """
    await ensure_headers(access_token, spreadsheet_id)
    existing = await read_all_leads(access_token, spreadsheet_id)
    email = (lead.get("email") or "").lower()

    for row in existing:
        if row.get("email", "").lower() == email and email:
            return await update_lead_in_sheet(access_token, spreadsheet_id, row["_row_index"], lead)

    row_data = _lead_to_row(lead)
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{SHEETS_BASE}/{spreadsheet_id}/values/{SHEET_NAME}!A:M:append",
            headers=_auth(access_token),
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [row_data]},
        )
        if not resp.is_success:
            logger.warning("Sheets append failed: %d %s", resp.status_code, resp.text[:200])
            return {"error": f"HTTP {resp.status_code}"}
        updates = resp.json().get("updates", {})
        logger.info("Appended lead %s to sheet %s", email, spreadsheet_id)
        return {"created": True, "updated_range": updates.get("updatedRange")}


async def bulk_upsert_leads(access_token: str, spreadsheet_id: str, leads: list[dict]) -> list[dict]:
    """Write multiple leads, deduplicating by email."""
    results = []
    for lead in leads:
        result = await upsert_lead(access_token, spreadsheet_id, lead)
        results.append({**lead, "crm_result": result})
    return results


async def update_lead_in_sheet(
    access_token: str,
    spreadsheet_id: str,
    row_index: int,
    properties: dict,
) -> dict:
    """
    Update a specific row. properties can be a full lead dict or just changed fields.
    row_index is 1-based (2 = first data row after header).
    """
    existing = await read_all_leads(access_token, spreadsheet_id)
    current = next((r for r in existing if r["_row_index"] == row_index), {})
    merged = {**current, **properties}
    row_data = _lead_to_row(merged)

    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.put(
            f"{SHEETS_BASE}/{spreadsheet_id}/values/{SHEET_NAME}!A{row_index}:M{row_index}",
            headers=_auth(access_token),
            params={"valueInputOption": "RAW"},
            json={"values": [row_data]},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}"}
        return {"updated": True, "row_index": row_index}


async def delete_lead_from_sheet(access_token: str, spreadsheet_id: str, row_index: int) -> dict:
    """
    Delete a lead row by clearing it. Uses batchUpdate to physically delete the row.
    row_index is 1-based sheet row number.
    """
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{SHEETS_BASE}/{spreadsheet_id}:batchUpdate",
            headers=_auth(access_token),
            json={"requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId":    0,
                        "dimension":  "ROWS",
                        "startIndex": row_index - 1,
                        "endIndex":   row_index,
                    }
                }
            }]},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}"}
        return {"deleted": True, "row_index": row_index}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lead_to_row(lead: dict) -> list:
    return [
        lead.get("id") or lead.get("hubspot_id") or "",
        lead.get("first_name") or lead.get("firstname") or "",
        lead.get("last_name")  or lead.get("lastname")  or "",
        lead.get("email", ""),
        lead.get("title", ""),
        lead.get("company", ""),
        lead.get("company_domain") or lead.get("website", ""),
        lead.get("location", ""),
        str(lead.get("icp_score") or lead.get("ICP Score") or ""),
        lead.get("linkedin_url") or lead.get("LinkedIn", ""),
        lead.get("lead_status") or lead.get("Lead Status") or "NEW",
        lead.get("source", "Orcha Lead Gen"),
        lead.get("created_at") or datetime.now(timezone.utc).isoformat(),
    ]


def _row_to_dict(header: list, row: list, row_index: int) -> dict:
    padded = row + [""] * (len(header) - len(row))
    mapping = {
        "ID":           "id",
        "First Name":   "first_name",
        "Last Name":    "last_name",
        "Email":        "email",
        "Title":        "title",
        "Company":      "company",
        "Website":      "website",
        "Location":     "location",
        "ICP Score":    "icp_score",
        "LinkedIn":     "linkedin_url",
        "Lead Status":  "lead_status",
        "Source":       "source",
        "Created At":   "created_at",
    }
    result = {"_row_index": row_index}
    for col, val in zip(header, padded):
        key = mapping.get(col, col.lower().replace(" ", "_"))
        result[key] = val
    return result
