# Lodestar Guard Contract

## Purpose

Catch drift between approved product shape and delivered UI/UX.

## Upstream Contracts

- gstack: `third_party/upstream/gstack/design-review`
- gstack: `third_party/upstream/gstack/guard`
- Compound Engineering: `third_party/upstream/compound-engineering-plugin/plugins/compound-engineering/skills/ce-proof`

UX guard compares implementation evidence against the approved UX lock. It is
not a taste review from scratch; it is drift detection against approved product
shape.

Guard runs in one of two modes. Supply only the inputs for the mode you are in.

- **Pre-lock shape check** — confirm the shape being locked matches what was
  shown and approved, before any implementation exists.
- **Post-implementation drift check** — confirm the delivered surface has not
  drifted from the approved shape lock.

## Required Input

### Pre-lock shape check

- `shape-lock.md`
- approved wireframe or preview (`wireframe.html`, `design-preview.html`, or
  `shape.html`)
- `responsive-matrix.json` with mobile, tablet, and desktop pass evidence for
  browser-rendered web surfaces

The post-implementation inputs below are **not** required in pre-lock mode;
there is no build or review evidence to check yet.

### Post-implementation drift check

Everything in the pre-lock list, plus the delivered-surface evidence:

- approved `DESIGN.md`
- `visual-qa.md` with release-quality pass evidence
- implementation evidence or browser screenshot
- `browser-evidence.json` when a browser-rendered surface exists
- `build-evidence.json`
- `review-report.json`

## Required Output

Produce `guard-report.json` and validate it with:

```powershell
lodestar validate guard-report .lodestar/runs/<run-id>/guard-report.json
```

A template exists at `templates/guard-report.json`. Required fields:

- `status` — one of `pass`, `fail`, `warning`.
- `summary` — a non-empty human-readable summary.
- `checks` — a non-empty list; each check has a non-empty `name` and a `status`
  of `pass`, `fail`, `warning`, or `not_applicable`.

Advance the proof-bundle `ux_guard` gate from this report:

```powershell
lodestar proof-gate --run-dir .lodestar/runs/<run-id> --gate ux_guard --status pass --evidence "UX guard passed against shape-lock.md" --artifact .lodestar/runs/<run-id>/guard-report.json
```

Carry enough evidence for the next Lodestar skill to continue without
re-interrogating product intent.

The Quality/QA adapter also reads `shape-lock.md` and approval evidence.
Missing UX lock or browser evidence fails QA and blocks handoff.

## Gate Rules

- Do not silently accept UX drift.
- Do not create new product intent.
- Handoff cannot pass while UX guard fails.
- Handoff cannot pass when release-quality visual QA is missing or failed for a
  UI product.
- Handoff cannot pass when responsive matrix evidence is missing or failing for
  a browser-rendered web product.
- QA cannot pass while UX lock, approved preview evidence, or browser evidence
  is missing.
- Browser evidence must be refreshed after implementation or fixer changes that
  can affect the rendered UI.
- If a drift is product-improving but intent-changing, route to
  `lodestar-course-correct`.
- If a drift is accidental, route to `lodestar-eva`.

## Next Route

Route only to the next valid Lodestar skill or to `lodestar-course-correct`
when product intent, UX lock, or spec meaning would change.
