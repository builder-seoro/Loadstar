"""Tests for approval-provenance enforcement and state schema versioning."""
from pathlib import Path

from lodestar import constants
from lodestar.builders import build_spec_gate_report, recorded_approval_gates
from lodestar.core import write_json
from lodestar.dryrun import fake_locked_spec, fake_task_graph
from lodestar.execution import new_task_state, read_task_state, task_state_path
from lodestar.validators import task_allowed_events

UX_LOCK = "# UX Lock\n\nApproved wireframe, design system, and final UI/UX.\n"


def approval_log():
    return [
        {"status": "accepted", "kind": "approval", "gate": g, "approver": "user", "at": "2026-01-01T00:00:00+00:00", "artifact": f"{g}.html"}
        for g in constants.USER_APPROVAL_GATES
    ]


def test_approved_preview_without_records_fails_spec_gate():
    spec = fake_locked_spec()  # approved_preview is True
    report = build_spec_gate_report(spec, UX_LOCK, [])
    assert report["categories"]["ux_flow"]["status"] == "fail"
    assert any(f["category"] == "ux_flow" and "approval" in f["summary"].lower() for f in report["findings"])


def test_approved_preview_with_records_passes_ux_flow():
    spec = fake_locked_spec()
    report = build_spec_gate_report(spec, UX_LOCK, approval_log())
    assert report["categories"]["ux_flow"]["status"] == "pass"


def test_partial_approval_still_fails():
    spec = fake_locked_spec()
    report = build_spec_gate_report(spec, UX_LOCK, approval_log()[:2])  # missing final_ux
    assert report["categories"]["ux_flow"]["status"] == "fail"


def test_recorded_approval_gates_requires_provenance():
    # accepted but no approver/timestamp does not count
    weak = [{"status": "accepted", "gate": "wireframe"}]
    assert recorded_approval_gates(weak) == set()
    strong = [{"status": "accepted", "gate": "wireframe", "approver": "user", "at": "2026-01-01T00:00:00+00:00"}]
    assert recorded_approval_gates(strong) == {"wireframe"}


def test_new_task_state_is_version_stamped():
    task = fake_task_graph()["tasks"][0]
    state = new_task_state(task, "run", "spec", Path(".lodestar/worktrees/T1"))
    assert state["schema_version"] == constants.STATE_SCHEMA_VERSION


def test_read_heals_stale_next_allowed_events(tmp_path):
    # Simulate a run written by an older engine whose stored event list is stale.
    task = fake_task_graph()["tasks"][0]
    state = new_task_state(task, "run", "spec", Path(".lodestar/worktrees/T1"))
    state["next_allowed_events"] = ["a-removed-event"]
    write_json(task_state_path(tmp_path, state["task_id"]), state)  # bypasses validation
    healed = read_task_state(tmp_path, state["task_id"])  # must not raise
    assert healed["next_allowed_events"] == task_allowed_events(healed["state"])
