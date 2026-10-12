# WORKSTREAM STATE — gate10/cp10-broad-suite-collection-continuation-01

**Gate** := GATE-10 (governed execution / gate hygiene)
**Branch** := `gate10/cp10-broad-suite-collection-continuation-01`
**BASE_MAIN** := `850216fc99b0eab66a66f8a8290c0db33823b681`
**Status** := IMPLEMENTED (repository-source); PR open; **sovereign review required**

## Objective

Make the CP10-B broad-suite step in `sg-02-fe-2-v.yml` actually execute the suite,
and add a regression guard that covers the *reporting* (non-judging) surface — the
class the existing guard deliberately exempted.

## Bounded scope

- `.github/workflows/sg-02-fe-2-v.yml` — add `--continue-on-collection-errors` to the
  CP10-B step (`continue-on-error: true` retained).
- `tests/test_ci_suite_collection_continuation.py` — new parametrized assertion over
  every workflow + live negative control + positive control.

## Explicit non-goals

- Do not touch `continue-on-error` on CP10-B (it is a reporting surface, not a gate).
- Do not touch `api/main.py`, `api/lab_routes.py`, or the CP10 boundary policy.
- Do not duplicate Defect B (owned by #459) or Defect C (owned by #458).
- Do not classify the 177 broad-suite-only files as decoration.
- Do not add `workflow_dispatch` to path-filtered gates (separate proposed class).

## Evidence

`docs/control-plane/evidence/gate10-cp10-broad-suite-collection-continuation-01/EVIDENCE.md`

## Sibling ownership (contested file `.github/workflows/sg-02-fe-2-v.yml`)

| PR | head | owns |
|---|---|---|
| #458 | `30c87f26` | trigger paths + blocking SolSpire isolated-runtime step |
| #459 | `12f8a0a6` | Grove step `id`/`pipefail`/outcome (Defect B) |
| **this** | — | CP10-B `--continue-on-collection-errors` (Defect A) |

Regions are disjoint (line ~26 / ~187 / ~210-222). Composition measured, not assumed.

## Next bounded task (for the next heartbeat)

Reconstruct live state; if this PR is merged, verify the CP10-B step executes the suite
in a real `sg-02-fe-2-v.yml` run on `main` and record it. If open, do not duplicate —
continue this PR. Remaining proposed (unowned, do not execute without authorization):
`workflow_dispatch` on the five path-filtered gates that lack it
(`arkadia-console-android.yml`, `arkana-signal-conformance.yml`,
`openapi-security-metadata.yml`, `phase6-persistent-execution.yml`,
`solspire-route-composition.yml`).

## Authorization

Human sovereign retains merge authority. No merge, no push to `main`, no force-push.
