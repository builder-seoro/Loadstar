---
name: lodestar-guard
description: Check implementation against the UX lock. Use during execution, review, integration, or handoff when implementation must be checked for drift from shape-lock.md and approved product-shape evidence.
---

# Lodestar Guard

Catch drift between approved product shape and delivered UI/UX.

Guard runs in two modes. In **pre-lock** mode it is a shape check whose only
inputs are shape-lock.md, the approved wireframe/preview, and
responsive-matrix.json. In **post-implementation** mode it is a drift check that
additionally reads build-evidence.json, review-report.json, and
browser/screenshot evidence. Supply only the inputs for your mode.

## Workflow

1. Compare delivered product with shape-lock.md and preview evidence.
2. Classify differences as implementation miss or product amendment.
3. Route implementation misses to lodestar-eva.
4. Route product-shape changes to lodestar-course-correct.

## Rules

- Do not silently accept UX drift.
- Do not create new product intent.
- Handoff cannot pass while UX guard fails.

## Output

Produce `guard-report.json` and validate it with `lodestar validate guard-report <path>` (template at `templates/guard-report.json`; required fields `status`, `summary`, and a non-empty `checks` list). Advance the proof-bundle gate with `lodestar proof-gate --run-dir .lodestar/runs/<run-id> --gate ux_guard --status pass --evidence "..." --artifact .lodestar/runs/<run-id>/guard-report.json`. Read `references/guard-contract.md` for the exact contract.
