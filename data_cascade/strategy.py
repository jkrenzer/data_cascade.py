
"""Strategy extraction."""

from __future__ import annotations
from typing import Any, Mapping
from .merge import MergeStrategy

def extract_strategy_from_node(node: Mapping[str, Any], inherited: MergeStrategy) -> MergeStrategy:
    cfg = node.get("__config__")
    if not isinstance(cfg, Mapping):
        return inherited
    data_cfg = cfg.get("data")
    if not isinstance(data_cfg, Mapping):
        return inherited
    merge_cfg = data_cfg.get("merge")
    if not isinstance(merge_cfg, Mapping):
        return inherited
    return MergeStrategy.from_config(merge_cfg, parent=inherited)

__all__ = ["extract_strategy_from_node"]
