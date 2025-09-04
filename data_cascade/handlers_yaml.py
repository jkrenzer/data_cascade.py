
"""YAML handler with ruamel.yaml preferred and PyYAML fallback."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Sequence
from .logging_utils import get_logger
from .registry import FileHandler, register_handler

logger = get_logger("yaml")

_YAML_BACKEND = None
_YAML_NAME = None
_yaml_loader = None
_yaml_dumper = None

try:
    from ruamel.yaml import YAML  # type: ignore
    _YAML_BACKEND = "ruamel"
    _YAML_NAME = "ruamel.yaml"
    _yaml_loader = YAML(typ="safe")
    _yaml_dumper = YAML()
    _yaml_dumper.default_flow_style = False
    _yaml_dumper.width = 4096
except Exception:  # pragma: no cover
    try:
        import yaml  # type: ignore
        _YAML_BACKEND = "pyyaml"
        _YAML_NAME = "PyYAML"
        _yaml_loader = yaml
        _yaml_dumper = yaml
    except Exception:
        _YAML_BACKEND = None
        _YAML_NAME = None

class YamlHandler(FileHandler):
    def supported_exts(self) -> Sequence[str]:
        return (".yaml", ".yml")

    def can_handle(self, path: Path) -> bool:
        return _YAML_BACKEND is not None and path.suffix.lower() in self.supported_exts()

    def load(self, path: Path) -> Any:
        if _YAML_BACKEND is None:
            raise RuntimeError("No YAML backend available. Install ruamel.yaml or PyYAML.")
        if _YAML_BACKEND == "ruamel":
            with path.open("r", encoding="utf-8") as f:
                return _yaml_loader.load(f)
        with path.open("r", encoding="utf-8") as f:
            return _yaml_loader.safe_load(f)  # type: ignore[attr-defined]

    def save(self, path: Path, data: Any) -> None:
        if _YAML_BACKEND is None:
            raise RuntimeError("No YAML backend available for saving.")
        if _YAML_BACKEND == "ruamel":
            with path.open("w", encoding="utf-8") as f:
                _yaml_dumper.dump(data, f)
            return
        with path.open("w", encoding="utf-8") as f:
            _yaml_dumper.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)  # type: ignore[attr-defined]

if _YAML_BACKEND is not None:
    register_handler(YamlHandler())
    logger.debug("Using YAML backend: %s", _YAML_NAME)
else:
    logger.warning("YAML files will not be loaded because no YAML library is available.")
