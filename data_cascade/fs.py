"""Filesystem helpers using pathlib."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .logging_utils import get_logger

log = get_logger(__name__)


def list_files(directory: Path, allowed_exts: tuple[str, ...]) -> Iterable[Path]:
    files = sorted(
        (
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in allowed_exts
        ),
        key=lambda p: p.name,
    )
    log.debug("Found %d files in %s", len(files), directory)
    return files


def list_dirs(directory: Path) -> Iterable[Path]:
    dirs = sorted((p for p in directory.iterdir() if p.is_dir()), key=lambda p: p.name)
    log.debug("Found %d subdirectories in %s", len(dirs), directory)
    return dirs
