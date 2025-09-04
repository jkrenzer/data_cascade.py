
"""Merge strategies and primitives."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, MutableMapping, Optional

class DictMode(str, Enum):
    DEEP = "deep"
    OVERRIDE = "override"
    FIRST_WINS = "first_wins"

class ListMode(str, Enum):
    REPLACE = "replace"
    EXTEND = "extend"
    UNIQUE = "unique"
    MERGE_BY_KEY = "merge_by_key"

@dataclass
class ListStrategy:
    mode: ListMode = ListMode.REPLACE
    key: Optional[str] = None

@dataclass
class MergeStrategy:
    dict_mode: DictMode = DictMode.DEEP
    list_strategy: ListStrategy = field(default_factory=ListStrategy)
    per_key: Dict[str, "MergeStrategy"] = field(default_factory=dict)
    excludes: set[str] = field(default_factory=set)

    def for_child(self, key: str) -> "MergeStrategy":
        return self.per_key.get(key, self)

    @staticmethod
    def from_config(config: Mapping[str, Any], parent: Optional["MergeStrategy"] = None) -> "MergeStrategy":
        base = MergeStrategy() if parent is None else MergeStrategy(
            dict_mode=parent.dict_mode,
            list_strategy=ListStrategy(parent.list_strategy.mode, parent.list_strategy.key),
            per_key=dict(parent.per_key),
            excludes=set(parent.excludes),
        )
        dict_val = config.get("dict")
        if isinstance(dict_val, str):
            try:
                base.dict_mode = DictMode(dict_val)
            except ValueError:
                pass
        list_cfg = config.get("list")
        if isinstance(list_cfg, Mapping):
            mode_val = list_cfg.get("mode")
            key_val = list_cfg.get("key")
            if isinstance(mode_val, str):
                try:
                    base.list_strategy.mode = ListMode(mode_val)
                except ValueError:
                    pass
            if isinstance(key_val, str) or key_val is None:
                base.list_strategy.key = key_val
        per_key_cfg = config.get("per_key")
        if isinstance(per_key_cfg, Mapping):
            for child_key, child_cfg in per_key_cfg.items():
                if isinstance(child_cfg, Mapping):
                    base.per_key[child_key] = MergeStrategy.from_config(child_cfg, parent=base)
        exclude_val = config.get("exclude")
        if isinstance(exclude_val, list):
            for name in exclude_val:
                if isinstance(name, str) and name:
                    base.excludes.add(name)
        return base

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
                    merged = dict(idx[kval]); merged.update(it); idx[kval] = merged
                else:
                    idx[kval] = dict(it); order.append(kval)
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

def deep_merge_dicts(a: Dict[str, Any], b: Mapping[str, Any], strategy: MergeStrategy) -> Dict[str, Any]:
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
