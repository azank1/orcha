"""Pydantic models for Registry service."""

from .api_responses import (
    DeleteAgentResponse,
    ErrorDetail,
    ErrorResponse,
    HealthCheckResponse,
    ListAgentsResponse,
    RegisterAgentResponse,
    UpdateAgentResponse,
)
from .emerge_config import (
    AuthStrategyConfig,
    EmergeConfig,
    IdentityConfig,
    PaymentConfig,
    ProtocolConfig,
    SecurityConfig,
    TransportConfig,
)
from .universal_manifest import (
    Capability,
    IdentityInfo,
    MetadataInfo,
    PaymentInfo,
    ProtocolInfo,
    SecurityInfo,
    UniversalManifest,
)

__all__ = [
    # emerge.yaml models
    "EmergeConfig",
    "IdentityConfig",
    "ProtocolConfig",
    "TransportConfig",
    "SecurityConfig",
    "AuthStrategyConfig",
    "PaymentConfig",
    # Universal manifest models
    "UniversalManifest",
    "IdentityInfo",
    "MetadataInfo",
    "ProtocolInfo",
    "SecurityInfo",
    "PaymentInfo",
    "Capability",
    # API response models
    "RegisterAgentResponse",
    "ListAgentsResponse",
    "UpdateAgentResponse",
    "DeleteAgentResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    "ErrorDetail",
]
