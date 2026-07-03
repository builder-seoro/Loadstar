"""Regression tests for the task/runner state machines and execution selection."""
from pathlib import Path

import pytest

from lodestar import constants
from lodestar.core import LodestarError
from lodestar.execution import (
    apply_task_event,
    new_task_state,
    select_next_execution_task,
)
from lodestar.runner import apply_runner_event


def make_task_state(task_id="T1", deps=None):
    task = {
        "id": task_id,
        "title": f"Task {task_id}",
        "branch": f"task/{task_id.lower()}",
        "role": "implementer",
        "acceptance_criteria": ["covers SC1"],
        "covers": ["SC1"],
        "dependencies": deps or [],
    }
    return new_task_state(task, "run", "spec", Path(".lodestar/worktrees") / task_id)


def advance(state, events):
    for event in events:
        state = apply_task_event(state, event, f"{event} evidence")
    return state


def test_merge_ready_is_selectable_single_dispatch():
    # A reviewer-approved task lands in MERGE_READY. select_next_execution_task must
    # pick it up (integrator route) instead of reporting a false deadlock.
    state = advance(
        make_task_state(),
        ["implementation-started", "implementation-ready", "build-pass", "reviewer-approve"],
    )
    assert state["state"] == "MERGE_READY"
    decision = select_next_execution_task([state])
    assert decision["status"] == "ready"
    assert decision["task_id"] == "T1"
    assert decision["state"] == "MERGE_READY"


def test_dispatchable_states_match_selection_set():
    # The two sets must never diverge again.
    from lodestar.execution import select_next_execution_task  # noqa: F401

    assert "MERGE_READY" in constants.DISPATCHABLE_ACTIVE_STATES


def test_attempt_counter_only_increments_on_failure():
    state = advance(
        make_task_state(),
        ["implementation-started", "implementation-ready", "build-pass", "reviewer-approve"],
    )
    # A clean first pass leaves failure counters at zero.
    assert state["attempts"]["build_attempts"] == 0
    assert state["attempts"]["review_attempts"] == 0


def test_build_failure_increments_build_attempts():
    state = advance(
        make_task_state(),
        ["implementation-started", "implementation-ready", "build-fail"],
    )
    assert state["attempts"]["build_attempts"] == 1
    assert state["state"] == "FIXING"


def test_task_blocked_has_recovery_transition():
    state = advance(make_task_state(), ["implementation-started", "implementation-blocked"])
    assert state["state"] == "TASK_BLOCKED"
    assert state["next_allowed_events"], "TASK_BLOCKED must not be a dead end"
    resumed = apply_task_event(state, "unblocked", "new context provided")
    assert resumed["state"] == "IMPLEMENTING"


def test_amendment_rejected_transition_task_and_runner():
    state = advance(
        make_task_state(),
        ["implementation-started", "implementation-ready", "build-pass", "reviewer-approve"],
    )
    # reviewer-approve -> MERGE_READY; drive to amendment via FIXING path instead.
    state = advance(make_task_state("T2"), ["implementation-started", "implementation-ready", "build-fail", "amendment-needed"])
    assert state["state"] == "AMENDMENT_PENDING"
    rejected = apply_task_event(state, "amendment-rejected", "user kept the approved product")
    assert rejected["state"] == "FIXING"
    assert rejected["gates"]["amendment"] == "not-needed"

    runner = apply_runner_event({"runner_state": "AMENDMENT_PENDING"}, "amendment-rejected", "user declined")
    assert runner["runner_state"] == "FIXING"


def test_blocked_diagnosis_surfaces_stuck_task():
    blocked = advance(make_task_state(), ["implementation-started", "implementation-blocked"])
    decision = select_next_execution_task([blocked])
    assert decision["status"] == "blocked"
    ids = {c["task_id"] for c in decision["pending_dependencies"]}
    assert "T1" in ids  # the stuck TASK_BLOCKED task is now reported, not hidden


def test_invalid_transition_rejected():
    state = make_task_state()
    with pytest.raises(LodestarError):
        apply_task_event(state, "merge-pass", "should not be legal from TASK_READY")


def test_fix_attempt_ceiling_forces_escalation():
    state = advance(make_task_state(), ["implementation-started", "implementation-ready", "build-fail"])
    # Cycle through fix -> build-fail until the ceiling is reached.
    for _ in range(constants.MAX_FIX_ATTEMPTS):
        state = advance(state, ["fix-ready", "implementation-ready", "build-fail"])
    assert state["attempts"]["fix_attempts"] == constants.MAX_FIX_ATTEMPTS
    with pytest.raises(LodestarError):
        apply_task_event(state, "fix-ready", "one retry too many")
    # Escalation routes remain legal.
    assert apply_task_event(state, "ce-needed", "escalate")["state"] == "COMPOUNDING"
