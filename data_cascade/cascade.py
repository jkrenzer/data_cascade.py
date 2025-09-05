"""Interactive Cascade object with path and proxy APIs and dirty saves."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Set

from .loader import load_data_cascade
from .logging_utils import get_logger
from .mapping import CascadeMap, KeyPath
from .pathops import get_at as _get_at
from .pathops import parse_path
from .pathops import set_at as _set_at
from .saver import _pick_default_write_path  # reuse internal
from .saver import save_data_cascade

log = get_logger(__name__)


class CascadeNode:
    def __init__(self, cascade: "Cascade", key_path: KeyPath):
        self._c = cascade
        self._p = key_path

    def __getattr__(self, name: str) -> "CascadeNode":
        if name.startswith("_"):
            raise AttributeError(name)
        return CascadeNode(self._c, self._p + (name,))

    def __getitem__(self, key: object) -> "CascadeNode":
        return CascadeNode(self._c, self._p + (str(key),))

    def get(self) -> Any:
        return self._c.get(self._p)

    def set(self, value: Any) -> None:
        self._c.set(self._p, value)

    def delete(self) -> None:
        self._c.delete(self._p)

    def __repr__(self) -> str:
        return f"CascadeNode(path={self._p!r})"


class Cascade:
    def __init__(self, root: Path, data: dict, cmap: CascadeMap):
        self.root = Path(root)
        self.data = data
        self.cmap = cmap
        self._dirty_files: Set[Path] = set()

    def get(self, path: str | KeyPath) -> Any:
        kp: KeyPath = parse_path(path) if isinstance(path, str) else path
        return _get_at(self.data, kp, missing=None)

    def set(self, path: str | KeyPath, value: Any) -> None:
        kp: KeyPath = parse_path(path) if isinstance(path, str) else path
        self.data = _set_at(self.data, kp, value)
        # mark files dirty: all origins for this key path
        if kp in self.cmap.reverse:
            for o in self.cmap.reverse[kp]:
                self._dirty_files.add(o.file)
        else:
            # choose the file based on nearest ancestor or default
            prefix = kp
            while prefix and prefix not in self.cmap.reverse:
                prefix = prefix[:-1]
            if prefix in self.cmap.reverse:
                file = self.cmap.reverse[prefix][0].file
            else:
                file = _pick_default_write_path(self.root)
            self._dirty_files.add(file)

    def delete(self, path: str | KeyPath) -> None:
        kp: KeyPath = parse_path(path) if isinstance(path, str) else path
        # Deletion strategy: set None at the leaf (simple). The saver reconstructs
        # per-file objects by reading the current merged data. If a key is None,
        # that None will be written; to perform a true delete, callers can remove
        # the key at the parent level. For brevity we keep None-write here.
        self.set(kp, None)

    def node(self, path: str | KeyPath = ()) -> CascadeNode:
        kp: KeyPath = (
            parse_path(path) if isinstance(path, str) else (path if path else tuple())
        )
        return CascadeNode(self, kp)

    def save(self) -> None:
        if not self._dirty_files:
            log.info("No dirty files to save.")
            return
        save_data_cascade(
            self.root, self.data, self.cmap, target_files=self._dirty_files
        )
        self._dirty_files.clear()


def make_cascade(root: Path | str) -> Cascade:
    data, cmap = load_data_cascade(root)
    return Cascade(Path(root), data, cmap)
