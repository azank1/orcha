"""Universal Agent Manifest models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IdentityInfo(BaseModel):
    """Agent identity information."""

    id: str
    name: str
    version: str
    provider: str
    owner_contact: str
    description: str
    tags: list[str] = Field(default_factory=list)


class MetadataInfo(BaseModel):
    """Agent metadata."""

    indexed_at: datetime
    health_status: str
    health_endpoint: str


class TransportInfo(BaseModel):
    """Transport configuration."""

    type: str
    endpoint: str | None = None
    command: str | None = None
    args: list[str] | None = None


class ProtocolInfo(BaseModel):
    """Protocol information."""

    type: str
    version: str
    transport: TransportInfo


class MTLSConfig(BaseModel):
    """mTLS configuration."""

    cert_vault_key: str
    key_vault_key: str
    ca_vault_key: str


class TransportLayerSecurity(BaseModel):
    """Transport layer security."""

    type: str
    mtls_config: MTLSConfig | None = None


class AuthStrategy(BaseModel):
    """Authentication strategy."""

    id: str
    type: str
    config: dict[str, Any]


class SecurityInfo(BaseModel):
    """Security information."""

    transport_layer: TransportLayerSecurity
    auth_strategies: list[AuthStrategy] = Field(default_factory=list)


class PaymentConfigInfo(BaseModel):
    """Payment configuration details."""

    enabled: bool
    chain_id: str | None = None
    recipient_address: str | None = None
    asset: str | None = None
    token_address: str | None = None
    default_price: str | None = None
    currency: str | None = None
    facilitator_url: str | None = None


class PaymentInfo(BaseModel):
    """Payment information."""

    type: str
    config: PaymentConfigInfo | None = None


class Capability(BaseModel):
    """Agent capability (tool, resource, or prompt)."""

    type: str = Field(..., description="tool, resource, or prompt")
    id: str
    name: str
    description: str

    # Tool-specific
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None

    # Resource-specific
    uri_template: str | None = None
    mime_type: str | None = None

    # Prompt-specific
    arguments: list[dict[str, Any]] | None = None

    # Payment overrides
    payment: dict[str, str] | None = None  # {"price": "10", "asset": "USDC"}

    # A2A per-capability auth
    auth_strategies: list[AuthStrategy] | None = None


class UniversalManifest(BaseModel):
    """
    Universal Agent Manifest.

    This is the normalized format used internally by Metaorcha.
    It combines data from emerge.yaml and harvested capabilities.
    """

    identity: IdentityInfo
    metadata: MetadataInfo
    protocol: ProtocolInfo
    security: SecurityInfo
    payment: PaymentInfo | None = None
    capabilities: list[Capability] = Field(default_factory=list)
