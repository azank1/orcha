"""Pydantic models for emerge.yaml configuration."""

from typing import Any

from pydantic import BaseModel, Field


class IdentityConfig(BaseModel):
    """Identity section of emerge.yaml."""

    id: str = Field(
        ...,
        description=(
            "DID: did:metaorcha:agent:* (user agents) or "
            "did:metaorcha:system:* (platform MCP tools)"
        ),
    )
    name: str
    version: str
    description: str
    tags: list[str] = Field(default_factory=list)


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

    type: str = Field(..., description="mcp or a2a")
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


class EmergeConfig(BaseModel):
    """
    Complete emerge.yaml configuration structure.

    This is the schema that developers use to register their agents.
    """

    identity: IdentityConfig
    protocol: ProtocolConfig
    health_endpoint: str
    security: SecurityConfig
    payment: PaymentConfig | None = None

    def validate_did_format(self) -> bool:
        """Validate that ID follows Metaorcha DID format (user or platform)."""
        return self.identity.id.startswith(
            ("did:metaorcha:agent:", "did:metaorcha:system:")
        )

    def validate_protocol_type(self) -> bool:
        """Validate protocol type is supported."""
        return self.protocol.type.lower() in ["mcp", "a2a"]

    def validate_transport_type(self) -> bool:
        """Validate transport type is supported."""
        return self.protocol.transport.type.lower() in ["sse", "stdio", "http"]
