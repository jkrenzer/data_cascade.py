from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_cascade import load_data_cascade, save_data_cascade


@pytest.fixture()
def sample_tree(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\nversion: 1\n", encoding="utf-8")
    (root / "team.yaml").write_text("members:\n  - Alice\n  - Bob\n", encoding="utf-8")
    (root / "team").mkdir()
    (root / "team" / "roles.yaml").write_text(
        "roles:\n  Alice: Lead\n  Bob: Dev\n", encoding="utf-8"
    )
    (root / "numbers.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    return root


def test_roundtrip_modify_add_delete(sample_tree: Path):
    data, cmap = load_data_cascade(sample_tree)
    data["name"] = "Beta"
    data.setdefault("team", {})["location"] = "EU"
    data["team"]["members"].remove("Bob")
    data["numbers"] = [10, 20]
    save_data_cascade(sample_tree, data, cmap)
    data2, _ = load_data_cascade(sample_tree)
    assert data2 == data


def test_new_root_key_goes_to_main(sample_tree: Path):
    data, cmap = load_data_cascade(sample_tree)
    data["new_root"] = {"flag": True}
    save_data_cascade(sample_tree, data, cmap)
    text = (sample_tree / "__main__.yaml").read_text(encoding="utf-8")
    assert "new_root" in text
