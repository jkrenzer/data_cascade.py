
"""Package-wide constants and helpers."""
from __future__ import annotations
from pathlib import Path
from typing import Final, Tuple

SUPPORTED_EXTS_DEFAULT: Final[tuple[str, ...]] = (".yaml", ".yml", ".json", ".toml")
MAIN_STEM: Final[str] = "__main__"
CONFIG_STEM: Final[str] = "__config__"
MAGIC_PREFIX: Final[str] = "__"
MAGIC_SUFFIX: Final[str] = "__"

def is_magic_name(name: str) -> bool:
    return name.startswith(MAGIC_PREFIX) and name.endswith(MAGIC_SUFFIX)

def ensure_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
