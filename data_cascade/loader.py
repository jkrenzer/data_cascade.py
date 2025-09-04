
"""Top-level API to load a data cascade from a root directory."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Tuple
from .config import SUPPORTED_EXTS_DEFAULT, ensure_dir
from .logging_utils import get_logger
from .traverse import load_directory_node
from .mapping import CascadeMap

# import handlers to register
from . import handlers_yaml  # noqa: F401
from . import handlers_json  # noqa: F401
from . import handlers_toml  # noqa: F401

logger = get_logger("loader")

def load_data_cascade(
    root: Path | str,
    *,
    allowed_exts: tuple[str, ...] = SUPPORTED_EXTS_DEFAULT,
) -> tuple[Dict[str, Any], CascadeMap]:
    root_path = Path(root)
    ensure_dir(root_path)
    logger.info("Loading data cascade from %s", root_path)
    data, cmap = load_directory_node(root_path, allowed_exts=allowed_exts)
    logger.info("Finished loading cascade from %s", root_path)
    return data, cmap
