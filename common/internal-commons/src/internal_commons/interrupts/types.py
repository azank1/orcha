"""InterruptType — master registry of all interrupt types in the Orcha platform."""

from __future__ import annotations

from enum import StrEnum


class InterruptType(StrEnum):
    """
    Master registry of all interrupt types in the Orcha platform.

    Interrupt types represent moments where workflow execution must pause
    and wait for explicit user action before it can continue.

    Naming convention: <CATEGORY>_<ACTION>
    - AUTH_*   : Credential or authorization required
    - HITL_*   : Human-in-the-loop decisions
    - AGENT_*  : Signals originating from an agent (not PreFlight)

    PAYMENT_REQUIRED is intentionally excluded from this patch.
    It will be added when the x402 payment integration is implemented,
    as its resume contract depends on on-chain settlement semantics
    that are not yet finalised.
    """

    # — Auth interrupts ──────────────────────────────────────────────────────
    AUTH_CALLBACK = "AUTH_CALLBACK"
    """
    Orcha-managed OAuth flow. Orcha holds the client_id / client_secret
    for a known provider (e.g. Google, GitHub). PreFlightManager builds the
    authorization URL. After user consent, Orcha exchanges the code for
    tokens and stores them in VaultService. The agent never sees the OAuth
    mechanics — it just receives an Authorization header on the next call.
    """

    AUTH_FORM_SUBMISSION = "AUTH_FORM_SUBMISSION"
    """
    A static credential (API key or Bearer token) is missing from VaultService.
    The UI must display a form prompting the user to enter the value.
    On submission, the value is saved to the vault and the session resumes.
    """

    AGENT_OAUTH_CALLBACK = "AGENT_OAUTH_CALLBACK"
    """
    Agent-managed OAuth flow. The agent developer owns their own OAuth client
    (client_id + client_secret) registered with an authorization server.
    Orcha surfaces the auth URL and pauses execution. The authorization
    server redirects directly to the agent callback, the agent exchanges
    code → token, and then calls Gateway resume endpoint to continue.
    The agent client_secret never leaves the agent server.
    """

    # — Human-in-the-loop interrupts ─────────────────────────────────────────
    HITL_APPROVAL = "HITL_APPROVAL"
    """
    A destructive or irreversible action was detected by ExecutionMiddleware.
    The user must explicitly approve or deny before the agent call proceeds.
    Examples: deleting files, sending emails, making purchases, running
    database mutations flagged as destructive in the agent manifest.
    """

    HITL_CLARIFICATION = "HITL_CLARIFICATION"
    """
    The orchestrator LLM determined it cannot proceed without clarification
    from the user. Distinct from AGENT_CLARIFICATION — this originates from
    the SuperAgent orchestrator itself, not from a downstream agent.
    """

    # — Agent-originated interrupts ───────────────────────────────────────────
    AGENT_CLARIFICATION = "AGENT_CLARIFICATION"
    """
    A downstream A2A or ACP agent sent a clarification request mid-task.
    The agent's question must be surfaced to the user. The user's reply
    is forwarded back to the agent to continue task execution.
    """

    CRM_SETUP = "CRM_SETUP"
    """
    The agent needs a CRM to save results but none is connected for this tenant.
    The UI must surface a CRM selection and connection flow. After the user
    connects a CRM, the session resumes and the agent retries the write using
    whichever CRM the user configured.
    """

    # — Payment interrupts ────────────────────────────────────────────────────
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    """
    The user does not have sufficient credits to invoke the requested agent.
    Execution is suspended until the user tops up their balance.
    reason may be "insufficient_credits", "arrears", or "user_not_found".
    """
