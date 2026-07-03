---
name: lodestar-integrator
description: Run build, lint, tests, and runtime checks. Use after implementer or fixer changes code and before review to gather build, lint, test, and runtime evidence.
---

# Lodestar Integrator

Verify the implementation mechanically before review.

## Workflow

1. Run the repo-appropriate build, lint, tests, and smoke checks.
2. Record commands, outputs, failures, and confidence.
3. Route pass to reviewer.
4. Route failure to fixer or debrief by threshold.

## Merge / Integration pass

The engine also routes the `MERGE_READY` task state to this skill with role
`integrator` (separate from the builder role above). When dispatched for a
`MERGE_READY` task, integrate the reviewed task branch per its `merge_risk` and
produce `merge-evidence.json`. Runner events are `merge-pass` (routes to QA),
`merge-conflict` (routes to fixer), and `ce-needed` (routes to debrief).
Resolving merge conflicts during this pass is permitted.

## Rules

- Builder may diagnose but does not silently rewrite implementation. Exception:
  resolving merge conflicts during the integrator merge pass is permitted.
- Build pass is required before normal review.
- Evidence must be concrete.

## Output

Produce `build-evidence.json` (builder role) and `merge-evidence.json`
(integrator/merge role). Read `references/integrator-contract.md` for the exact contract.
