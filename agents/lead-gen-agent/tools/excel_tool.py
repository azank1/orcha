"""
Microsoft Excel CRM tool — uses an Excel workbook in OneDrive as a CRM.

Uses Microsoft Graph API.
Workbook structure (auto-initialised):
  Sheet: "Leads"
  Table: "LeadsTable"
  Columns: ID | First Name | Last Name | Email | Title | Company | Website |
           Location | ICP Score | LinkedIn | Lead Status | Source | Created At

Setup:
  1. Client connects via /oauth/excel/connect
  2. The workbook is created in their OneDrive root if it doesn't exist,
     or the agent uses an existing workbook named "Leads.xlsx" (configurable).
"""
import logging
from datetime import datetime, timezone

import certifi
import httpx

logger = logging.getLogger(__name__)

GRAPH_BASE   = "https://graph.microsoft.com/v1.0"
WORKBOOK_DEFAULT = "Leads"
SHEET_NAME   = "Leads"
TABLE_NAME   = "LeadsTable"

COLUMNS = [
    "ID", "First Name", "Last Name", "Email", "Title", "Company",
    "Website", "Location", "ICP Score", "LinkedIn", "Lead Status",
    "Source", "Created At",
]


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


def _workbook_path(workbook_name: str) -> str:
    name = workbook_name if workbook_name.endswith(".xlsx") else f"{workbook_name}.xlsx"
    return f"{GRAPH_BASE}/me/drive/root:/{name}:"


# ── Workbook initialisation ───────────────────────────────────────────────────

async def ensure_workbook(access_token: str, workbook_name: str = WORKBOOK_DEFAULT) -> str | None:
    """
    Get or create the Excel workbook in OneDrive root.
    Returns the workbook item ID, or None on failure.
    """
    path = _workbook_path(workbook_name)
    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        resp = await client.get(path, headers=_headers(access_token))
        if resp.is_success:
            return resp.json()["id"]

        # Create an empty workbook by uploading a minimal xlsx
        upload_url = f"{GRAPH_BASE}/me/drive/root:/{workbook_name}.xlsx:/content"
        from io import BytesIO
        xlsx_bytes = _empty_xlsx_bytes()
        put_resp = await client.put(
            upload_url,
            headers={**_headers(access_token), "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            content=xlsx_bytes,
        )
        if not put_resp.is_success:
            logger.warning("Could not create Excel workbook: %d %s", put_resp.status_code, put_resp.text[:200])
            return None
        logger.info("Created Excel workbook %s.xlsx", workbook_name)
        return put_resp.json()["id"]


async def ensure_table(access_token: str, item_id: str) -> bool:
    """
    Ensure the Leads sheet and table exist with the correct headers.
    Returns True if the table already existed or was created successfully.
    """
    wb_base = f"{GRAPH_BASE}/me/drive/items/{item_id}/workbook"
    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        tables_resp = await client.get(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables",
            headers=_headers(access_token),
        )
        if tables_resp.is_success:
            tables = tables_resp.json().get("value", [])
            if any(t["name"] == TABLE_NAME for t in tables):
                return True

        header_range = f"A1:{chr(ord('A') + len(COLUMNS) - 1)}1"
        await client.patch(
            f"{wb_base}/worksheets/{SHEET_NAME}/range(address='{header_range}')",
            headers=_headers(access_token),
            json={"values": [COLUMNS]},
        )
        create_resp = await client.post(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables/add",
            headers=_headers(access_token),
            json={"address": f"{SHEET_NAME}!{header_range}", "hasHeaders": True},
        )
        if create_resp.is_success:
            await client.patch(
                f"{wb_base}/worksheets/{SHEET_NAME}/tables/0",
                headers=_headers(access_token),
                json={"name": TABLE_NAME},
            )
        return create_resp.is_success


# ── Read ──────────────────────────────────────────────────────────────────────

async def read_all_leads(access_token: str, item_id: str) -> list[dict]:
    """Read all rows from the Leads table."""
    wb_base = f"{GRAPH_BASE}/me/drive/items/{item_id}/workbook"
    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        resp = await client.get(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables/{TABLE_NAME}/rows",
            headers=_headers(access_token),
        )
        if not resp.is_success:
            logger.warning("Excel read failed: %d", resp.status_code)
            return []
        rows = resp.json().get("value", [])
        return [_row_to_dict(r["values"][0], idx) for idx, r in enumerate(rows)]


async def search_leads(
    access_token: str,
    item_id: str,
    query: str = "",
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search leads by keyword or status."""
    leads = await read_all_leads(access_token, item_id)
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
        if len(results) >= limit:
            break
    return results


# ── Write ─────────────────────────────────────────────────────────────────────

async def upsert_lead(access_token: str, item_id: str, lead: dict) -> dict:
    """Add or update a lead. Deduplicates by email."""
    await ensure_table(access_token, item_id)
    email = (lead.get("email") or "").lower()

    if email:
        existing = await read_all_leads(access_token, item_id)
        for row in existing:
            if row.get("email", "").lower() == email:
                return await update_lead(access_token, item_id, row["_row_index"], lead)

    row_data = _lead_to_row(lead)
    wb_base  = f"{GRAPH_BASE}/me/drive/items/{item_id}/workbook"
    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        resp = await client.post(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables/{TABLE_NAME}/rows/add",
            headers=_headers(access_token),
            json={"values": [row_data]},
        )
        if not resp.is_success:
            logger.warning("Excel row add failed: %d %s", resp.status_code, resp.text[:200])
            return {"error": f"HTTP {resp.status_code}"}
        logger.info("Added Excel lead %s", email)
        return {"created": True, "excel_item_id": item_id}


async def bulk_upsert_leads(access_token: str, item_id: str, leads: list[dict]) -> list[dict]:
    results = []
    for lead in leads:
        result = await upsert_lead(access_token, item_id, lead)
        results.append({**lead, "crm_result": result})
    return results


async def update_lead(access_token: str, item_id: str, row_index: int, properties: dict) -> dict:
    """Update a specific row (0-based row_index within table data rows)."""
    existing = await read_all_leads(access_token, item_id)
    current  = next((r for r in existing if r["_row_index"] == row_index), {})
    merged   = {**current, **properties}
    row_data = _lead_to_row(merged)
    wb_base  = f"{GRAPH_BASE}/me/drive/items/{item_id}/workbook"

    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        resp = await client.patch(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables/{TABLE_NAME}/rows/itemAt(index={row_index})",
            headers=_headers(access_token),
            json={"values": [row_data]},
        )
        if not resp.is_success:
            return {"error": f"HTTP {resp.status_code}"}
        return {"updated": True, "row_index": row_index}


async def delete_lead(access_token: str, item_id: str, row_index: int) -> dict:
    """Delete a row from the table by 0-based index."""
    wb_base = f"{GRAPH_BASE}/me/drive/items/{item_id}/workbook"
    async with httpx.AsyncClient(timeout=20.0, verify=certifi.where()) as client:
        resp = await client.delete(
            f"{wb_base}/worksheets/{SHEET_NAME}/tables/{TABLE_NAME}/rows/itemAt(index={row_index})",
            headers=_headers(access_token),
        )
        if resp.status_code not in (200, 204):
            return {"error": f"HTTP {resp.status_code}"}
        return {"deleted": True, "row_index": row_index}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lead_to_row(lead: dict) -> list:
    return [
        lead.get("id") or "",
        lead.get("first_name") or lead.get("firstname") or "",
        lead.get("last_name")  or lead.get("lastname")  or "",
        lead.get("email", ""),
        lead.get("title", ""),
        lead.get("company", ""),
        lead.get("company_domain") or lead.get("website", ""),
        lead.get("location", ""),
        str(lead.get("icp_score") or ""),
        lead.get("linkedin_url", ""),
        lead.get("lead_status", "NEW"),
        lead.get("source", "MetaOrcha Lead Gen"),
        lead.get("created_at") or datetime.now(timezone.utc).isoformat(),
    ]


def _row_to_dict(row: list, row_index: int) -> dict:
    padded = row + [""] * max(0, len(COLUMNS) - len(row))
    keys   = [
        "id", "first_name", "last_name", "email", "title", "company",
        "website", "location", "icp_score", "linkedin_url", "lead_status",
        "source", "created_at",
    ]
    result = {"_row_index": row_index}
    for key, val in zip(keys, padded):
        result[key] = val
    return result


def _empty_xlsx_bytes() -> bytes:
    """Return minimal valid xlsx bytes for workbook creation."""
    import zipfile, io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>')
        zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
        zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>')
        zf.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Leads" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>')
        zf.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData/></worksheet>')
    return buf.getvalue()
