"""Logging configuration for Metaorcha services."""

import logging
import sys

_APP_ROOT = "metaorcha"


def setup_logging(
    service_name: str,
    level: str = "INFO",
    format_string: str | None = None,
    extra_namespaces: list[str] | None = None,
) -> logging.Logger:
    """
    Set up logging for a service.

    Root logger is set to WARNING so third-party dependencies stay quiet.
    The "metaorcha" namespace and the service-specific namespace are both
    set to the requested level.

    Args:
        service_name: Name of the service (will be used as logger name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Optional custom format string
        extra_namespaces: Additional Python package roots whose loggers should
            also be configured at ``level``.  Use this when module-level loggers
            use ``__name__`` and the resulting names are not children of either
            ``metaorcha`` or ``service_name`` (e.g. a src-layout service whose
            top-level packages are ``api``, ``planning``, ``db``, …).

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Build a single shared handler for all our namespaces.
    # We do NOT use basicConfig because uvicorn configures the root logger before
    # the app is imported, making basicConfig a no-op.  Instead we attach the
    # handler directly to each namespace logger and turn off propagation so
    # records don't double-print through uvicorn's root handler.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_string))
    handler.setLevel(numeric_level)

    def _configure(name: str) -> None:
        lg = logging.getLogger(name)
        lg.setLevel(numeric_level)
        # Add handler only once (guard against repeated calls / reloads)
        if not any(
            isinstance(h, logging.StreamHandler) and h.stream is sys.stdout
            for h in lg.handlers
        ):
            lg.addHandler(handler)
        # Don't bubble up to the root logger — keeps third-party libs quiet
        lg.propagate = False

    _configure(_APP_ROOT)
    if service_name != _APP_ROOT:
        _configure(service_name)

    # Extra package roots (src-layout services with bare top-level packages)
    for ns in extra_namespaces or []:
        _configure(ns)

    return logging.getLogger(service_name)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
