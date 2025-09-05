"""Origin mapping structures to enable saving back to files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

KeyPath = Tuple[str, ...]
LocalPath = Tuple[str, ...]


@dataclass(frozen=True)
class KeyOrigin:
    file: Path
    local_path: LocalPath


@dataclass
class CascadeMap:
    forward: Dict[Path, set[KeyPath]] = field(default_factory=dict)
    reverse: Dict[KeyPath, List[KeyOrigin]] = field(default_factory=dict)

    def add_origin(self, key_path: KeyPath, origin: KeyOrigin) -> None:
        self.reverse.setdefault(key_path, []).append(origin)
        self.forward.setdefault(origin.file, set()).add(key_path)

    def drop_prefix(self, prefix: KeyPath) -> None:
        to_drop = [
            kp for kp in list(self.reverse.keys()) if kp[: len(prefix)] == prefix
        ]
        for kp in to_drop:
            origins = self.reverse.pop(kp, [])
            for o in origins:
                if o.file in self.forward and kp in self.forward[o.file]:
                    self.forward[o.file].remove(kp)
                    if not self.forward[o.file]:
                        del self.forward[o.file]


def merge_maps(a: CascadeMap, b: CascadeMap, *, prefix: KeyPath = ()) -> CascadeMap:
    out = CascadeMap(
        forward={p: set(kps) for p, kps in a.forward.items()},
        reverse={kp: list(origins) for kp, origins in a.reverse.items()},
    )
    for kp, origins in b.reverse.items():
        kp2 = prefix + kp
        for o in origins:
            out.add_origin(kp2, o)
    return out


def enumerate_paths(obj: Any, base: KeyPath = ()) -> Iterable[KeyPath]:
    if isinstance(obj, dict):
        yield base
        for k, v in obj.items():
            if not isinstance(k, str):
                k = str(k)
            yield from enumerate_paths(v, base + (k,))
    elif isinstance(obj, list):
        yield base
        for idx, v in enumerate(obj):
            yield from enumerate_paths(v, base + (str(idx),))
    else:
        yield base
