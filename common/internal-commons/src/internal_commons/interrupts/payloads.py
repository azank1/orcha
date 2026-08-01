"""Per-type metadata Pydantic models for interrupt payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .types import InterruptType


class AuthCallbackMetadata(BaseModel):
    """Metadata for AUTH_CALLBACK interrupts."""

    auth_url: str
    """Full authorization URL to open in a popup. Constructed by PreFlightManager."""

    provider_name: str
    """Human-readable provider name for display. e.g. 'Google Calendar'."""

    scopes: list[str]
    """OAuth scopes being requested. Displayed to the user in the consent modal."""


class AuthFormSubmissionMetadata(BaseModel):
    """Metadata for AUTH_FORM_SUBMISSION interrupts."""

    form_title: str
    """Title shown in the credential input modal. e.g. 'API Key Required'."""

    field_label: str
    """Label for the input field. e.g. 'Notion API Key'."""

    vault_key: str
    """
    The vault key under which the submitted value will be stored.
    The Gateway's /sessions/{id}/submit-credential endpoint receives
    this key and calls VaultService.save_user_secret(user_id, vault_key, value).
    """

    is_secret: bool = True
    """If true, the UI should render a password-type input (value masked)."""

    agent_display_name: str | None = None
    """Optional agent name to contextualize the prompt."""


class AgentOAuthCallbackMetadata(BaseModel):
    """Metadata for AGENT_OAUTH_CALLBACK interrupts."""

    auth_url: str
    """
    Full authorization URL including client_id, redirect_uri, scopes, and
    HMAC-signed state parameter. Constructed from agent manifest auth config.
    redirect_uri points to the downstream agent callback endpoint declared
    by the agent auth strategy manifest config.
    """

    provider_name: str
    """Display name of the agent requesting authorization. e.g. 'Acme CRM Agent'."""

    scopes: list[str]
    """Scopes the agent is requesting on the authorization server."""

    agent_id: str
    """Internal agent_id — used by Gateway to look up the agent's callback_url."""


class HitlApprovalMetadata(BaseModel):
    """Metadata for HITL_APPROVAL interrupts."""

    action_description: str
    """
    Plain-English description of the action about to be taken.
    e.g. 'Delete 47 files in /prod/data/archive matching *.log'
    """

    risk_level: Literal["low", "medium", "high"]
    """Risk classification. Determined by ExecutionMiddleware based on
    the capability's `destructive` flag and action parameters."""

    agent_display_name: str
    """Name of the agent requesting to perform this action."""

    capability_name: str
    """Name of the tool/capability being invoked."""


class HitlClarificationMetadata(BaseModel):
    """Metadata for HITL_CLARIFICATION interrupts."""

    question: str
    """The clarifying question from the orchestrator LLM."""


class AgentClarificationMetadata(BaseModel):
    """Metadata for AGENT_CLARIFICATION interrupts."""

    question: str
    """The question from the downstream agent."""

    agent_display_name: str
    """Name of the agent asking the question."""

    agent_id: str


class CrmSetupMetadata(BaseModel):
    """Metadata for CRM_SETUP interrupts."""

    tenant_id: str
    """The tenant that needs a CRM configured. Used by the frontend to call /crm/status."""

    agent_display_name: str = "Agent"
    """Name of the agent requesting CRM setup."""

    lead_gen_url: str = "http://localhost:4567"
    """Base URL of the lead-gen agent — used by the frontend to drive CRM OAuth flows."""


class InsufficientCreditsMetadata(BaseModel):
    """Metadata for INSUFFICIENT_CREDITS interrupts."""

    reason: str
    """Why execution was blocked: 'insufficient_credits' | 'arrears' | 'user_not_found'."""

    amount_owed: str
    """Decimal string — amount owed for arrears, '0' for zero-balance blocks."""

    agent_display_name: str = ""
    """Human-readable name of the agent that triggered the guard."""


# — Union type — exhaustive across all InterruptTypes ─────────────────────────
# Discrimination is handled externally via INTERRUPT_METADATA_MAP.

AnyInterruptMetadata = (
    AuthCallbackMetadata
    | AuthFormSubmissionMetadata
    | AgentOAuthCallbackMetadata
    | HitlApprovalMetadata
    | HitlClarificationMetadata
    | AgentClarificationMetadata
    | CrmSetupMetadata
    | InsufficientCreditsMetadata
)

# Convenience map: InterruptType → metadata model class
# Used for runtime validation and documentation generation.
INTERRUPT_METADATA_MAP: dict[InterruptType, type[BaseModel]] = {
    InterruptType.AUTH_CALLBACK: AuthCallbackMetadata,
    InterruptType.AUTH_FORM_SUBMISSION: AuthFormSubmissionMetadata,
    InterruptType.AGENT_OAUTH_CALLBACK: AgentOAuthCallbackMetadata,
    InterruptType.HITL_APPROVAL: HitlApprovalMetadata,
    InterruptType.HITL_CLARIFICATION: HitlClarificationMetadata,
    InterruptType.AGENT_CLARIFICATION: AgentClarificationMetadata,
    InterruptType.CRM_SETUP: CrmSetupMetadata,
    InterruptType.INSUFFICIENT_CREDITS: InsufficientCreditsMetadata,
}
