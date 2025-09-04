
"""Logging helpers for consistent logger creation."""
from __future__ import annotations
import logging
from typing import Optional

LOGGER_NAME = "data_cascade"

def get_logger(name: Optional[str] = None) -> logging.Logger:
    full = LOGGER_NAME if name is None else f"{LOGGER_NAME}.{name}"
    logger = logging.getLogger(full)
    return logger
