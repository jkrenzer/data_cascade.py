"""TOML handler using tomllib (3.11+) or tomli; save using tomli_w or toml if available."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ..logging_utils import get_logger
from .registry import FileHandler, register_handler

log = get_logger(__name__)

_TOML_LOAD_BACKEND = None
_TOML_SAVE_BACKEND = None

try:
    import tomllib  # type: ignore[attr-defined]

    _TOML_LOAD_BACKEND = "tomllib"
except Exception:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore

        _TOML_LOAD_BACKEND = "tomli"
    except Exception:
        _TOML_LOAD_BACKEND = None

try:
    import tomli_w  # type: ignore

    _TOML_SAVE_BACKEND = "tomli_w"
except Exception:  # pragma: no cover
    try:
        import toml  # type: ignore

        _TOML_SAVE_BACKEND = "toml"
    except Exception:
        _TOML_SAVE_BACKEND = None


class TomlHandler(FileHandler):
    """Handler for TOML files."""

    def supported_exts(self) -> Sequence[str]:
        return (".toml",)

    def can_handle(self, path: Path) -> bool:
        return (
            _TOML_LOAD_BACKEND is not None
            and path.suffix.lower() in self.supported_exts()
        )

    def load(self, path: Path) -> Any:
        if _TOML_LOAD_BACKEND is None:
            raise RuntimeError(
                "No TOML backend available. Install tomli or use Python 3.11+."
            )
        with path.open("rb") as f:
            return tomllib.load(f)  # type: ignore[name-defined]

    def save(self, path: Path, data: Any) -> None:
        if _TOML_SAVE_BACKEND is None:
            raise RuntimeError("No TOML writer available. Install tomli-w or toml.")
        if _TOML_SAVE_BACKEND == "tomli_w":
            from tomli_w import dump as tomli_dump  # type: ignore

            with path.open("wb") as f:
                tomli_dump(data, f)
        else:
            import toml  # type: ignore

            with path.open("w", encoding="utf-8") as f:
                toml.dump(data, f)  # type: ignore


if _TOML_LOAD_BACKEND is not None:
    register_handler(TomlHandler())
    log.debug(
        "Using TOML backends: load=%s save=%s",
        _TOML_LOAD_BACKEND,
        _TOML_SAVE_BACKEND or "NONE",
    )
else:
    log.warning("TOML files will not be loaded because no TOML library is available.")
