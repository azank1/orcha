"""
Lead Gen Agent — core LLM agentic loop.
Provider-agnostic: works with Anthropic, OpenAI, Grok, or OpenRouter.
Set LLM_PROVIDER=anthropic|openai|grok|openrouter in your .env.
"""
import json
import logging
import os
import time
from typing import Any, Awaitable, Callable

from tools import (
    search_prospects,
    find_email,
    bulk_upsert_contacts,
    get_contact,
    search_contacts,
    update_contact,
    delete_contact,
    create_deal,
    update_deal,
    get_deals_for_contact,
    bulk_upsert_sheet_leads,
    search_leads_in_sheet,
    update_lead_in_sheet,
    delete_lead_from_sheet,
    bulk_upsert_notion_leads,
    search_notion_leads,
    update_notion_lead,
    delete_notion_lead,
    bulk_upsert_excel_leads,
    search_excel_leads,
    update_excel_lead,
    delete_excel_lead,
    ensure_excel_workbook,
    smart_search,
    detect_mode,
    send_outreach_emails,
    send_from_drafts,
    build_email_previews,
)
from integrations.gmail_oauth import send_drafts_via_gmail
from core.tool_schemas import TOOL_SCHEMAS
from core.context import get_key, set_credentials
from core.llm_provider import get_provider, get_api_key_name, AnthropicProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a production lead generation agent that works for ANY business type — tech B2B, local SMBs, rural trades, agriculture, hospitality, retail, and more. Use tools for every step — do NOT output conversational text between tool calls.

## Workflow — execute ALL steps using tools, one after another:
1. search_leads        — find prospects for the query
   • After search_leads, read `sources`, `count`, and `search_notes` from the tool result.
     Apollo may be empty while Hunter (`hunter`) and/or Google Maps (`google_maps`) still provide rows —
     mention those providers in the summary when non-empty; never tell the user the pipeline failed solely
     because of Apollo when `count` > 0.
2. score_and_filter_leads — mark all discovered leads as qualified (pass results from step 1)
3. find_email          — enrich qualified leads missing emails (skip for local/Maps leads — they rarely have professional emails)
4. write_leads_to_crm  — save ALL leads returned in the "qualified" array from step 2
5. send_outreach_emails — if send_outreach_email={send_outreach_email} AND there are qualified leads with email

## CRM management (when asked):
- search_crm_leads, update_crm_lead, delete_crm_lead, create_deal, update_deal, get_deals

## Query construction rules:
- ALWAYS include a specific location in the search_leads query when the business type is local
  (restaurants, shops, clinics, gyms, farms, plumbers, mechanics, salons, etc.).
  e.g. "restaurants in Lahore" not just "restaurants".
- If the user gives only a country for a local search, pick the 3 most populated cities and
  run one search per city.
- For SMB / rural / traditional searches (farms, co-ops, rural tradespeople, brick-and-mortar
  shops), prefer Google Maps queries — Apollo has no coverage for these.
  e.g. "grain farms in rural Iowa", "furniture workshops in Lahore", "dairy farms in Punjab".
- For tech B2B / executive searches, use Apollo-style kwargs (person_titles, industries,
  geographies, company_size_min/max) alongside the query.
- If a first search returns 0 results, try a broader version:
  "plumbers in Springfield, IL" → "plumbers in Illinois" → "plumbers".

## Scoring rules:
- Local business results (Google Maps) qualify on phone or website alone — do NOT require email or title.
- A rural business with 3 reviews and a phone number is a valid lead.
- B2B results qualify on role + industry + size match — email adds score but is not mandatory.
- Pass the entire "qualified" array from score_and_filter_leads to write_leads_to_crm — do NOT re-filter.
- Always call write_leads_to_crm even if leads have no email.

## Other rules:
- If write_leads_to_crm returns an error or skipped=true, set leads_written_to_crm=0 in your final JSON and include the reason in the summary. Do NOT ask the user for CRM configuration — that is handled externally.
- Max leads per run: {max_leads}
- Never guess email addresses — only use verified emails from find_email.
- For CRM-only queries, skip search_leads and go directly to the CRM tool.
- If an email message template is provided in the query, use it verbatim in send_outreach_emails.

## Final response (after all tools complete) — output only this JSON, nothing else:
{{
  "leads_found": <int>,
  "leads_qualified": <int>,
  "leads_written_to_crm": <int>,
  "emails_sent": <int>,
  "search_mode": "<local|global|crm>",
  "qualified_leads": [<list of qualified lead objects>],
  "summary": "<1-2 sentence plain English summary>"
}}
"""

ReviewCallback    = Callable[[list[dict]], Awaitable[list[dict]]]
HubspotAuthCallback = Callable[[], Awaitable[str]]
GmailOAuthCallback  = Callable[[], Awaitable[tuple[str, str]]]
CrmSetupCallback  = Callable[[], Awaitable[str]]  # returns crm_type string


class LeadGenAgent:
    def __init__(self):
        self._last_search_results: list[dict] = []
        self._last_qualified_leads: list[dict] = []
        self._leads_found = 0
        self._leads_qualified = 0
        self._leads_written_to_crm = 0
        self._emails_sent = 0
        self._crm_type: str | None = None
        self._tools_used_this_run: set[str] = set()

    def _pipeline_recovery_nudge(
        self,
        *,
        write_to_crm: bool,
        send_outreach_email: bool,
    ) -> str | None:
        """
        GLM/OpenRouter sometimes returns finish_reason=stop with prose or empty content right after
        search_leads instead of chaining score/find_email/write. Return a corrective user message, or None.
        """
        t = self._tools_used_this_run
        n_results = len(self._last_search_results)

        if "search_leads" in t and "score_and_filter_leads" not in t and n_results > 0:
            return (
                "You must continue with tool calls only (no plain-text reply yet).\n"
                "Next: call score_and_filter_leads — pass the `results` array from the last search_leads "
                "response as `leads`, or omit `leads` to use the cached search results.\n"
                "Then: find_email for qualified B2B rows missing `email` (skip bulk find_email for pure "
                "Google-Maps-only local rows if there are no domains).\n"
                f"Then: call write_leads_to_crm (write_to_crm is {write_to_crm}).\n"
                + (
                    "Then: call send_outreach_emails if enabled and at least one lead has an email.\n"
                    if send_outreach_email
                    else ""
                )
                + "Only after every required tool has run, output the single final JSON object from the system prompt."
            )

        if (
            write_to_crm
            and "score_and_filter_leads" in t
            and "write_leads_to_crm" not in t
            and self._leads_qualified > 0
        ):
            return (
                "Continue with tool calls: call write_leads_to_crm with the full `qualified` array from "
                "score_and_filter_leads (or omit `leads` to use the cached qualified list).\n"
                + (
                    "Then call send_outreach_emails if appropriate.\n"
                    if send_outreach_email
                    else ""
                )
                + "After tools finish, output only the final JSON."
            )

        if (
            send_outreach_email
            and "write_leads_to_crm" in t
            and "send_outreach_emails" not in t
            and self._leads_qualified > 0
            and any((str(x.get("email") or "")).strip() for x in self._last_qualified_leads)
        ):
            return (
                "Continue: call send_outreach_emails for the qualified leads that have email addresses "
                "(use the message template from the user request if one was given). "
                "Then output only the final JSON."
            )

        return None

    async def run(
        self,
        query: str,
        max_leads: int = 20,
        write_to_crm: bool = True,
        send_outreach_email: bool = True,
        review_callback: ReviewCallback | None = None,
        hubspot_auth_callback: HubspotAuthCallback | None = None,
        gmail_oauth_callback: GmailOAuthCallback | None = None,
        crm_setup_callback: CrmSetupCallback | None = None,
        tenant_id: str = "default",
        gmail_token_store=None,
        crm_type: str | None = None,
        gsheets_token_store=None,
        spreadsheet_id: str | None = None,
        notion_token_store=None,
        notion_database_id: str | None = None,
        excel_token_store=None,
        excel_workbook_name: str = "Leads",
    ) -> dict:
        start_ms = int(time.time() * 1000)
        self._leads_found = self._leads_qualified = self._leads_written_to_crm = self._emails_sent = 0
        self._tenant_id             = tenant_id
        self._gmail_token_store     = gmail_token_store
        self._crm_type              = crm_type
        self._gsheets_store   = gsheets_token_store
        self._spreadsheet_id  = spreadsheet_id
        self._notion_store      = notion_token_store
        self._notion_database_id = notion_database_id
        self._excel_store       = excel_token_store
        self._excel_workbook    = excel_workbook_name

        provider = get_provider()
        tools    = provider.format_tools(TOOL_SCHEMAS)
        system   = SYSTEM_PROMPT.format(
            max_leads=max_leads,
            send_outreach_email=send_outreach_email,
        )

        messages = [{"role": "user", "content": query}]
        logger.info("Agent: provider=%s query='%s' max_leads=%d crm=%s",
                    os.getenv("LLM_PROVIDER", "openrouter"), query, max_leads, crm_type)

        response = None
        idle_iters = 0  # consecutive iterations with no tool call and no done
        self._tools_used_this_run = set()
        pipeline_recoveries = 0
        max_pipeline_recoveries = int(os.getenv("LEAD_GEN_MAX_PIPELINE_RECOVERIES", "6"))

        for iteration in range(20):
            response = await provider.chat(messages, tools, system)
            logger.info("Iter %d: done=%s tools=%d", iteration + 1, response["done"], len(response["tool_calls"]))
            if response["done"]:
                recovery = self._pipeline_recovery_nudge(
                    write_to_crm=write_to_crm,
                    send_outreach_email=send_outreach_email,
                )
                if recovery and pipeline_recoveries < max_pipeline_recoveries:
                    pipeline_recoveries += 1
                    logger.warning(
                        "Model stopped early (%d leads found, %d qualified tools=%s). "
                        "Pipeline recovery %d/%d.",
                        self._leads_found,
                        self._leads_qualified,
                        sorted(self._tools_used_this_run),
                        pipeline_recoveries,
                        max_pipeline_recoveries,
                    )
                    if isinstance(provider, AnthropicProvider):
                        messages.append({"role": "assistant", "content": response["_raw_content"]})
                    else:
                        raw_done = response["_raw_message"]
                        messages.append({"role": "assistant", "content": raw_done.content or ""})
                    messages.append({"role": "user", "content": recovery})
                    continue
                break

            if isinstance(provider, AnthropicProvider):
                messages.append({"role": "assistant", "content": response["_raw_content"]})
                blocks = []
                for tc in response["tool_calls"]:
                    try:
                        result = await self._execute_tool(
                            tc["name"], tc["input"], write_to_crm, send_outreach_email,
                            review_callback, hubspot_auth_callback, gmail_oauth_callback,
                            crm_setup_callback,
                        )
                        content, error = json.dumps(result), False
                    except Exception as e:
                        logger.error("Tool %s failed: %s", tc["name"], e, exc_info=True)
                        content, error = json.dumps({"error": str(e)}), True
                    blocks.append(provider.make_tool_result_block(tc["id"], content, is_error=error))
                messages.append({"role": "user", "content": blocks})
            else:
                raw = response["_raw_message"]
                has_tools = bool(response["tool_calls"])

                if has_tools or response["done"]:
                    # Model made tool calls or is genuinely done — commit to history
                    assistant_msg: dict = {"role": "assistant", "content": raw.content}
                    if raw.tool_calls:
                        assistant_msg["tool_calls"] = [
                            {"id": tc.id, "type": "function",
                             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                            for tc in raw.tool_calls
                        ]
                    messages.append(assistant_msg)
                    idle_iters = 0
                else:
                    # Pure reasoning text — don't add it to history (bloats context).
                    # Inject a pre-filled JSON nudge instead.
                    idle_iters += 1
                    logger.warning("Iter %d: reasoning text only, idle_streak=%d — dropping from history",
                                   iteration + 1, idle_iters)
                    if idle_iters >= 4:
                        logger.warning("idle_streak=%d hit limit — exiting loop with tracked state", idle_iters)
                        break
                    final_json_nudge = (
                        "All tools have already been called. "
                        "Do NOT reason. Output ONLY this JSON right now, nothing else:\n"
                        "{{\n"
                        f'  "leads_found": {self._leads_found},\n'
                        f'  "leads_qualified": {self._leads_qualified},\n'
                        f'  "leads_written_to_crm": {self._leads_written_to_crm},\n'
                        f'  "emails_sent": {self._emails_sent},\n'
                        '  "search_mode": "local",\n'
                        '  "qualified_leads": [],\n'
                        '  "summary": "Task complete."\n'
                        "}}"
                    )
                    messages.append({"role": "user", "content": final_json_nudge})

                for tc in response["tool_calls"]:
                    try:
                        result = await self._execute_tool(
                            tc["name"], tc["input"], write_to_crm, send_outreach_email,
                            review_callback, hubspot_auth_callback, gmail_oauth_callback,
                            crm_setup_callback,
                        )
                    except Exception as e:
                        logger.error("Tool %s failed: %s", tc["name"], e, exc_info=True)
                        result = {"error": str(e)}
                    messages = provider.append_tool_result(messages, tc["id"], result)

        final_text = response["text"] if response else ""
        result = self._parse_final_response(final_text)
        # Always use tracked counters — they are authoritative regardless of model output
        result["leads_found"]          = self._leads_found
        result["leads_qualified"]      = self._leads_qualified
        result["leads_written_to_crm"] = self._leads_written_to_crm
        result["emails_sent"]          = self._emails_sent
        if not result.get("qualified_leads") and self._last_qualified_leads:
            result["qualified_leads"]  = self._last_qualified_leads
        if not result.get("summary"):
            result["summary"] = (
                f"Found {self._leads_found} leads, {self._leads_qualified} qualified, "
                f"{self._leads_written_to_crm} written to CRM."
            )
        result["execution_time_ms"] = int(time.time() * 1000) - start_ms
        result["status"]   = "success"
        result["provider"] = os.getenv("LLM_PROVIDER", "openrouter")
        result["crm_type"] = self._crm_type
        logger.info("Done %dms | found=%d qualified=%d crm=%d emails=%d",
                    result["execution_time_ms"], result["leads_found"],
                    result["leads_qualified"], result["leads_written_to_crm"], result["emails_sent"])
        return result

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        write_to_crm: bool,
        send_outreach_email: bool = True,
        review_callback: ReviewCallback | None = None,
        hubspot_auth_callback: HubspotAuthCallback | None = None,
        gmail_oauth_callback: GmailOAuthCallback | None = None,
        crm_setup_callback: CrmSetupCallback | None = None,
    ) -> Any:
        self._tools_used_this_run.add(tool_name)

        # ── Lead discovery ────────────────────────────────────────────────────
        if tool_name == "search_leads":
            mode = detect_mode(tool_input.get("query", ""))
            res = await smart_search(
                query=tool_input.get("query", ""),
                person_titles=tool_input.get("person_titles"),
                industries=tool_input.get("industries"),
                geographies=tool_input.get("geographies"),
                company_size_min=tool_input.get("company_size_min"),
                company_size_max=tool_input.get("company_size_max"),
                per_page=tool_input.get("per_page", 25),
                max_results=tool_input.get("max_results", 20),
            )
            self._last_search_results = res.get("results", [])
            self._leads_found = res.get("count", len(self._last_search_results))
            return res

        elif tool_name == "search_prospects":
            return await search_prospects(**tool_input)

        elif tool_name == "find_email":
            return await find_email(
                first_name=tool_input["first_name"],
                last_name=tool_input["last_name"],
                domain=tool_input["domain"],
            )

        elif tool_name == "score_and_filter_leads":
            raw = tool_input.get("leads", [])
            if isinstance(raw, dict):
                raw = raw.get("results", [])
            if not raw and self._last_search_results:
                raw = self._last_search_results
            qualified = [{**lead, "qualified": True} for lead in raw]
            disqualified: list[dict] = []
            self._last_qualified_leads = qualified
            self._leads_qualified = len(qualified)
            return {"qualified": qualified, "disqualified_count": len(disqualified), "total_scored": len(raw)}

        # ── CRM write ─────────────────────────────────────────────────────────
        elif tool_name == "write_leads_to_crm":
            if not write_to_crm:
                return {"skipped": True, "reason": "write_to_crm=False"}
            leads = tool_input.get("leads", []) or self._last_qualified_leads
            return await self._crm_write(leads, hubspot_auth_callback, crm_setup_callback)

        # ── CRM read/search ───────────────────────────────────────────────────
        elif tool_name == "search_crm_leads":
            return await self._crm_search(
                query=tool_input.get("query", ""),
                status=tool_input.get("status"),
                limit=tool_input.get("limit", 20),
            )

        # ── CRM update ────────────────────────────────────────────────────────
        elif tool_name == "update_crm_lead":
            return await self._crm_update(str(tool_input["contact_id"]), tool_input["properties"])

        # ── CRM delete ────────────────────────────────────────────────────────
        elif tool_name == "delete_crm_lead":
            return await self._crm_delete(str(tool_input["contact_id"]))

        # ── Deals (HubSpot only) ──────────────────────────────────────────────
        elif tool_name == "create_deal":
            return await create_deal(
                deal_name=tool_input["deal_name"],
                contact_id=tool_input.get("contact_id"),
                pipeline=tool_input.get("pipeline", "default"),
                stage=tool_input.get("stage", "appointmentscheduled"),
                amount=tool_input.get("amount"),
                close_date=tool_input.get("close_date"),
            )

        elif tool_name == "update_deal":
            return await update_deal(tool_input["deal_id"], tool_input["properties"])

        elif tool_name == "get_deals":
            return {"deals": await get_deals_for_contact(tool_input["contact_id"])}

        # ── Email outreach ────────────────────────────────────────────────────
        elif tool_name == "send_outreach_emails":
            if not send_outreach_email:
                return {"skipped": True, "reason": "send_outreach_email=False"}

            leads = tool_input.get("leads", []) or self._last_qualified_leads
            if not leads:
                return {"skipped": True, "reason": "no_leads", "sent": 0, "failed": 0}

            previews = build_email_previews(
                leads,
                tool_input.get("subject", "Quick question, {first_name}"),
                tool_input.get("message_template", "Hi {first_name}, I'd love to connect."),
                tool_input.get("from_name", "Sales Team"),
            )

            if review_callback:
                previews = await review_callback(previews)
            if not previews:
                return {"skipped": True, "reason": "email_review_not_approved", "sent": 0, "failed": 0}

            if self._gmail_token_store:
                from integrations.gmail_oauth import get_valid_access_token, get_sender_email
                token = await get_valid_access_token(self._tenant_id, self._gmail_token_store)
                if not token and gmail_oauth_callback:
                    token, _ = await gmail_oauth_callback()
                if token:
                    sender = await get_sender_email(self._tenant_id, self._gmail_token_store) or "noreply"
                    result = await send_drafts_via_gmail(token, sender, previews)
                    self._emails_sent += result.get("sent", 0)
                    return result

            result = await send_from_drafts(previews)
            self._emails_sent += result.get("sent", 0)
            return result

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    # ── CRM dispatch helpers ──────────────────────────────────────────────────

    async def _crm_write(self, leads: list[dict], hubspot_auth_callback, crm_setup_callback=None) -> dict:
        crm = self._crm_type
        logger.info("_crm_write: crm=%s leads=%d", crm, len(leads))

        if not leads:
            logger.warning("_crm_write: called with empty leads list")
            return {"skipped": True, "reason": "No leads to write"}

        # If no CRM is configured, ask the user to pick and connect one
        if not crm:
            if crm_setup_callback:
                crm = await crm_setup_callback()
                self._crm_type = crm
            if not crm:
                logger.info("_crm_write: no CRM selected for tenant %s — defaulting to gsheets", self._tenant_id)
                crm = "gsheets"
                self._crm_type = crm

        if crm == "notion":
            token = await self._get_notion_token()
            db_id = self._notion_database_id
            # Re-read database_id from store in case user connected mid-run
            if not db_id and self._notion_store:
                from integrations.notion_oauth import get_database_id
                db_id = await get_database_id(self._tenant_id, self._notion_store)
                self._notion_database_id = db_id
            logger.info("_crm_write notion: token_present=%s db_id=%r", bool(token), db_id)
            if not token:
                logger.warning("_crm_write notion: no token for tenant %s", self._tenant_id)
                return {"error": "Notion not connected"}
            if not db_id:
                logger.warning("_crm_write notion: no database_id for tenant %s — Notion requires a database ID", self._tenant_id)
                return {"error": "Notion database_id missing. Use PAT connect at /crm/notion/connect with your database ID."}
            results = await bulk_upsert_notion_leads(token, db_id, leads)
            written = sum(1 for r in results if not r.get("crm_result", {}).get("error"))
            self._leads_written_to_crm += written
            logger.info("_crm_write notion: wrote %d/%d leads", written, len(leads))
            return {"crm": "notion", "written": written, "results": results}

        if crm == "excel":
            token = await self._get_excel_token()
            logger.info("_crm_write excel: token_present=%s workbook=%r", bool(token), self._excel_workbook)
            if not token:
                logger.warning("_crm_write excel: no token for tenant %s", self._tenant_id)
                return {"error": "Excel / OneDrive not connected"}
            item_id = await ensure_excel_workbook(token, self._excel_workbook)
            if not item_id:
                return {"error": "Could not create or find Excel workbook"}
            results = await bulk_upsert_excel_leads(token, item_id, leads)
            written = sum(1 for r in results if not r.get("crm_result", {}).get("error"))
            self._leads_written_to_crm += written
            logger.info("_crm_write excel: wrote %d/%d leads", written, len(leads))
            return {"crm": "excel", "written": written, "results": results}

        if crm == "gsheets":
            token = await self._get_gsheets_token()
            sid   = self._spreadsheet_id
            logger.info("_crm_write gsheets: token_present=%s sid=%r", bool(token), sid)
            if token and not sid:
                # Auto-create a sheet when connected but no spreadsheet was configured
                from tools.gsheets_tool import create_spreadsheet
                from integrations.gsheets_oauth import update_spreadsheet_id
                sid = await create_spreadsheet(token)
                logger.info("_crm_write gsheets: auto-created spreadsheet %s", sid)
                if self._gsheets_store:
                    await update_spreadsheet_id(self._tenant_id, sid, self._gsheets_store)
                self._spreadsheet_id = sid
            if not token or not sid:
                logger.warning("_crm_write gsheets: token=%s sid=%r — aborting", bool(token), sid)
                return {"error": "Google Sheets not connected"}
            results = await bulk_upsert_sheet_leads(token, sid, leads)
            written = sum(1 for r in results if not r.get("crm_result", {}).get("error"))
            self._leads_written_to_crm += written
            logger.info("_crm_write gsheets: wrote %d/%d leads to %s", written, len(leads), sid)
            return {"crm": "gsheets", "written": written, "results": results}

        # HubSpot (default when crm_type is set but unrecognised, or explicitly "hubspot")
        await self._ensure_hubspot_token(hubspot_auth_callback)
        results = await bulk_upsert_contacts(leads)
        written = sum(1 for r in results if r.get("crm_result", {}).get("hubspot_id"))
        self._leads_written_to_crm += written
        logger.info("_crm_write hubspot: wrote %d/%d leads", written, len(leads))
        return {"crm": "hubspot", "written": written, "results": results}

    async def _crm_search(self, query: str, status: str | None, limit: int) -> dict:
        crm = self._crm_type

        if crm == "notion":
            token = await self._get_notion_token()
            db_id = self._notion_database_id
            if not token or not db_id:
                return {"error": "Notion not connected"}
            results = await search_notion_leads(token, db_id, query=query, status=status, limit=limit)
            return {"crm": "notion", "results": results, "count": len(results)}

        if crm == "excel":
            token = await self._get_excel_token()
            if not token:
                return {"error": "Excel not connected"}
            item_id = await ensure_excel_workbook(token, self._excel_workbook)
            results = await search_excel_leads(token, item_id, query=query, status=status, limit=limit)
            return {"crm": "excel", "results": results, "count": len(results)}

        if crm == "gsheets":
            token = await self._get_gsheets_token()
            sid   = self._spreadsheet_id
            if not token or not sid:
                return {"error": "Google Sheets not connected"}
            results = await search_leads_in_sheet(token, sid, query=query, status=status)
            return {"crm": "gsheets", "results": results[:limit], "count": len(results)}

        # HubSpot
        filters = []
        if status:
            filters.append({"propertyName": "hs_lead_status", "operator": "EQ", "value": status})
        results = await search_contacts(query=query, filters=filters or None, limit=limit)
        return {"crm": "hubspot", "results": results, "count": len(results)}

    async def _crm_update(self, contact_id: str, properties: dict) -> dict:
        crm = self._crm_type

        if crm == "notion":
            token = await self._get_notion_token()
            if not token:
                return {"error": "Notion not connected"}
            return await update_notion_lead(token, contact_id, properties)

        if crm == "excel":
            token = await self._get_excel_token()
            if not token:
                return {"error": "Excel not connected"}
            item_id = await ensure_excel_workbook(token, self._excel_workbook)
            return await update_excel_lead(token, item_id, int(contact_id), properties)

        if crm == "gsheets":
            token = await self._get_gsheets_token()
            sid   = self._spreadsheet_id
            if not token or not sid:
                return {"error": "Google Sheets not connected"}
            return await update_lead_in_sheet(token, sid, int(contact_id), properties)

        return await update_contact(contact_id, properties)

    async def _crm_delete(self, contact_id: str) -> dict:
        crm = self._crm_type

        if crm == "notion":
            token = await self._get_notion_token()
            if not token:
                return {"error": "Notion not connected"}
            return await delete_notion_lead(token, contact_id)

        if crm == "excel":
            token = await self._get_excel_token()
            if not token:
                return {"error": "Excel not connected"}
            item_id = await ensure_excel_workbook(token, self._excel_workbook)
            return await delete_excel_lead(token, item_id, int(contact_id))

        if crm == "gsheets":
            token = await self._get_gsheets_token()
            sid   = self._spreadsheet_id
            if not token or not sid:
                return {"error": "Google Sheets not connected"}
            return await delete_lead_from_sheet(token, sid, int(contact_id))

        return await delete_contact(contact_id)

    # ── Token getters ─────────────────────────────────────────────────────────

    async def _ensure_hubspot_token(self, hubspot_auth_callback):
        if get_key("HUBSPOT_API_KEY"):
            return
        if not hubspot_auth_callback:
            return
        logger.info("HubSpot key missing — triggering auth interrupt")
        try:
            token = await hubspot_auth_callback()
            set_credentials({"HUBSPOT_API_KEY": token})
        except Exception as exc:
            # User declined / no token provided → fall through to mock mode
            logger.warning("HubSpot auth declined (%s) — using mock CRM write", exc)

    async def _get_gsheets_token(self) -> str | None:
        if not self._gsheets_store:
            return None
        from integrations.gsheets_oauth import get_valid_access_token
        return await get_valid_access_token(self._tenant_id, self._gsheets_store)

    async def _get_notion_token(self) -> str | None:
        if not self._notion_store:
            return None
        from integrations.notion_oauth import get_access_token
        return await get_access_token(self._tenant_id, self._notion_store)

    async def _get_excel_token(self) -> str | None:
        if not self._excel_store:
            return None
        from integrations.excel_oauth import get_valid_access_token
        return await get_valid_access_token(self._tenant_id, self._excel_store)

    def _parse_final_response(self, text: str) -> dict:
        import re
        candidates = []
        for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL):
            candidates.append(m.group(1))
        depth = start = None
        for i, ch in enumerate(text):
            if ch == "{":
                if depth is None or depth == 0:
                    start = i
                    depth = 0
                depth += 1
            elif ch == "}" and depth:
                depth -= 1
                if depth == 0:
                    candidates.append(text[start: i + 1])
                    depth = start = None
        for raw in candidates:
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "leads_found" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        logger.warning("Could not parse JSON from agent response")
        return {
            "leads_found": 0, "leads_qualified": 0, "leads_written_to_crm": 0,
            "emails_sent": 0, "qualified_leads": [],
            "summary": text[:500] if text else "Agent completed.",
        }
