"""InputGuard — validates tool call arguments against JSON Schema."""

from __future__ import annotations

import logging
from typing import Any

import jsonschema

logger = logging.getLogger(__name__)

# Default pagination injected when a schema declares these fields
_PAGINATION_DEFAULTS = {"page": 1, "page_size": 20, "max_results": 100}


class InputGuardError(ValueError):
    """Raised when input validation fails."""


class InputGuard:
    """Validates and normalises tool call arguments."""

    @staticmethod
    def validate(
        args: dict[str, Any],
        schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Validate ``args`` against ``schema`` and inject pagination defaults.

        Returns the (possibly mutated) args dict.
        Raises InputGuardError on validation failure.
        """
        if not schema:
            return args

        # Inject pagination defaults before validation so they satisfy 'required'
        properties = schema.get("properties", {})
        for key, default in _PAGINATION_DEFAULTS.items():
            if key in properties and key not in args:
                args[key] = default

        try:
            jsonschema.validate(instance=args, schema=schema)
        except jsonschema.ValidationError as exc:
            raise InputGuardError(
                f"Input validation failed: {exc.message} (path: {list(exc.path)})"
            ) from exc

        return args
