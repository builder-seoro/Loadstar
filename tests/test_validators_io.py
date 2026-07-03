"""Tests for cycle detection, path safety, atomic IO, and BOM tolerance."""
import json
import os

import pytest

from lodestar.core import LodestarError, read_json, safe_path_segment, write_json
from lodestar.validators import find_dependency_cycle, validate_task_graph_obj


def base_graph(tasks):
    return {"spec_id": "spec", "status": "ready", "tasks": tasks}


def task(tid, deps=None):
    return {
        "id": tid,
        "title": f"Task {tid}",
        "branch": f"task/{tid}",
        "role": "implementer",
        "acceptance_criteria": ["does a thing"],
        "covers": ["SC1"],
        "dependencies": deps or [],
    }


def test_find_dependency_cycle_direct():
    assert find_dependency_cycle({"a": ["b"], "b": ["a"]}) is not None
    assert find_dependency_cycle({"a": ["b"], "b": []}) is None


def test_task_graph_rejects_cycle():
    graph = base_graph([task("a", ["b"]), task("b", ["c"]), task("c", ["a"])])
    errors = validate_task_graph_obj(graph)
    assert any("dependency cycle" in e for e in errors)


def test_task_graph_accepts_acyclic():
    graph = base_graph([task("a"), task("b", ["a"])])
    errors = validate_task_graph_obj(graph)
    assert not any("cycle" in e for e in errors)


def test_task_graph_rejects_unsafe_task_id():
    graph = base_graph([task("../evil")])
    errors = validate_task_graph_obj(graph)
    assert any("safe path segment" in e for e in errors)


@pytest.mark.parametrize("value,ok", [
    ("T1", True), ("task-1", True), ("a.b_c", True),
    ("../x", False), ("a/b", False), ("a\\b", False), ("C:evil", False),
    ("", False), (".", False), ("..", False), (None, False),
])
def test_safe_path_segment(value, ok):
    assert safe_path_segment(value) is ok


def test_atomic_write_leaves_no_temp_and_valid_json(tmp_path):
    target = tmp_path / "sub" / "state.json"
    write_json(target, {"emoji": "✅ done", "hangul": "한글"})
    assert target.exists()
    data = read_json(target)
    assert data["emoji"].endswith("done")
    # no leftover temp files in the directory
    leftovers = [p.name for p in target.parent.iterdir() if p.name.startswith(".lodestar-tmp-")]
    assert leftovers == []


def test_read_json_tolerates_utf8_bom(tmp_path):
    target = tmp_path / "bom.json"
    target.write_bytes(b"\xef\xbb\xbf" + json.dumps({"k": "v"}).encode("utf-8"))
    assert read_json(target) == {"k": "v"}


def test_read_json_missing_file_is_lodestar_error(tmp_path):
    with pytest.raises(LodestarError):
        read_json(tmp_path / "nope.json")
