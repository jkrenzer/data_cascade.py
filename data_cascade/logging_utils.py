"""Logging helpers for consistent logger creation."""

from __future__ import annotations

import logging

LOGGER_NAME = "data_cascade"


def get_logger(*args, **kwargs) -> logging.Logger:
    logger = logging.getLogger(*args, **kwargs)
    return logger
