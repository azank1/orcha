"""Health check service for agent monitoring."""

import httpx


class HealthCheckService:
    """Service for checking agent health status."""

    def __init__(self, timeout: int = 5):
        """
        Initialize health check service.

        Args:
            timeout: Timeout for health check requests in seconds
        """
        self.timeout = timeout

    async def check_agent_health(self, health_endpoint: str) -> tuple[bool, str]:
        """
        Check if an agent is healthy.

        Args:
            health_endpoint: URL of the agent's health endpoint

        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    health_endpoint, timeout=self.timeout, follow_redirects=True
                )

                # Consider 2xx status codes as healthy
                if 200 <= response.status_code < 300:
                    return True, ""
                return False, f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            return False, "Connection timeout"
        except httpx.ConnectError:
            return False, "Connection failed"
        except httpx.HTTPError as e:
            return False, f"HTTP error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def should_mark_unhealthy(health_failures: int, max_failures: int = 3) -> bool:
        """
        Determine if agent should be marked as unhealthy.

        Args:
            health_failures: Number of consecutive health check failures
            max_failures: Maximum allowed failures before marking unhealthy

        Returns:
            True if should be marked unhealthy
        """
        return health_failures >= max_failures

    @staticmethod
    def get_health_status(
        is_healthy: bool, health_failures: int, max_failures: int = 3
    ) -> str:
        """
        Get health status string based on check result.

        Args:
            is_healthy: Result of health check
            health_failures: Number of consecutive failures
            max_failures: Maximum allowed failures

        Returns:
            Health status: "HEALTHY", "UNHEALTHY", or "UNKNOWN"
        """
        if is_healthy:
            return "HEALTHY"
        if health_failures >= max_failures:
            return "UNHEALTHY"
        return "UNKNOWN"
