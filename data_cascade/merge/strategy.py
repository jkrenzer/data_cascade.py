from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional

from data_cascade.logging_utils import get_logger

log = get_logger(__name__)


class ListMode(str, Enum):
    REPLACE = "replace"
    EXTEND = "extend"
    UNIQUE = "unique"
    MERGE_BY_KEY = "merge_by_key"


@dataclass
class ListStrategy:
    mode: ListMode = ListMode.REPLACE
    key: Optional[str] = None


class DictMode(str, Enum):
    DEEP = "deep"
    OVERRIDE = "override"
    FIRST_WINS = "first_wins"


@dataclass
class MergeStrategy:
    dict_mode: DictMode = DictMode.DEEP
    list_strategy: ListStrategy = field(default_factory=ListStrategy)
    per_key: Dict[str, "MergeStrategy"] = field(default_factory=dict)
    excludes: set[str] = field(default_factory=set)

    def for_child(self, key: str) -> "MergeStrategy":
        return self.per_key.get(key, self)

    @staticmethod
    def from_config(
        config: Mapping[str, Any], parent: Optional["MergeStrategy"] = None
    ) -> "MergeStrategy":
        base = (
            MergeStrategy()
            if parent is None
            else MergeStrategy(
                dict_mode=parent.dict_mode,
                list_strategy=ListStrategy(
                    parent.list_strategy.mode, parent.list_strategy.key
                ),
                per_key=dict(parent.per_key),
                excludes=set(parent.excludes),
            )
        )
        dict_val = config.get("dict")
        if isinstance(dict_val, Mapping):
            mode_val = dict_val.get("mode")
            if isinstance(mode_val, str):
                try:
                    base.dict_mode = DictMode(mode_val)
                except ValueError:
                    log.warning("Invalid dict mode in config: %s", mode_val)
        list_cfg = config.get("list")
        if isinstance(list_cfg, Mapping):
            mode_val = list_cfg.get("mode")
            key_val = list_cfg.get("key")
            if isinstance(mode_val, str):
                try:
                    base.list_strategy.mode = ListMode(mode_val)
                except ValueError:
                    log.warning("Invalid list mode in config: %s", mode_val)
            if isinstance(key_val, str) or key_val is None:
                base.list_strategy.key = key_val
        per_key_cfg = config.get("per_key")
        if isinstance(per_key_cfg, Mapping):
            for child_key, child_cfg in per_key_cfg.items():
                if isinstance(child_cfg, Mapping):
                    base.per_key[child_key] = MergeStrategy.from_config(
                        child_cfg, parent=base
                    )
        exclude_val = config.get("exclude")
        if isinstance(exclude_val, list):
            for name in exclude_val:
                if isinstance(name, str) and name:
                    base.excludes.add(name)
        log.debug("Constructed MergeStrategy from config: %s", repr(base))
        return base


def extract_strategy_from_node(
    node: Mapping[str, Any], inherited: MergeStrategy
) -> MergeStrategy:
    cfg = node.get("__config__")
    if not isinstance(cfg, Mapping):
        log.debug("No __config__ mapping found; using inherited strategy")
        return inherited
    if cfg.get("__config__") is not None:
        log.info("Ignoring nested __config__ in __config__ mapping")
        cfg = cfg.get("__config__")
    data_cfg = cfg.get("data")
    if not isinstance(data_cfg, Mapping):
        log.debug(
            "No data mapping found in __config__; using inherited strategy. __config__: %s",
            cfg,
        )
        return inherited
    merge_cfg = data_cfg.get("merge")
    if not isinstance(merge_cfg, Mapping):
        log.debug(
            "No merge mapping found in data config; using inherited strategy. data config: %s",
            data_cfg,
        )
        return inherited
    log.debug("Setting merge strategy from config: %s", merge_cfg)
    return MergeStrategy.from_config(merge_cfg, parent=inherited)
