"""Error hierarchy for the Planning & Discovery Service."""


class PlanningError(Exception):
    """Base exception for all planning errors."""


class UserError(PlanningError):
    """Recoverable errors caused by user input (4xx-equivalent)."""


class InternalError(PlanningError):
    """Retriable system errors (5xx-equivalent)."""


class FatalError(PlanningError):
    """Non-recoverable errors that require operator intervention."""


# ── Concrete error types ──────────────────────────────────────────────────────


class AmbiguousQueryError(UserError):
    """Query is too ambiguous to decompose into a concrete workflow."""


class NoAgentsFoundError(UserError):
    """No agents match the capability requirements of a task."""


class AgentUnavailableError(InternalError):
    """Agent exists in the registry but is currently unhealthy."""


class LLMTimeoutError(InternalError):
    """LLM request timed out."""


class ValidationFailedError(FatalError):
    """Workflow plan failed all validation tiers and cannot be recovered."""
