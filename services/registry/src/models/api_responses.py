"""API response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class CapabilitiesHarvested(BaseModel):
    """Summary of harvested capabilities."""

    tools: int = 0
    resources: int = 0
    prompts: int = 0


class RegisterAgentData(BaseModel):
    """Successful registration response data."""

    agent_id: str
    name: str
    version: str
    registered_at: datetime
    health_status: str
    capabilities_harvested: CapabilitiesHarvested


class RegisterAgentResponse(BaseModel):
    """Response for agent registration."""

    status: str = "success"
    data: RegisterAgentData | None = None
    error: ErrorDetail | None = None


class AgentListItem(BaseModel):
    """Agent list item."""

    id: str
    name: str
    version: str
    health_status: str
    protocol_type: str
    indexed_at: datetime
    execution_count: int = 0
    success_rate: float = 0.70


class PaginationInfo(BaseModel):
    """Pagination metadata."""

    page: int
    limit: int
    total: int
    total_pages: int


class ListAgentsData(BaseModel):
    """List agents response data."""

    agents: list[AgentListItem]
    pagination: PaginationInfo


class ListAgentsResponse(BaseModel):
    """Response for listing agents."""

    status: str = "success"
    data: ListAgentsData | None = None
    error: ErrorDetail | None = None


class UpdateAgentData(BaseModel):
    """Update agent response data."""

    agent_id: str
    version: str
    updated_at: datetime
    version_created: bool


class UpdateAgentResponse(BaseModel):
    """Response for updating agent."""

    status: str = "success"
    data: UpdateAgentData | None = None
    error: ErrorDetail | None = None


class DeleteAgentResponse(BaseModel):
    """Response for deleting agent."""

    status: str = "success"
    message: str = "Agent deleted successfully"
    error: ErrorDetail | None = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    timestamp: datetime
    database: str = "connected"
    version: str


class ErrorResponse(BaseModel):
    """Generic error response."""

    status: str = "error"
    error: ErrorDetail
