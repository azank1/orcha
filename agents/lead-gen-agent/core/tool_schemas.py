"""
Tool schemas passed to Claude's function-calling API.
"""

TOOL_SCHEMAS = [
    {
        "name": "search_leads",
        "description": (
            "Unified lead search that works for ANY business type. "
            "Automatically routes to Google Maps (SMB / local / rural / traditional businesses) "
            "or Apollo.io (tech B2B professionals) based on the query — with fallback chains "
            "(Hunter.io domain search + Google Maps) whenever Apollo yields nothing or is missing. "
            "Always inspect `sources`, `count`, and `search_notes` in the tool result before "
            "claiming failure. "
            "Local examples: 'restaurants in Lahore', 'grain farms in rural Iowa', 'plumbers in Manchester'. "
            "B2B examples: 'fintech CTOs in US', 'SaaS CEOs with 50-200 employees'. "
            "Local mode returns: name, address, rating, reviews, website, phone. "
            "B2B mode returns: full_name, title, company, email, LinkedIn. "
            "Always include a city/region for local queries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query. Include location for local/SMB/rural searches."},
                "person_titles": {"type": "array", "items": {"type": "string"}, "description": "(B2B) Job titles e.g. ['CTO', 'CEO', 'Owner']"},
                "industries": {"type": "array", "items": {"type": "string"}, "description": "(B2B) Industries e.g. ['SaaS', 'Manufacturing']"},
                "geographies": {"type": "array", "items": {"type": "string"}, "description": "(B2B) Locations e.g. ['United States', 'Pakistan']"},
                "company_size_min": {"type": "integer", "description": "(B2B) Min employees (use 1 for sole traders / SMBs)"},
                "company_size_max": {"type": "integer", "description": "(B2B) Max employees"},
                "per_page": {"type": "integer", "description": "(B2B) Results to fetch per source (default 25)", "default": 25},
                "max_results": {"type": "integer", "description": "(Local) Max businesses to return (default 20, up to 60)", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_email",
        "description": (
            "Find a professional email via Hunter.io for a person at a company. "
            "Requires HUNTER_API_KEY. Use the company's real email domain hostname (e.g. acme.com) "
            "from the lead's company_domain field — not linkedin.com or other social hosts. "
            "Apollo search often leaves email empty; call this for each qualified B2B lead missing email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "domain": {
                    "type": "string",
                    "description": "Corporate domain hostname only, e.g. stripe.com (may come from lead company_domain)",
                },
            },
            "required": ["first_name", "last_name", "domain"],
        },
    },
    {
        "name": "score_and_filter_leads",
        "description": "Normalize and qualify discovered leads. This step currently marks all provided leads as qualified. Always run after searching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "leads": {"type": "array", "items": {"type": "object"}, "description": "Prospects from search_leads"},
            },
            "required": ["leads"],
        },
    },
    {
        "name": "write_leads_to_crm",
        "description": (
            "Write qualified leads to the connected CRM (HubSpot, Google Sheets, Excel, or Notion). "
            "Creates new rows/contacts or updates existing ones. "
            "Call this with ALL leads from the 'qualified' array — email is optional (local businesses may not have one)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "leads": {"type": "array", "items": {"type": "object"}, "description": "All qualified leads from score_and_filter_leads. Email is not required."},
            },
            "required": ["leads"],
        },
    },
    {
        "name": "search_crm_leads",
        "description": (
            "Search existing leads already in the CRM. Use this to check if a lead exists, "
            "find leads by status, or look up a specific contact before updating."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword search (name, email, company)"},
                "status": {"type": "string", "description": "Filter by lead status e.g. 'NEW', 'IN_PROGRESS', 'CONNECTED'"},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20},
            },
        },
    },
    {
        "name": "update_crm_lead",
        "description": (
            "Update an existing lead's properties in the CRM. "
            "Use this to change lead status, update contact info, or add notes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "HubSpot contact ID or sheet row index"},
                "properties": {
                    "type": "object",
                    "description": (
                        "Fields to update. For HubSpot: {hs_lead_status, jobtitle, company, notes_last_updated}. "
                        "Lead statuses: NEW, OPEN, IN_PROGRESS, OPEN_DEAL, UNQUALIFIED, ATTEMPTED_TO_CONTACT, CONNECTED, BAD_TIMING"
                    ),
                },
            },
            "required": ["contact_id", "properties"],
        },
    },
    {
        "name": "delete_crm_lead",
        "description": "Archive or delete a lead from the CRM. For HubSpot this is a soft delete (restorable).",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "HubSpot contact ID or sheet row index"},
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "create_deal",
        "description": (
            "Create a deal in HubSpot pipeline and associate it with a contact. "
            "Use when a lead becomes an opportunity. Only available when CRM is HubSpot."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_name": {"type": "string", "description": "Name for the deal e.g. 'Acme Corp - Enterprise Plan'"},
                "contact_id": {"type": "string", "description": "HubSpot contact ID to associate the deal with"},
                "stage": {
                    "type": "string",
                    "description": "Deal stage. Common values: appointmentscheduled, qualifiedtobuy, presentationscheduled, contractsent, closedwon, closedlost",
                    "default": "appointmentscheduled",
                },
                "amount": {"type": "number", "description": "Deal value in USD"},
                "close_date": {"type": "string", "description": "Expected close date in ISO format e.g. '2025-12-31'"},
                "pipeline": {"type": "string", "description": "Pipeline ID (default: 'default')", "default": "default"},
            },
            "required": ["deal_name"],
        },
    },
    {
        "name": "update_deal",
        "description": "Update a deal's stage, amount, or other properties in HubSpot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "string", "description": "HubSpot deal ID"},
                "properties": {
                    "type": "object",
                    "description": "Properties to update e.g. {dealstage: 'closedwon', amount: '5000'}",
                },
            },
            "required": ["deal_id", "properties"],
        },
    },
    {
        "name": "get_deals",
        "description": "Get all deals associated with a HubSpot contact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "description": "HubSpot contact ID"},
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "send_outreach_emails",
        "description": (
            "Send personalised cold-outreach emails to qualified leads. "
            "The system will pause for the user to review and edit drafts before sending."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "leads": {"type": "array", "items": {"type": "object"}, "description": "Leads with 'email' field"},
                "subject": {"type": "string", "description": "Subject line. Placeholders: {first_name}, {company}, {title}"},
                "message_template": {"type": "string", "description": "Email body with same placeholders"},
                "from_name": {"type": "string", "description": "From display name", "default": "Sales Team"},
            },
            "required": ["leads", "subject", "message_template"],
        },
    },
]
