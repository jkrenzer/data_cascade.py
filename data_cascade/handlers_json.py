
"""JSON handler using the Python standard library."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Sequence
from .logging_utils import get_logger
from .registry import FileHandler, register_handler

logger = get_logger("json")

class JsonHandler(FileHandler):
    def supported_exts(self) -> Sequence[str]:
        return (".json",)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_exts()

    def load(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, path: Path, data: Any) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

register_handler(JsonHandler())
logger.debug("Registered JSON handler.")
