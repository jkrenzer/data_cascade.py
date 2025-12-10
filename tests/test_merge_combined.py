# Combined tests: ensure both list and dict settings in the same __config__ apply.
from __future__ import annotations

from pathlib import Path

from data_cascade import load_data_cascade


def _write_yaml(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def test_combined_list_and_dict_settings(tmp_path: Path):
    # Verify that a single __config__ file with both list and dict settings is respected.
    root = tmp_path / "data"
    root.mkdir()
    _write_yaml(
        root / "__main__.yaml",
        "layer:\n  items:\n    - a\n    - b\n  config:\n    k1: v1\n",
    )
    _write_yaml(root / "layer.yaml", "items:\n  - c\nconfig:\n  k2: v2\n")
    _write_yaml(
        root / "__config__.yaml",
        "data:\n  merge:\n    list:\n      mode: extend\n    dict:\n      mode: deep\n",
    )

    data, _ = load_data_cascade(root)
    assert data["layer"]["items"] == ["a", "b", "c"]
    assert data["layer"]["config"]["k1"] == "v1"
    assert data["layer"]["config"]["k2"] == "v2"
