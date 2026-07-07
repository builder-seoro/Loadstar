# Lodestar EVA Contract

## Purpose

Own code changes after failure feedback.

## Required Input

Use the upstream Lodestar artifacts and evidence required by this workflow step. If the required upstream artifact is missing, stop and route backward rather than guessing.

## Required Output

Produce `fix-handoff.json` with enough evidence for the next Lodestar skill to continue without re-interrogating product intent.

The runner event sequence is:

- `fix-ready` returns to implementer before builder/reviewer.
- `ce-needed` activates debrief mode for repeated or unclear failures.
- `amendment-needed` routes spec/product conflicts to amendment advisor.

### Recording the outcome

After producing `fix-handoff.json`, record the result with the engine:

```powershell
lodestar task-event --run-dir .lodestar/runs/<run-id> --task-id <task-id> --event <event> --evidence "..." --artifact <path-to-output-artifact>
```

Valid `<event>` values for this role are `fix-ready`, `ce-needed`, and `amendment-needed`.

## Gate Rules

- Do not bypass builder.
- Do not broaden scope silently.
- Route spec or product conflicts to amend advisor.

## Next Route

Route only to the next valid Lodestar skill or to `lodestar-course-correct` when product intent, UX lock, or spec meaning would change.
