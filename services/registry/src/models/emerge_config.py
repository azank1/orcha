"""Pydantic models for emerge.yaml configuration."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class IdentityConfig(BaseModel):
    """Identity section of emerge.yaml."""

    id: str = Field(
        ...,
        description=(
            "DID: did:orcha:agent:* (user agents) or "
            "did:orcha:system:* (platform MCP tools)"
        ),
    )
    name: str
    version: str
    description: str
    tags: list[str] = Field(default_factory=list)
    public_key: str | None = Field(
        default=None,
        description=(
            "Optional Ed25519 public key (base64) for signed identity. "
            "Reserved for emerge/1.1 signed-identity verification; "
            "unused in mock OSS mode."
        ),
    )


class TransportConfig(BaseModel):
    """Transport configuration."""

    type: str = Field(..., description="sse, stdio, or http")
    endpoint: str | None = None  # For SSE/HTTP
    command: str | None = None  # For STDIO
    args: list[str] | None = None  # For STDIO
    env: dict[str, str] | None = (
        None  # For STDIO — env var templates e.g. {"KEY": "${KEY}"}
    )


class ProtocolConfig(BaseModel):
    """Protocol section of emerge.yaml."""

    type: str = Field(..., description="mcp, a2a, or computer_use")
    version: str
    transport: TransportConfig


class MTLSConfig(BaseModel):
    """mTLS configuration."""

    cert_vault_key: str
    key_vault_key: str
    ca_vault_key: str


class TransportLayerConfig(BaseModel):
    """Transport layer security configuration."""

    type: str = Field(..., description="tls, mtls, or none")
    mtls_config: MTLSConfig | None = None


class AuthStrategyConfig(BaseModel):
    """Authentication strategy configuration."""

    id: str
    type: str = Field(..., description="x_api_key, http_bearer, oauth2, oauth2_dcr")
    capability_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Capability IDs this strategy applies to. "
            "Empty list = global (applies to all capabilities of this agent). "
            "Non-empty = only resolved when the invoked capability_id is in this list."
        ),
    )
    config: dict[str, Any]


class SecurityConfig(BaseModel):
    """Security section of emerge.yaml."""

    transport_layer: TransportLayerConfig
    auth_strategies: list[AuthStrategyConfig] = Field(default_factory=list)


class PaymentConfig(BaseModel):
    """Payment configuration for an agent.

    Supports a simple enabled/base_fee model — x402 payment headers are no longer used.
    """

    enabled: bool = False
    # Price per invocation in USD as a string, e.g. "0.50".
    # Null / absent means the agent is free.
    base_fee: str | None = None


class PrincipalConfig(BaseModel):
    """Legal entity accountable for the agent (emerge/1.2, RFC 0002)."""

    legal_name: str = Field(..., min_length=1)
    identifier_type: Literal["CIN", "GST", "Aadhaar", "CNPJ", "UEN", "LEI"] = Field(
        ...,
        description="Typed legal identifier scheme.",
    )
    identifier_value: str = Field(..., min_length=1)
    regulator_license: str | None = Field(
        default=None,
        description="Optional regulator-issued licence reference.",
    )


class DelegationConfig(BaseModel):
    """Sub-agent charter delegation limits (emerge/1.2, RFC 0002)."""

    allowed: bool = False
    max_depth: int = Field(
        default=0,
        ge=0,
        description="Maximum delegation hops permitted below this charter.",
    )


class ValidityConfig(BaseModel):
    """Charter validity window, RFC 3339 datetimes (emerge/1.2, RFC 0002)."""

    not_before: str | None = None
    not_after: str | None = None


class AuthorizedScopeConfig(BaseModel):
    """Declared authorised-scope limits (emerge/1.1, RFC 0001; extended in 1.2, RFC 0002).

    Optional supervisory limits consumed by verifiers (e.g. the KY-A
    supervisory harness). Absence means "unspecified", not "unrestricted".
    """

    allowed_capabilities: list[str] = Field(
        default_factory=list,
        description="Capability/skill names the agent may invoke.",
    )
    spend_cap_usd: str | None = Field(
        default=None,
        description="Maximum M2M payment volume in scope, USD decimal as string.",
    )
    allowed_counterparties: list[str] = Field(
        default_factory=list,
        description="Allowed payee / counterparty identifiers.",
    )
    jurisdictions: list[str] = Field(
        default_factory=list,
        description="Authorised operating jurisdictions.",
    )
    principal: PrincipalConfig | None = Field(
        default=None,
        description="Legal entity accountable for the agent (AAC charter).",
    )
    rails: list[str] = Field(
        default_factory=list,
        description="DPI rails the authorisation covers, e.g. UPI, AccountAggregator, ULI.",
    )
    delegation: DelegationConfig | None = Field(
        default=None,
        description="Sub-agent charter delegation limits.",
    )
    human_approval_required_above: str | None = Field(
        default=None,
        description="Transaction value above which a named human must approve, decimal as string.",
    )
    validity: ValidityConfig | None = Field(
        default=None,
        description="Charter validity window, RFC 3339 datetimes.",
    )


class EmergeConfig(BaseModel):
    """
    Complete emerge.yaml configuration structure.

    This is the schema that developers use to register their agents.
    """

    schema_version: str = Field(
        default="1.0",
        description=(
            "Version of the emerge.yaml schema. Defaults to '1.0' when absent. "
            "Validated against docs/spec/emerge-yaml.schema.json. "
            "The spec is frozen-by-default; changes go through the RFC process."
        ),
    )
    identity: IdentityConfig
    protocol: ProtocolConfig
    health_endpoint: str
    security: SecurityConfig
    payment: PaymentConfig | None = None
    authorized_scope: AuthorizedScopeConfig | None = None

    def validate_did_format(self) -> bool:
        """Validate that ID follows the Orcha DID format (user or platform)."""
        return self.identity.id.startswith(("did:orcha:agent:", "did:orcha:system:"))

    def validate_protocol_type(self) -> bool:
        """Validate protocol type is supported."""
        return self.protocol.type.lower() in ["mcp", "a2a", "computer_use"]

    def validate_transport_type(self) -> bool:
        """Validate transport type is supported."""
        return self.protocol.transport.type.lower() in ["sse", "stdio", "http"]
