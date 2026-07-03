"""Tests for the merge-evidence and guard-report artifacts (validator + template + schema)."""
import json
import pathlib

import pytest

from lodestar.validators import validate_guard_report_obj, validate_merge_evidence_obj

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_merge_evidence_template_validates():
    doc = json.loads((ROOT / "templates" / "merge-evidence.json").read_text(encoding="utf-8"))
    assert validate_merge_evidence_obj(doc) == []


def test_guard_report_template_validates():
    doc = json.loads((ROOT / "templates" / "guard-report.json").read_text(encoding="utf-8"))
    assert validate_guard_report_obj(doc) == []


def test_merge_evidence_requires_conflict_on_fail():
    errors = validate_merge_evidence_obj({"task_id": "T1", "status": "fail", "summary": "conflict"})
    assert any("conflict" in e for e in errors)


def test_guard_report_rejects_empty_checks():
    errors = validate_guard_report_obj({"status": "pass", "summary": "ok", "checks": []})
    assert any("checks" in e for e in errors)


@pytest.mark.parametrize("name", ["merge-evidence", "guard-report"])
def test_new_templates_match_new_schemas(name):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "templates" / f"{name}.json").read_text(encoding="utf-8"))
    jsonschema.validate(doc, schema)
