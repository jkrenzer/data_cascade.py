"""Saving a cascade back to files using a CascadeMap."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .handlers.registry import get_handler_for, known_extensions
from .io import save_file
from .logging_utils import get_logger
from .mapping import CascadeMap, KeyOrigin, KeyPath

log = get_logger(__name__)


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def _get_at(data: Any, key_path: KeyPath, *, missing: object) -> Any:
    cur = data
    for seg in key_path:
        if isinstance(cur, dict):
            if seg in cur:
                cur = cur[seg]
            else:
                return missing
        elif isinstance(cur, list):
            if _is_int(seg):
                idx = int(seg)
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return missing
            else:
                return missing
        else:
            return missing
    return cur


def _ensure_container(obj: Any, next_seg: str) -> Any:
    if obj is None:
        return [] if _is_int(next_seg) else {}
    return obj


def _set_at_local(root: Any, local_path: KeyPath, value: Any) -> Any:
    if not local_path:
        return value
    cur = root
    for i, seg in enumerate(local_path):
        is_last = i == len(local_path) - 1
        if isinstance(cur, dict):
            if is_last:
                cur[seg] = value
            else:
                nxt = cur.get(seg)
                nxt = _ensure_container(nxt, local_path[i + 1])
                cur[seg] = nxt
                cur = nxt
        elif isinstance(cur, list):
            if not _is_int(seg):
                raise TypeError("List index segment expected")
            idx = int(seg)
            while len(cur) <= idx:
                cur.append(None)
            if is_last:
                cur[idx] = value
            else:
                nxt = cur[idx]
                nxt = _ensure_container(nxt, local_path[i + 1])
                cur[idx] = nxt
                cur = nxt
        else:
            if i == 0:
                cur = [] if _is_int(seg) else {}
                root = cur
                return _set_at_local(root, local_path, value)
            raise TypeError("Cannot descend into scalar")
    return root


def _choose_origin_for_key(file: Path, origins: List[KeyOrigin]) -> KeyOrigin:
    for o in origins:
        if o.file == file:
            return o
    return origins[0]


def _reconstruct_file_object(file: Path, data: Dict[str, Any], cmap: CascadeMap) -> Any:
    root_obj: Any = None
    key_paths = sorted(list(cmap.forward.get(file, set())), key=lambda kp: len(kp))
    for kp in key_paths:
        origins = cmap.reverse.get(kp, [])
        if not origins:
            continue
        o = _choose_origin_for_key(file, origins)
        local = o.local_path
        sentinel = object()
        val = _get_at(data, kp, missing=sentinel)
        if val is sentinel:
            continue
        if local == tuple():
            root_obj = val
            continue
        if root_obj is None:
            root_obj = [] if (local and _is_int(local[0])) else {}
        root_obj = _set_at_local(root_obj, local, val)
    if root_obj is None:
        root_obj = {}
    return root_obj


def _pick_default_write_path(root: Path) -> Path:
    for ext in (".yaml", ".yml", ".json", ".toml"):
        p = root / f"__main__{ext}"
        if get_handler_for(p) is not None:
            return p
    known = list(known_extensions())
    ext = known[0] if known else ".json"
    return root / f"__main__{ext}"


def _assign_new_keys_to_files(
    root: Path, data: Dict[str, Any], cmap: CascadeMap
) -> Dict[Path, List[Tuple[KeyPath, KeyPath]]]:
    assignments: Dict[Path, List[Tuple[KeyPath, KeyPath]]] = {}

    def walk(obj: Any, base: KeyPath = ()) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and k.startswith("__") and k.endswith("__"):
                    continue
                walk(v, base + (str(k),))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, base + (str(i),))
        else:
            kp = base
            if kp in cmap.reverse:
                return
            prefix = kp
            while prefix and prefix not in cmap.reverse:
                prefix = prefix[:-1]
            if prefix in cmap.reverse:
                origin = cmap.reverse[prefix][0]
                file = origin.file
                local = origin.local_path + kp[len(prefix) :]
            else:
                default = _pick_default_write_path(root)
                file = default
                local = kp
            assignments.setdefault(file, []).append((kp, local))

    walk(data, ())
    return assignments


def save_data_cascade(
    root: Path | str,
    data: Dict[str, Any],
    cmap: CascadeMap,
    *,
    target_files: Optional[Iterable[Path]] = None,
) -> None:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)

    files = list(cmap.forward.keys())
    new_assignments = _assign_new_keys_to_files(root_path, data, cmap)
    files = set(files) | set(new_assignments.keys())

    if target_files is not None:
        files = set(files) & set(target_files)
        # include any assignment files not already present
        files = files | (set(new_assignments.keys()) & set(target_files))

    for file in sorted(files):
        try:
            obj = _reconstruct_file_object(file, data, cmap)
            for kp, local in new_assignments.get(file, []):
                sentinel = object()
                val = _get_at(data, kp, missing=sentinel)
                if val is sentinel:
                    continue
                if obj is None:
                    obj = [] if (local and _is_int(local[0])) else {}
                obj = _set_at_local(obj, local, val)
            file.parent.mkdir(parents=True, exist_ok=True)
            save_file(file, obj)
            log.info("Saved %s", file)
        except Exception as e:
            log.error("Failed to save %s: %s", file, e)
            raise


__all__ = ["save_data_cascade"]
