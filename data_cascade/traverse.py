"""Directory traversal and cascade assembly with origin mapping."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from .config import CONFIG_STEM, MAIN_STEM, SUPPORTED_EXTS_DEFAULT
from .fs import list_dirs, list_files
from .io import load_file
from .logging_utils import get_logger
from .mapping import CascadeMap, KeyOrigin, KeyPath, enumerate_paths, merge_maps
from .merge.merge import deep_merge_dicts, merge_lists
from .merge.strategy import MergeStrategy, extract_strategy_from_node

log = get_logger(__name__)


def _assign_origins_for_subtree(
    base_path: KeyPath, content: Any, file_path: Path, cmap: CascadeMap
) -> None:
    for rel_path in enumerate_paths(content):
        full: KeyPath = tuple(list(base_path) + list(rel_path))
        cmap.add_origin(full, KeyOrigin(file=file_path, local_path=rel_path))


def load_directory_node(
    directory: Path,
    inherited_strategy: Optional[MergeStrategy] = None,
    inherited_default_config: Optional[Mapping[str, Any]] = None,
    allowed_exts: tuple[str, ...] = SUPPORTED_EXTS_DEFAULT,
) -> Tuple[Dict[str, Any], CascadeMap]:
    strategy = inherited_strategy or MergeStrategy()
    node: Dict[str, Any] = {}
    cmap = CascadeMap()

    dir_default_config: Optional[Mapping[str, Any]] = inherited_default_config
    listed_files = list(list_files(directory, allowed_exts))
    files_to_process = list()
    for file_path in listed_files:
        if file_path.stem == CONFIG_STEM:
            try:
                cfg_content = load_file(file_path) or {}
            except Exception as e:
                log.error("Failed to load config file %s: %s", file_path, e)
                continue
            if isinstance(cfg_content, Mapping):
                if dir_default_config and isinstance(dir_default_config, Mapping):
                    log.info("Merging directory default config from %s", file_path)
                    merged_cfg = dict(dir_default_config)
                    merged_cfg.update(cfg_content)
                    dir_default_config = merged_cfg
                else:
                    log.info("Setting directory default config from %s", file_path)
                    dir_default_config = dict(cfg_content)
            else:
                log.warning(
                    "Config file %s does not contain a mapping; ignoring", file_path
                )
        elif file_path.stem == MAIN_STEM:
            files_to_process.insert(0, file_path)
        else:
            files_to_process.append(file_path)

    if isinstance(dir_default_config, Mapping):
        strategy = extract_strategy_from_node(
            {"__config__": dir_default_config}, strategy
        )

    for file_path in files_to_process:
        log.debug("Processing file %s", file_path)
        stem = file_path.stem
        if stem == CONFIG_STEM:
            continue
        if stem in strategy.excludes:
            log.debug("Excluding stem %s due to strategy excludes", stem)
            continue
        try:
            content = load_file(file_path)
        except Exception as e:
            log.warning("Skipping file %s due to load error: %s", file_path, e)
            continue
        if content is None:
            content = {}
        if (
            isinstance(content, Mapping)
            and dir_default_config
            and "__config__" not in content
        ):
            tmp = dict(content)
            tmp["__config__"] = dict(dir_default_config)
            content = tmp
        if stem == MAIN_STEM:
            if not isinstance(content, Mapping):
                raise RuntimeError(
                    f"{file_path} must contain a mapping for {MAIN_STEM}"
                )
            node = deep_merge_dicts(node, content, strategy)
            _assign_origins_for_subtree((), content, file_path, cmap)
            continue
        if stem in node:
            if isinstance(node[stem], dict) and isinstance(content, dict):
                log.debug("Merging dict child node for key %s", stem)
                node[stem] = deep_merge_dicts(
                    node[stem], content, strategy.for_child(stem)
                )
            elif isinstance(node[stem], list) and isinstance(content, list):
                log.debug("Merging list child node for key %s", stem)
                node[stem] = merge_lists(
                    node[stem], content, strategy.for_child(stem).list_strategy
                )
            else:
                log.warning(
                    "Type mismatch when merging key %s from file %s; skipping",
                    stem,
                    file_path,
                )
                node[stem] = content if stem not in node else node[stem]
        else:
            node[stem] = content if stem not in node else node[stem]
        base = (stem,)
        _assign_origins_for_subtree(base, content, file_path, cmap)

    strategy = extract_strategy_from_node(node, strategy)

    for subdir in list_dirs(directory):
        child_key = subdir.name
        if child_key in (CONFIG_STEM, MAIN_STEM):
            log.debug("Skipping directory %s due to reserved name", child_key)
            continue
        if child_key in strategy.excludes:
            log.debug("Excluding directory %s due to strategy excludes", child_key)
            continue
        child_node, child_map = load_directory_node(
            subdir,
            inherited_strategy=strategy.for_child(child_key),
            inherited_default_config=dir_default_config,
            allowed_exts=allowed_exts,
        )
        if child_key in node:
            if isinstance(node[child_key], dict) and isinstance(child_node, dict):
                log.debug("Merging dict child node for key %s", child_key)
                node[child_key] = deep_merge_dicts(
                    node[child_key], child_node, strategy.for_child(child_key)
                )
            if isinstance(node[child_key], list) and isinstance(child_node, list):
                log.debug("Merging list child node for key %s", child_key)
                node[child_key] = merge_lists(
                    node[child_key],
                    child_node,
                    strategy.for_child(child_key).list_strategy,
                )
        else:
            node[child_key] = child_node if child_key not in node else node[child_key]
        cmap = merge_maps(cmap, child_map, prefix=(child_key,))

    for k in list(node.keys()):
        if k in strategy.excludes:
            del node[k]
            cmap.drop_prefix((k,))

    log.debug("Loaded node for %s with keys: %s", directory, list(node.keys()))
    return node, cmap
