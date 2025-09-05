"""Get/set/delete by parsed key paths."""

from __future__ import annotations

from typing import Any, Tuple

KeyPath = Tuple[str, ...]


def is_int_segment(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_at(obj: Any, key_path: KeyPath, *, missing: object = None) -> Any:
    cur = obj
    for seg in key_path:
        if isinstance(cur, dict):
            if seg in cur:
                cur = cur[seg]
            else:
                return missing
        elif isinstance(cur, list):
            if is_int_segment(seg):
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
        return [] if is_int_segment(next_seg) else {}
    return obj


def set_at(obj: Any, key_path: KeyPath, value: Any) -> Any:
    if not key_path:
        return value
    cur = obj
    if cur is None:
        cur = [] if is_int_segment(key_path[0]) else {}
        obj = cur
    for i, seg in enumerate(key_path):
        is_last = i == len(key_path) - 1
        if isinstance(cur, dict):
            if is_last:
                cur[seg] = value
            else:
                nxt = cur.get(seg)
                nxt = _ensure_container(nxt, key_path[i + 1])
                cur[seg] = nxt
                cur = nxt
        elif isinstance(cur, list):
            if not is_int_segment(seg):
                raise TypeError("List index segment expected")
            idx = int(seg)
            while len(cur) <= idx:
                cur.append(None)
            if is_last:
                cur[idx] = value
            else:
                nxt = cur[idx]
                nxt = _ensure_container(nxt, key_path[i + 1])
                cur[idx] = nxt
                cur = nxt
        else:
            raise TypeError("Cannot descend into scalar")
    return obj


def delete_at(obj: Any, key_path: KeyPath) -> Any:
    if not key_path:
        return None
    cur = obj
    parents: list[tuple[Any, str]] = []
    for seg in key_path:
        parents.append((cur, seg))
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        elif isinstance(cur, list) and is_int_segment(seg):
            idx = int(seg)
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return obj
        else:
            return obj
    parent, last = parents[-1]
    if isinstance(parent, dict):
        parent.pop(last, None)
    elif isinstance(parent, list) and is_int_segment(last):
        idx = int(last)
        if 0 <= idx < len(parent):
            parent[idx] = None
    return obj
