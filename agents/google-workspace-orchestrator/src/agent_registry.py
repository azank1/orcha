"""Registry: domain agent id → workspace-mcp tool names (per upstream README)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

# Tool names match https://github.com/taylorwilsdon/google_workspace_mcp (Available Tools).
# If upstream renames a tool, update this map; unknown tools still match via _KEYWORD_FALLBACK.

TOOL_NAMES_BY_DOMAIN: Final[dict[str, frozenset[str]]] = {
    "workspace_calendar": frozenset(
        {
            "list_calendars",
            "get_events",
            "manage_event",
            "create_calendar",
            "query_freebusy",
            "manage_out_of_office",
            "manage_focus_time",
        }
    ),
    "workspace_drive": frozenset(
        {
            "search_drive_files",
            "get_drive_file_content",
            "get_drive_file_download_url",
            "create_drive_file",
            "create_drive_folder",
            "import_to_google_doc",
            "get_drive_shareable_link",
            "list_drive_items",
            "copy_drive_file",
            "update_drive_file",
            "manage_drive_access",
            "set_drive_file_permissions",
            "get_drive_file_permissions",
            "check_drive_file_public_access",
        }
    ),
    "workspace_gmail": frozenset(
        {
            "search_gmail_messages",
            "get_gmail_message_content",
            "get_gmail_messages_content_batch",
            "send_gmail_message",
            "get_gmail_thread_content",
            "modify_gmail_message_labels",
            "list_gmail_labels",
            "list_gmail_filters",
            "manage_gmail_label",
            "manage_gmail_filter",
            "draft_gmail_message",
            "get_gmail_threads_content_batch",
            "batch_modify_gmail_message_labels",
            "start_google_auth",
        }
    ),
    "workspace_docs": frozenset(
        {
            "get_doc_content",
            "create_doc",
            "modify_doc_text",
            "search_docs",
            "find_and_replace_doc",
            "list_docs_in_folder",
            "insert_doc_elements",
            "update_paragraph_style",
            "get_doc_as_markdown",
            "insert_doc_image",
            "update_doc_headers_footers",
            "batch_update_doc",
            "inspect_doc_structure",
            "export_doc_to_pdf",
            "create_table_with_data",
            "debug_table_structure",
            "list_document_comments",
            "manage_document_comment",
        }
    ),
    "workspace_sheets": frozenset(
        {
            "read_sheet_values",
            "modify_sheet_values",
            "create_spreadsheet",
            "list_spreadsheets",
            "get_spreadsheet_info",
            "format_sheet_range",
            "list_sheet_tables",
            "create_sheet",
            "append_table_rows",
            "list_spreadsheet_comments",
            "manage_spreadsheet_comment",
            "manage_conditional_formatting",
        }
    ),
    "workspace_slides": frozenset(
        {
            "create_presentation",
            "get_presentation",
            "batch_update_presentation",
            "get_page",
            "get_page_thumbnail",
            "list_presentation_comments",
            "manage_presentation_comment",
        }
    ),
    "workspace_forms": frozenset(
        {
            "create_form",
            "get_form",
            "set_publish_settings",
            "get_form_response",
            "list_form_responses",
            "batch_update_form",
        }
    ),
    "workspace_tasks": frozenset(
        {
            "list_tasks",
            "get_task",
            "manage_task",
            "list_task_lists",
            "get_task_list",
            "manage_task_list",
        }
    ),
    "workspace_contacts": frozenset(
        {
            "search_contacts",
            "get_contact",
            "list_contacts",
            "manage_contact",
            "list_contact_groups",
            "get_contact_group",
            "manage_contacts_batch",
            "manage_contact_group",
        }
    ),
    "workspace_chat": frozenset(
        {
            "list_spaces",
            "get_messages",
            "send_message",
            "search_messages",
            "create_reaction",
            "download_chat_attachment",
        }
    ),
    "workspace_search": frozenset(
        {
            "search_custom",
            "get_search_engine_info",
        }
    ),
    "workspace_apps_script": frozenset(
        {
            "list_script_projects",
            "get_script_project",
            "get_script_content",
            "create_script_project",
            "update_script_content",
            "run_script_function",
            "list_deployments",
            "manage_deployment",
            "list_script_processes",
        }
    ),
}

# When explicit names miss (upstream added tools), match by substring on tool name.
_KEYWORD_FALLBACK: dict[str, tuple[str, ...]] = {
    "workspace_calendar": ("calendar", "event", "freebusy", "office", "focus_time"),
    "workspace_drive": ("drive",),
    "workspace_gmail": ("gmail",),
    "workspace_docs": ("doc", "paragraph", "document_comment"),
    "workspace_sheets": ("sheet", "spreadsheet", "table_rows", "conditional_format"),
    "workspace_slides": ("presentation", "slide", "page_thumbnail"),
    "workspace_forms": ("form",),
    "workspace_tasks": ("task",),
    "workspace_contacts": ("contact",),
    "workspace_chat": (
        "list_spaces",
        "get_messages",
        "send_message",
        "search_messages",
        "create_reaction",
        "download_chat",
    ),
    "workspace_search": ("search_custom", "search_engine", "cse"),
    "workspace_apps_script": (
        "script_project",
        "script_content",
        "run_script",
        "deployment",
        "script_process",
    ),
}

PLANNER_DOMAIN_IDS: Final[tuple[str, ...]] = (
    "workspace_drive",
    "workspace_gmail",
    "workspace_calendar",
    "workspace_docs",
    "workspace_sheets",
    "workspace_slides",
    "workspace_forms",
    "workspace_tasks",
    "workspace_contacts",
    "workspace_chat",
    "workspace_search",
    "workspace_apps_script",
)

ALL_SKILL_IDS: Final[tuple[str, ...]] = ("workspace_orchestrator",) + PLANNER_DOMAIN_IDS


def _domain_description(domain_id: str) -> str:
    return {
        "workspace_orchestrator": "Cross-service DAG over all workspace-mcp tools",
        "workspace_drive": "Google Drive files and permissions",
        "workspace_gmail": "Gmail search, threads, drafts, send",
        "workspace_calendar": "Calendars, events, free/busy, OOO, focus time",
        "workspace_docs": "Google Docs content, comments, export",
        "workspace_sheets": "Google Sheets ranges, tables, formatting",
        "workspace_slides": "Google Slides presentations and pages",
        "workspace_forms": "Google Forms and responses",
        "workspace_tasks": "Google Tasks lists and items",
        "workspace_contacts": "Google People / Contacts and groups",
        "workspace_chat": "Google Chat spaces and messages",
        "workspace_search": "Programmable Search (Custom Search API)",
        "workspace_apps_script": "Apps Script projects, deployments, execution",
    }.get(domain_id, domain_id)


@dataclass(frozen=True)
class DomainSpec:
    id: str
    description: str


DOMAINS: tuple[DomainSpec, ...] = tuple(
    DomainSpec(id=did, description=_domain_description(did))
    for did in ("workspace_orchestrator",) + PLANNER_DOMAIN_IDS
)


def tools_for_domain(domain_id: str, all_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if domain_id == "workspace_orchestrator":
        return all_tools

    explicit = TOOL_NAMES_BY_DOMAIN.get(domain_id)
    if explicit is None:
        return all_tools

    by_name = {str(t.get("name") or ""): t for t in all_tools if t.get("name")}
    picked = [by_name[n] for n in explicit if n in by_name]
    if picked:
        return picked

    keys = _KEYWORD_FALLBACK.get(domain_id, ())
    out: list[dict[str, Any]] = []
    for t in all_tools:
        name = (t.get("name") or "").lower()
        if any(k in name for k in keys):
            out.append(t)
    return out if out else all_tools
