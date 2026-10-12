# WORKSTREAM STATE — gate10/cp10-broad-suite-collection-continuation-01

**Gate** := GATE-10 (governed execution / gate hygiene)
**Branch** := `gate10/cp10-broad-suite-collection-continuation-01`
**BASE_MAIN** := `850216fc99b0eab66a66f8a8290c0db33823b681`
**PR** := #462
**Heads measured** := `427da5a7` (repair) · `812689be` (repair + evidence) · `c35ab6d2`
**Status** := IMPLEMENTED (repository-source); PR open; **sovereign review required**

> The head moves with each evidence-only commit; the *result* does not. Every head above was
> measured and produced the same outcome (see the table). Read the latest head from the PR,
> not from this line.

## CI result (measured on both heads)

Re-measured after the evidence-only commit — the result is unchanged:

| Head | `validate` (judging, whole suite) | `provider-routing` (reporting) | node set vs `main` |
|---|---|---|---|
| `427da5a7` (repair) | **pass** | failure | 22 nodes, identical |
| `812689be` (repair + evidence) | **pass** | failure | 22 nodes, identical |

| Gate | Conclusion |
|---|---|
| `validate` (runs the full suite as a *judging* surface) | **pass** |
| `boot-syntax`, `trigger-coverage`, `Full-history secret scan` | pass |
| `provider-routing` | failure — **pre-existing `main` debt, node-identical** |

Attribution was measured, not argued: `gh workflow run provider-routing.yml --ref main`
(run `38203666667`, head `850216fc` == main) reproduces the **same 22-node** failing/error
set as both branch runs (`38203244231`, `38203942626`); `diff` of the sorted node lists is
empty each time, and none of the 22 nodes are in this repair's files. `main` itself fails
`provider-routing`. See EVIDENCE.md §6.

## Duplicate-repair check (all open PRs, measured)

Scanned every open PR's diff for an actual `+`-line adding the flag to a workflow step:
none exists. Other matches are prose only — `#461` (reconnaissance doc) and `#432`
(evidence docs) *describe* the defect/flag; `#459` names it in a comment; `#458` and
`#457` cite the documented command line. No sibling duplicates Defect A.

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
