"""
core/context.py
Per-request credential context using Python's contextvars.
Thread-safe — concurrent requests never bleed credentials into each other.
"""
from contextvars import ContextVar

# Holds API keys for the current async request context
api_keys: ContextVar[dict] = ContextVar("api_keys", default={})


def get_key(name: str) -> str | None:
    """
    Retrieve an API key for the current request context.
    Falls back to os.environ so local dev (.env) still works.
    """
    import os
    return api_keys.get().get(name) or os.getenv(name)


def set_credentials(creds: dict) -> object:
    """
    Inject credentials into the current request context.
    Returns the token needed to reset the context after the request.

    Usage:
        token = set_credentials({"ANTHROPIC_API_KEY": "...", ...})
        try:
            await do_work()
        finally:
            api_keys.reset(token)
    """
    # Strip None values so get_key falls through to os.environ for missing keys
    clean = {k: v for k, v in creds.items() if v is not None}
    return api_keys.set(clean)

