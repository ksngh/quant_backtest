"""Minimal runtime error logging helpers for CLI entrypoints."""

from __future__ import annotations

import logging


def configure_runtime_logging() -> None:
    """Initialize process logging when no handlers are configured yet."""

    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def log_runtime_exception(component: str) -> None:
    """Emit an exception log entry with stack trace for runtime failures."""

    configure_runtime_logging()
    logging.getLogger(component).exception("runtime failure in %s", component)
