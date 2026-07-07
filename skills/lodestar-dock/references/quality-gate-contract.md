# Lodestar Quality Gate Contract

## Purpose

Convert build, review, UX, integration, and proof evidence into a deterministic
handoff blocker.

## Adapter Command

```powershell
lodestar quality-gate --run-dir .lodestar/runs/<run-id> --out .lodestar/runs/<run-id>/quality-report.json
```

Collect browser evidence before final QA when the product has a renderable UI:

```powershell
lodestar browser-collect --url http://127.0.0.1:3000 --expect-text "Approved surface text" --out .lodestar/runs/<run-id>/browser-evidence.json
```

If a real browser tool produced a rendered snapshot, use `--snapshot` instead
of raw URL/HTML so QA evaluates the hydrated page state.

Use `--report-only` for diagnosis. Without `--report-only`, a failing quality
gate exits non-zero and must not continue to handoff.

## Required Inputs

- `locked-spec.json`
- `execution-plan.json`
- `build-evidence.json`
- `review-report.json`
- `shape-lock.md`
- `browser-evidence.json`
- `proof-bundle.json`

## Required Output

Produce `quality-report.json`.

Required report fields:

- `run_id`
- `spec_id`
- `status`
- `upstream_source`
- `checks`
- `findings`
- `metrics`
- `next_route`
- `artifacts`

Required checks:

- execution completion
- build verification
- review integrity
- UX alignment
- acceptance coverage
- regression smoke
- integration readiness
- accessibility baseline
- proof readiness

Browser evidence contributes to UX alignment, regression smoke, and
accessibility baseline checks. Missing or failed browser evidence blocks final
handoff.

## Proof Bundle Gates

Proof-bundle gates are advanced with the engine command, not hand-edited:

```powershell
lodestar proof-gate --run-dir .lodestar/runs/<run-id> --gate <ux_guard|build|review|amendment|integration|qa|proof> --status pass --evidence "..." --artifact <path>
```

The command validates the backing artifact before flipping the gate
(`build`, `review`, `qa`, and `ux_guard` gates require a valid, non-failing
evidence artifact) and only sets the bundle status to `pass` once all gates
pass and every required artifact is recorded.

## Gate Rules

- Critical or high findings make the report fail.
- Proof-bundle gates must be `pass`, and each such `pass` must be set through the
  `proof-gate` command above so its backing artifact is validated.
- Passing quality reports route to `lodestar-dock`.
- Final handoff requires `browser-evidence.json` in the proof bundle artifacts.
- Failed implementation evidence routes to `lodestar-eva`.
- Repeated or systemic quality failure routes to `lodestar-debrief`.
- UX/spec/integration intent conflicts route to `lodestar-course-correct`.
- Final handoff requires `quality-report.json` in both the proof bundle and
  final handoff artifacts.
