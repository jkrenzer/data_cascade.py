
"""File IO utilities that delegate to registered format handlers."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from .logging_utils import get_logger
from .registry import get_handler_for, known_extensions

logger = get_logger("io")

def load_file(path: Path) -> Any:
    handler = get_handler_for(path)
    if handler is None:
        logger.warning("No handler for extension %s. Known: %s", path.suffix.lower(), list(known_extensions()))
        raise ValueError(f"Unsupported file extension: {path.suffix} for {path}")
    logger.debug("Loading file: %s with handler: %r", path, handler)
    return handler.load(path)

def save_file(path: Path, data: Any) -> None:
    handler = get_handler_for(path)
    if handler is None:
        logger.warning("No handler for extension %s. Known: %s", path.suffix.lower(), list(known_extensions()))
        raise ValueError(f"Unsupported file extension for saving: {path.suffix} for {path}")
    logger.debug("Saving file: %s with handler: %r", path, handler)
    handler.save(path, data)
