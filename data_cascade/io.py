"""File IO utilities that delegate to registered format handlers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .handlers.registry import get_handler_for, known_extensions
from .logging_utils import get_logger

log = get_logger(__name__)


def load_file(path: Path) -> Any:
    handler = get_handler_for(path)
    if handler is None:
        log.warning(
            "No handler for extension %s. Known: %s",
            path.suffix.lower(),
            list(known_extensions()),
        )
        raise ValueError(f"Unsupported file extension: {path.suffix} for {path}")
    log.debug("Loading file: %s with handler: %r", path, handler)
    return handler.load(path)


def save_file(path: Path, data: Any) -> None:
    handler = get_handler_for(path)
    if handler is None:
        log.warning(
            "No handler for extension %s. Known: %s",
            path.suffix.lower(),
            list(known_extensions()),
        )
        raise ValueError(
            f"Unsupported file extension for saving: {path.suffix} for {path}"
        )
    log.debug("Saving file: %s with handler: %r", path, handler)
    handler.save(path, data)
