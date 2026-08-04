"""Pydantic model for the Agentic Authorization Charter (aac-srs.md FR-1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IssuedBy(BaseModel):
    """Legal entity (principal) issuing the charter."""

    legal_name: str = Field(..., min_length=1)
    identifier_type: Literal["CIN", "GST", "Aadhaar", "CNPJ", "UEN", "LEI"]
    identifier_value: str = Field(..., min_length=1)
    regulator_license: str | None = None


class AgentIdentity(BaseModel):
    """Identity of the chartered agent."""

    agent_id: str = Field(..., description="Agent DID, e.g. did:orcha:agent:*.")
    model_attestation: str | None = None
    deployment_hash: str | None = None
    agent_public_key: str | None = Field(
        default=None,
        description=(
            "Base64 Ed25519 public key bound to the agent DID; the holder "
            "proves possession by signing request hashes (FR-4 holder binding)."
        ),
    )


class CharterScope(BaseModel):
    """Authorised scope of the charter (mirrors the OAuth 2.0 scope model)."""

    dpi_rails: list[str] = Field(
        default_factory=list,
        description="DPI rails the authorisation covers, e.g. UPI, AccountAggregator, ULI.",
    )
    permitted_actions: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    max_transaction_value: str | None = Field(
        default=None,
        description="Maximum per-transaction value, decimal as string.",
    )
    human_approval_required_above: str | None = Field(
        default=None,
        description="Value above which a named human must approve, decimal as string.",
    )
    allowed_counterparties: list[str] = Field(
        default_factory=list,
        description="Allowed payee / counterparty identifiers (RFC 0001 passthrough).",
    )
    jurisdictions: list[str] = Field(
        default_factory=list,
        description="Authorised operating jurisdictions (RFC 0001 passthrough).",
    )


class CharterDelegation(BaseModel):
    allowed: bool = False
    max_depth: int = Field(default=0, ge=0)


class CharterValidity(BaseModel):
    """RFC 3339 validity window."""

    not_before: str
    not_after: str


class OperatorSignature(BaseModel):
    algorithm: str = "Ed25519"
    public_key: str = Field(..., description="Base64 Ed25519 public key.")
    signature: str = Field(..., description="Base64 signature over charter_hash.")


class AACCharter(BaseModel):
    """Versioned, machine-readable authorisation charter (FR-1).

    ``operator_signature`` is attached at issuance by ``signing.sign_charter``;
    ``regulator_attestation`` is an optional later endorsement. Absence of a
    scope dimension means "unspecified", never "unrestricted".
    """

    charter_id: str
    version: str = "1.0"
    issued_by: IssuedBy
    agent_identity: AgentIdentity
    authorized_scope: CharterScope
    delegation: CharterDelegation = Field(default_factory=CharterDelegation)
    validity: CharterValidity | None = None
    operator_signature: OperatorSignature | None = None
    regulator_attestation: dict[str, Any] | None = None
    charter_hash: str | None = Field(
        default=None,
        description="sha256 hex of the canonical unsigned charter; set by sign_charter.",
    )
    parent_charter_hash: str | None = Field(
        default=None,
        description="charter_hash of the parent charter for delegated charters (FR-3).",
    )
