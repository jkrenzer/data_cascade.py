
"""Registry for file format handlers."""

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Optional, Protocol, Sequence, Dict, Iterable
from .logging_utils import get_logger

logger = get_logger("registry")

class FileHandler(Protocol):
    def supported_exts(self) -> Sequence[str]: ...
    def can_handle(self, path: Path) -> bool: ...
    def load(self, path: Path) -> Any: ...
    def save(self, path: Path, data: Any) -> None: ...

_HANDLERS: List[FileHandler] = []
_EXT_TO_HANDLER: Dict[str, FileHandler] = {}

def register_handler(handler: FileHandler) -> None:
    for ext in handler.supported_exts():
        ext_low = ext.lower()
        if ext_low in _EXT_TO_HANDLER:
            logger.debug("Overriding handler for extension %s with %r", ext_low, handler)
        _EXT_TO_HANDLER[ext_low] = handler
    _HANDLERS.append(handler)
    logger.debug("Registered handler %r for %r", handler, list(handler.supported_exts()))

def get_handler_for(path: Path) -> Optional[FileHandler]:
    ext = path.suffix.lower()
    return _EXT_TO_HANDLER.get(ext)

def known_extensions() -> Iterable[str]:
    return list(_EXT_TO_HANDLER.keys())
