from __future__ import annotations

from data_cascade.pathops import delete_at, get_at, parse_path, set_at


def test_parse_and_access():
    p = parse_path('a.b[1]."x.y"[2]')
    assert p == ("a", "b", "1", "x.y", "2")
    obj = {"a": {"b": [10, {"x.y": [0, 1, 2, 3]}]}}
    assert get_at(obj, p, missing="NA") == 2
    obj2 = set_at(obj, ("a", "b", "0"), 99)
    assert obj2["a"]["b"][0] == 99
    obj3 = delete_at(obj2, ("a", "b", "0"))
    assert obj3["a"]["b"][0] is None
