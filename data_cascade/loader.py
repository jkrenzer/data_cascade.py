"""Top-level API to load a data cascade from a root directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .config import SUPPORTED_EXTS_DEFAULT, ensure_dir
# import handlers to register
from .handlers import json  # noqa: F401
from .handlers import toml  # noqa: F401
from .handlers import yaml  # noqa: F401
from .logging_utils import get_logger
from .mapping import CascadeMap
from .traverse import load_directory_node

log = get_logger(__name__)


def load_data_cascade(
    root: Path | str,
    *,
    allowed_exts: tuple[str, ...] = SUPPORTED_EXTS_DEFAULT,
) -> tuple[Dict[str, Any], CascadeMap]:
    root_path = Path(root)
    ensure_dir(root_path)
    log.info("Loading data cascade from %s", root_path)
    data, cmap = load_directory_node(root_path, allowed_exts=allowed_exts)
    log.info("Finished loading cascade from %s", root_path)
    return data, cmap
