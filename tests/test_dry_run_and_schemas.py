"""Integration: dry-run passes and its artifacts satisfy the published JSON schemas."""
import json
import pathlib

import pytest

from lodestar.dryrun import run_dry_run

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (schema file, dry-run artifact relative path)
SCHEMA_ARTIFACTS = [
    ("locked-spec.schema.json", "locked-spec.json"),
    ("tasks.schema.json", "task-graph.json"),
    ("execution-plan.schema.json", "execution-plan.json"),
    ("task-state.schema.json", "tasks/T2/state.json"),
    ("proof-bundle.schema.json", "proof-bundle.json"),
    ("build-evidence.schema.json", "build-evidence.json"),
    ("review-report.schema.json", "review-report.json"),
    ("quality-report.schema.json", "quality-report.json"),
    ("browser-evidence.schema.json", "browser-evidence.json"),
    ("debrief.schema.json", "debrief.json"),
    ("handoff.schema.json", "final-handoff.json"),
]


def test_dry_run_passes(tmp_path, monkeypatch):
    # run_dry_run resolves references/ from cwd; run it from the repo root.
    monkeypatch.chdir(ROOT)
    result = run_dry_run(tmp_path / "dry")
    assert result["status"] == "pass"


def test_dry_run_artifacts_match_schemas(tmp_path, monkeypatch):
    jsonschema = pytest.importorskip("jsonschema")
    monkeypatch.chdir(ROOT)
    out = tmp_path / "dry"
    run_dry_run(out)
    for schema_name, artifact in SCHEMA_ARTIFACTS:
        schema_path = ROOT / "schemas" / schema_name
        artifact_path = out / artifact
        if not schema_path.exists() or not artifact_path.exists():
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        doc = json.loads(artifact_path.read_text(encoding="utf-8"))
        jsonschema.validate(doc, schema)


def test_all_schemas_are_valid_json():
    for schema_path in (ROOT / "schemas").glob("*.json"):
        json.loads(schema_path.read_text(encoding="utf-8"))


def _load(out, name):
    return json.loads((out / name).read_text(encoding="utf-8"))


def test_quality_gate_requires_responsive_matrix_for_browser_products(tmp_path, monkeypatch):
    from lodestar.builders import build_quality_report

    monkeypatch.chdir(ROOT)
    out = tmp_path / "dry"
    run_dry_run(out)
    spec = _load(out, "locked-spec.json")
    plan = _load(out, "execution-plan.json")
    build = _load(out, "build-evidence.json")
    review = _load(out, "review-report.json")
    browser = _load(out, "browser-evidence.json")
    matrix = _load(out, "responsive-matrix.json")
    ux_lock = (out / "shape-lock.md").read_text(encoding="utf-8")

    with_matrix = build_quality_report(
        "t", spec, plan, build, review, ux_lock, None, browser, responsive_matrix=matrix
    )
    assert with_matrix["checks"]["regression_smoke"]["status"] == "pass"

    without_matrix = build_quality_report(
        "t", spec, plan, build, review, ux_lock, None, browser, responsive_matrix=None
    )
    assert without_matrix["checks"]["regression_smoke"]["status"] == "fail"
