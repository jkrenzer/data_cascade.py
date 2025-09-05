from __future__ import annotations

from pathlib import Path

from data_cascade import load_data_cascade, save_data_cascade


def test_preserve_directory_file_mapping(tmp_path: Path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("root_key: 1\n", encoding="utf-8")
    (root / "a.yaml").write_text("x: 1\n", encoding="utf-8")
    (root / "a").mkdir()
    (root / "a" / "b.yaml").write_text("y: 2\n", encoding="utf-8")

    data, cmap = load_data_cascade(root)
    data["a"]["x"] = 99
    data["a"]["b"]["y"] = 123
    save_data_cascade(root, data, cmap)

    assert (root / "a.yaml").exists()
    assert (root / "a" / "b.yaml").exists()
    data2, _ = load_data_cascade(root)
    assert data2 == data
