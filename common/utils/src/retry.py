"""Retry utilities with exponential backoff."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


async def retry_with_backoff(  # noqa: UP047
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> T:
    """
    Retry an async function with exponential backoff.

    Args:
        func: The async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be exponentially increased)
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt == max_retries - 1:
                raise

            # Exponential backoff: 1s, 2s, 4s, 8s, etc.
            delay = min(base_delay * (2**attempt), max_delay)
            await asyncio.sleep(delay)

    # Should never reach here, but for type safety
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed without exception")


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry

    Example:
        @async_retry(max_retries=3, base_delay=1.0)
        async def fetch_data():
            # Your async function here
            pass
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exceptions=exceptions,
            )

        return wrapper

    return decorator
