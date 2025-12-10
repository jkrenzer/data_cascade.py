# Tests for dict merge strategies controlled by a __config__ file.
from __future__ import annotations

from pathlib import Path

from data_cascade import load_data_cascade


def _write_yaml(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def test_dict_merge_deep(tmp_path: Path):
    # Base dict and overlay dict should be merged when config requests merge.
    root = tmp_path / "data"
    root.mkdir()
    _write_yaml(root / "__main__.yaml", "layer:\n  config:\n    a: 1\n")
    _write_yaml(root / "layer.yaml", "config:\n  b: 2\n")
    _write_yaml(
        root / "__config__.yaml",
        "data:\n  merge:\n    dict:\n      mode: merge\n",
    )

    data, _ = load_data_cascade(root)
    assert data["layer"]["config"]["a"] == 1
    assert data["layer"]["config"]["b"] == 2


def test_dict_merge_replace(tmp_path: Path):
    # When dict merge strategy is replace, overlay dict should replace base dict entirely.
    root = tmp_path / "data"
    root.mkdir()
    _write_yaml(root / "__main__.yaml", "layer:\n  config:\n    a: 1\n")
    _write_yaml(root / "layer.yaml", "config:\n  b: 2\n")
    _write_yaml(
        root / "__config__.yaml",
        "data:\n  merge:\n    dict:\n      mode: override\n",
    )

    data, _ = load_data_cascade(root)
    # Only overlay key should remain after replace
    assert "a" not in data["layer"]["config"]
    assert data["layer"]["config"] == {"b": 2}
