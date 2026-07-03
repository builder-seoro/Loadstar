"""Tests for the proof-gate command: gates only flip pass with validated evidence."""
from types import SimpleNamespace

import pytest

from lodestar.commands import command_proof_gate
from lodestar.core import LodestarError, write_json
from lodestar.dryrun import fake_build_evidence
from lodestar.runner import new_proof_bundle


def ns(run_dir, gate, status, evidence="evidence", artifact=None, proof_bundle=None):
    return SimpleNamespace(
        run_dir=str(run_dir), gate=gate, status=status,
        evidence=evidence, artifact=artifact, proof_bundle=proof_bundle,
    )


def seed_bundle(run_dir):
    write_json(run_dir / "proof-bundle.json", new_proof_bundle("run"))


def test_proof_gate_refuses_pass_without_evidence(tmp_path):
    seed_bundle(tmp_path)
    with pytest.raises(LodestarError):
        command_proof_gate(ns(tmp_path, "build", "pass"))


def test_proof_gate_passes_with_valid_evidence(tmp_path):
    seed_bundle(tmp_path)
    write_json(tmp_path / "build-evidence.json", fake_build_evidence("pass"))
    result = command_proof_gate(ns(tmp_path, "build", "pass"))
    assert result["gate_status"] == "pass"
    assert result["proof_status"] == "in-progress"  # other gates still pending
    assert "review_report" in result["missing_artifacts_for_pass"]


def test_proof_gate_rejects_failing_evidence(tmp_path):
    seed_bundle(tmp_path)
    write_json(tmp_path / "build-evidence.json", fake_build_evidence("fail"))
    with pytest.raises(LodestarError):
        command_proof_gate(ns(tmp_path, "build", "pass"))


def test_proof_gate_unknown_gate(tmp_path):
    seed_bundle(tmp_path)
    with pytest.raises(LodestarError):
        command_proof_gate(ns(tmp_path, "not-a-gate", "pass"))


def test_proof_gate_can_fail_a_gate(tmp_path):
    seed_bundle(tmp_path)
    result = command_proof_gate(ns(tmp_path, "ux_guard", "fail", evidence="guard drift"))
    assert result["gate_status"] == "fail"
    assert result["proof_status"] == "in-progress"
