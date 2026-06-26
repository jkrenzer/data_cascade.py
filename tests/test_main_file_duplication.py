"""Tests ensuring __main__.* files do not duplicate sibling-file data on save."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from data_cascade import load_data_cascade, make_cascade, save_data_cascade
from data_cascade.io import load_file


def _load_yaml(path: Path) -> Any:
    return load_file(path) or {}


def test_full_save_does_not_write_sibling_keys_into_main(tmp_path: Path) -> None:
    """Full save_data_cascade must not copy sibling-owned keys into __main__.yaml."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\nversion: 1\n", encoding="utf-8")
    (root / "requirements.yaml").write_text(
        "packages:\n  - numpy\n  - pandas\n", encoding="utf-8"
    )

    data, cmap = load_data_cascade(root)
    save_data_cascade(root, data, cmap)

    raw_main = _load_yaml(root / "__main__.yaml")
    assert (
        "requirements" not in raw_main
    ), "__main__.yaml must not grow the sibling stem 'requirements'"
    assert (
        "packages" not in raw_main
    ), "__main__.yaml must not contain the sibling key 'packages'"

    raw_req = _load_yaml(root / "requirements.yaml")
    assert raw_req == {"packages": ["numpy", "pandas"]}


def test_main_only_keys_saved_correctly_after_fix(tmp_path: Path) -> None:
    """Keys that exist only in __main__ must still round-trip to __main__."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text(
        "name: Alpha\nenv: production\n", encoding="utf-8"
    )
    (root / "team.yaml").write_text("members:\n  - Alice\n", encoding="utf-8")

    data, cmap = load_data_cascade(root)
    save_data_cascade(root, data, cmap)

    raw_main = _load_yaml(root / "__main__.yaml")
    assert raw_main.get("name") == "Alpha"
    assert raw_main.get("env") == "production"

    data2, _ = load_data_cascade(root)
    assert data2["name"] == "Alpha"
    assert data2["env"] == "production"


def test_sibling_wins_ownership_when_key_overlaps_main(tmp_path: Path) -> None:
    """When __main__ defines key 'X' and 'X.yaml' also exists, X.yaml owns the container origin."""
    root = tmp_path / "data"
    root.mkdir()
    # __main__ defines 'db' key; db.yaml also contributes to the 'db' namespace
    (root / "__main__.yaml").write_text(
        "name: Alpha\ndb:\n  host: localhost\n", encoding="utf-8"
    )
    (root / "db.yaml").write_text("port: 5432\n", encoding="utf-8")

    data, cmap = load_data_cascade(root)

    # db.yaml owns the ("db",) container path
    owners = [o.file.name for o in cmap.reverse.get(("db",), [])]
    assert "db.yaml" in owners
    assert "__main__.yaml" not in owners

    # __main__ owns the leaf ("db", "host") but NOT the container ("db",)
    main_owned = cmap.forward.get(root / "__main__.yaml", set())
    assert ("db",) not in main_owned
    assert ("db", "host") in main_owned

    save_data_cascade(root, data, cmap)

    raw_db = _load_yaml(root / "db.yaml")
    assert raw_db.get("port") == 5432

    raw_main = _load_yaml(root / "__main__.yaml")
    assert raw_main.get("name") == "Alpha"
    # __main__ must NOT receive db.port — that key belongs to db.yaml
    assert raw_main.get("db", {}).get("port") is None


def test_dirty_tracking_modifying_sibling_does_not_touch_main(tmp_path: Path) -> None:
    """Mutating a sibling-owned key via make_cascade must not write __main__.yaml."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\n", encoding="utf-8")
    (root / "requirements.yaml").write_text("packages:\n  - numpy\n", encoding="utf-8")

    c = make_cascade(root)
    main_yaml = root / "__main__.yaml"
    req_yaml = root / "requirements.yaml"
    t0_main = main_yaml.stat().st_mtime
    t0_req = req_yaml.stat().st_mtime
    time.sleep(0.1)  # ensure mtime changes

    c.node("requirements").packages.set(["numpy", "scipy"])
    c.save()

    assert main_yaml.stat().st_mtime == t0_main, "__main__.yaml must not be touched"
    assert req_yaml.stat().st_mtime > t0_req, "requirements.yaml must be updated"
    assert "scipy" in req_yaml.read_text(encoding="utf-8")

    raw_main = _load_yaml(main_yaml)
    assert "packages" not in raw_main
    assert "requirements" not in raw_main


def test_no_content_drift_after_repeated_load_save_reload(tmp_path: Path) -> None:
    """Three load/save cycles must leave each file's content identical (idempotency)."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\nversion: 1\n", encoding="utf-8")
    (root / "requirements.yaml").write_text(
        "packages:\n  - numpy\n  - pandas\n", encoding="utf-8"
    )
    (root / "team.yaml").write_text("members:\n  - Alice\n  - Bob\n", encoding="utf-8")

    expected_main = {"name": "Alpha", "version": 1}
    expected_req = {"packages": ["numpy", "pandas"]}
    expected_team = {"members": ["Alice", "Bob"]}

    for _ in range(3):
        data, cmap = load_data_cascade(root)
        save_data_cascade(root, data, cmap)

        assert _load_yaml(root / "__main__.yaml") == expected_main
        assert _load_yaml(root / "requirements.yaml") == expected_req
        assert _load_yaml(root / "team.yaml") == expected_team

    data_final, _ = load_data_cascade(root)
    assert data_final["name"] == "Alpha"
    assert data_final["version"] == 1
    assert data_final["requirements"] == {"packages": ["numpy", "pandas"]}
    assert data_final["team"] == {"members": ["Alice", "Bob"]}


def test_new_key_added_to_data_goes_to_main(tmp_path: Path) -> None:
    """A brand-new key with no prior origin must be routed to __main__ on save."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\n", encoding="utf-8")
    (root / "team.yaml").write_text("members:\n  - Alice\n", encoding="utf-8")

    data, cmap = load_data_cascade(root)
    data["brand_new"] = {"flag": True}
    save_data_cascade(root, data, cmap)

    raw_main = _load_yaml(root / "__main__.yaml")
    assert "brand_new" in raw_main
    assert raw_main["brand_new"] == {"flag": True}

    raw_team = _load_yaml(root / "team.yaml")
    assert "brand_new" not in raw_team
