# Tests for list merge strategies controlled by a __config__ file.
from __future__ import annotations

from pathlib import Path

from data_cascade import load_data_cascade


def _write_yaml(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def test_list_merge_extend(tmp_path: Path):
    # Base list + overlay list should be extended when config requests extend.
    root = tmp_path / "data"
    root.mkdir()
    _write_yaml(root / "__main__.yaml", "layer:\n  items:\n    - 1\n    - 2\n")
    _write_yaml(root / "layer.yaml", "items:\n  - 3\n")
    # Place merge config under __config__ to control list merging.
    _write_yaml(
        root / "__config__.yaml",
        "data:\n  merge:\n    list:\n      mode: extend\n",
    )

    data, _ = load_data_cascade(root)
    assert data["layer"]["items"] == [1, 2, 3]


def test_list_merge_replace(tmp_path: Path):
    # When list merge strategy is replace, overlay list should replace base.
    root = tmp_path / "data"
    root.mkdir()
    _write_yaml(root / "__main__.yaml", "layer:\n  items:\n    - 1\n    - 2\n")
    _write_yaml(root / "layer.yaml", "items:\n  - 3\n")
    _write_yaml(
        root / "__config__.yaml",
        "data:\n  merge:\n    list:\n      mode: replace\n",
    )

    data, _ = load_data_cascade(root)
    assert data["layer"]["items"] == [3]
