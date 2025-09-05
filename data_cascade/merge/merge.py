"""Merge strategies and primitives."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping

from data_cascade.merge.strategy import (DictMode, ListMode, ListStrategy,
                                         MergeStrategy)


def merge_lists(a: list[Any], b: list[Any], strategy: ListStrategy) -> list[Any]:
    mode = strategy.mode
    if mode == ListMode.REPLACE:
        return list(b)
    if mode == ListMode.EXTEND:
        return list(a) + list(b)
    if mode == ListMode.UNIQUE:
        out: list[Any] = []
        for item in list(a) + list(b):
            if item not in out:
                out.append(item)
        return out
    if mode == ListMode.MERGE_BY_KEY:
        key = strategy.key
        if not key:
            return list(b)
        idx: dict[Any, dict[str, Any]] = {}
        order: list[Any] = []
        tail: list[Any] = []
        for it in a:
            if isinstance(it, Mapping) and key in it:
                kval = it[key]
                idx[kval] = dict(it)
                order.append(kval)
            else:
                tail.append(it)
        for it in b:
            if isinstance(it, Mapping) and key in it:
                kval = it[key]
                if kval in idx:
                    merged = dict(idx[kval])
                    merged.update(it)
                    idx[kval] = merged
                else:
                    idx[kval] = dict(it)
                    order.append(kval)
            else:
                tail.append(it)
        out = [idx[k] for k in order if k in idx]
        out.extend(tail)
        return out
    return list(b)


def merge_values(a: Any, b: Any, strategy: MergeStrategy) -> Any:
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        if strategy.dict_mode == DictMode.FIRST_WINS:
            return dict(a)
        if strategy.dict_mode == DictMode.OVERRIDE:
            return dict(b)
        return deep_merge_dicts(dict(a), dict(b), strategy)
    if isinstance(a, list) and isinstance(b, list):
        return merge_lists(a, b, strategy.list_strategy)
    if strategy.dict_mode == DictMode.FIRST_WINS:
        return a
    return b


def deep_merge_dicts(
    a: Dict[str, Any], b: Mapping[str, Any], strategy: MergeStrategy
) -> Dict[str, Any]:
    out = dict(a)
    for k, b_val in b.items():
        if k in strategy.excludes:
            continue
        if k in out:
            child_strategy = strategy.for_child(k)
            out[k] = merge_values(out[k], b_val, child_strategy)
        else:
            out[k] = b_val
    return out


def strip_magic_keys(d: MutableMapping[str, Any]) -> None:
    to_delete: list[str] = []
    for k, v in d.items():
        if isinstance(v, dict):
            strip_magic_keys(v)
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    strip_magic_keys(it)
        if k.startswith("__") and k.endswith("__"):
            to_delete.append(k)
    for k in to_delete:
        del d[k]
