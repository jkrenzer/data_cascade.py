
from __future__ import annotations
from pathlib import Path
import json, time
from data_cascade import make_cascade

def setup_tree(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    (root / "__main__.yaml").write_text("name: Alpha\n", encoding="utf-8")
    (root / "team.yaml").write_text("members:\n  - Alice\n  - Bob\n", encoding="utf-8")
    (root / "numbers.json").write_text(json.dumps([1,2,3]), encoding="utf-8")
    return root

def test_proxy_and_dirty_save(tmp_path: Path):
    root = setup_tree(tmp_path)
    c = make_cascade(root)
    team_yaml = root / "team.yaml"
    numbers_json = root / "numbers.json"
    t0_team = team_yaml.stat().st_mtime
    t0_numbers = numbers_json.stat().st_mtime
    time.sleep(0.1)  # ensure mtime changes

    # modify only team
    c.node("team").members.set(["Alice", "Carol"])
    c.save()
    t1_team = team_yaml.stat().st_mtime
    t1_numbers = numbers_json.stat().st_mtime
    assert t1_team > t0_team
    assert t1_numbers == t0_numbers
    assert "Carol" in team_yaml.read_text(encoding="utf-8")
    assert "Alice" in team_yaml.read_text(encoding="utf-8")
    assert "Bob" not in team_yaml.read_text(encoding="utf-8")

    # add new root key, should touch __main__.yaml
    main_yaml = root / "__main__.yaml"
    t0_main = main_yaml.stat().st_mtime
    time.sleep(0.1)  # ensure mtime changes
    c.set("new_root.flag", True)
    c.save()
    t1_main = main_yaml.stat().st_mtime
    assert t1_main > t0_main
    assert "new_root" in main_yaml.read_text(encoding="utf-8")
