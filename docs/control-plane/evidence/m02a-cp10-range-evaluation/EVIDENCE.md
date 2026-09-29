# M02A follow-on — CP10 range evaluation + boundary self-coverage

**Gate:** GATE-10 (Governed Execution) · M02A follow-on
**Supersedes rationale in:** `docs/control-plane/evidence/m02a-ci-gate-integrity/EVIDENCE.md`
**Branch:** `gate10/cp10-range-evaluation`
**Base:** `main`

## Defect 1 — the boundary judged only the tip commit

The M02A step ran `git diff --name-only HEAD^ HEAD`. On a pull-request run the
checkout is the head commit, so that range is the PR's **last commit only**. Any
path introduced in an earlier PR commit shows no change there and can never fail.

This is not theoretical. PR #110 (`feat/opportunity-radar-capture-mvp`) added
`opportunity_radar/SAPZ_CAPTURE_STATE.md`, which no allowlist surface admitted.
The gate reddened on the merge (run 36514924096, job 109234968163) and then went
green on the next merge **without the surface being admitted** — the offender was
masked, not resolved. The allowlist gap was closed separately in PR #111; this
change closes the range defect that would mask any future earlier-commit offender.

The same blind spot applied to the constitutional `forbid` stage: a
`SolSpireExperienceV2/V3` implementation added in an earlier PR commit and
followed by any unrelated commit was diffed as "no change".

## Repair

- `scripts/cp10_mutation_boundary_policy.py` gains `resolve_range_endpoint()` —
  a tested, single source of truth for the guarded range:
  `pull_request.base.sha` → `push.before` → `HEAD^` (fallback) → **undeterminable**.
  An all-zero `before` (branch-creation push) falls back to `HEAD^`.
  When no range can be determined the function returns `None` and the caller
  **fails** — it does not silently pass.
- The workflow diffs `"$base" HEAD` for the allowlist scan, the V2 forbid scan,
  and the workflow-automation scan, and fetches with `fetch-depth: 0` (was `2`,
  which only reached `HEAD^`).
- The workflow trigger `paths` now include the boundary's own contract surfaces
  (`scripts/cp10_mutation_boundary_policy.py`, `tests/test_m02a_ci_gate_integrity.py`)
  so the gate is judged by the policy it rewrites instead of being self-exempt.

## Runtime evidence — full CI step, real git objects

The **verbatim** workflow step was executed against a purpose-built repository
(offender added in commit 1, unrelated legitimate commit 2) with
`GITHUB_EVENT_PATH` carrying `pull_request.base.sha`. The step body was extracted
from the workflow YAML, so the assertion surface is the shipped code, not a
re-implementation.

```
SCENARIO 1 - masked offender (multi-commit PR)
  NEW (base..HEAD)         exit=1  "Unexpected path outside legitimate repository surfaces: secret-backdoor/bin"
  OLD (HEAD^ HEAD)         exit=0  "Mutation boundary PASS"
  -> NEW catches what OLD masked.

SCENARIO 2 - legitimate multi-commit PR (web/, api/, docs/)
  NEW (base..HEAD)         exit=0  PASS
  -> no false positive on ordinary multi-commit product work.

SCENARIO 3 - SolSpireExperienceV3 added in an EARLIER PR commit, unrelated commit after
  NEW (base..HEAD)         exit=1
  -> the constitutional forbid stage also sees earlier-commit offenders.
```

## Tests

```
python -m pytest -q tests/test_m02a_ci_gate_integrity.py   -> 44 passed   (baseline 32)
python -m pytest -q tests/architecture                      -> 11 passed
python -m py_compile api/main.py                            -> OK (2519 lines, under budget)
```

Baseline vs changed full suite: **identical failing set** (47 failed / 12 skipped
/ 2 collection errors), `+12 passed`. No regression attributable to this change.

## Remaining uncertainty

- `fetch-depth: 0` clones the full history on a large repository. Correctness of
  the range is chosen over checkout cost; if clone time becomes material the range
  could be bounded by the PR commit count instead.
- `resolve_range_endpoint` is exercised against constructed repos; the CI event
  payload shape for `push` is asserted by unit test, not by a live push run.

## Authority

No merge by automation. No M03. Human merge required.

---

# PASS 2 — GATE-10 · the red gate and the unwatched surface

Pass 1 made the boundary judge the whole guarded range. Pass 2 addresses why the
*executed* gate was red on `main` (`36516287611`) and why a red gate could be merged
onto `main` at all.

## 1. The failure was a test-side fixed-point defect, not a product defect

`tests/test_phase5_governed_execution.py` declared `new_body = "MUTATED BY
COMPARATIVE EXAMINATION I\n"` and then asserted the on-disk file equals it. The
governed K3 write boundary normalises the provider payload (`weaver.agent` parses
file blocks with `content.strip()`), so a declared body ending in newline can never
be observed. Reproduced against the real write path in a scratch repo:

```
declared after : 'MUTATED BY COMPARATIVE EXAMINATION I\n'
actual on disk : 'MUTATED BY COMPARATIVE EXAMINATION I'
EQUAL: False
k15_ready: True   k3: BLOCKED
```

`k15_ready` and the K15-before-K3 ordering were already satisfied; only the
unfalsifiable equality failed. The K3 write path does **not** verify the object
against the approved `after`, so this is not a silent-corruption channel — the
declared content was simply unachievable. The fix makes the declared body a fixed
point of the boundary's own normalisation. Ingested/executed byte-fidelity
verification is a *fast-follow proposal*, not a claim made here.

## 2. The deeper defect: the gate did not run on the surface it judges

`.github/workflows/sg-02-fe-2-v.yml` judged `tests/test_phase5_governed_execution.py`
on `push` but its `pull_request` filter omitted that file (and `lab/evolution/**`,
`lab/execution/**`). A PR could therefore introduce the very fixture the gate
validates without the gate executing — which is how PR #112 landed it against an
already-red gate.

Fixed: the two filters are now identical (21 paths each). Guarded by two new tests
in `tests/test_m02a_ci_gate_integrity.py`, proven falsifiable:

```
against the pre-fix workflow : 2 failed  (test_push_and_pull_request_filters_are_identical,
                                          test_phase5_fixture_surface_triggers_the_boundary)
against the fixed workflow   : 2 passed
```

`test_push_and_pull_request_filters_are_identical` asserts set equality, so a future
widening of one filter is always a widening of both.

## Verification (branch = origin/main merged with the Pass-1 branch)

```
python -m pytest -q tests/test_phase5_governed_execution.py \
                    tests/test_m02a_ci_gate_integrity.py \
                    tests/test_static_ingestion_idempotency.py   -> 52 passed
python -m pytest -q tests/architecture                            -> 11 passed
python -m py_compile api/main.py                                  -> OK (2519, under budget)
```

Full suite, failing-set diff rather than counts (same merged base both sides):

```
main   : 47 failed / 926 passed
branch : 46 failed / 941 passed   (baseline was 47/926)
only failing on main   : test_phase5_governed_execution.py::test_comparative_exam_i_authorization_change_reaches_k15_before_k3
only failing on branch : (none)
```

Zero new failures; one pre-existing failure fixed; +15 passed from the Pass-1 test
additions plus this fix. Note the standing `main` baseline in the contract
(804/54/12/2) is stale against current `main` (6038989 -> 8f9d509).

## Remaining uncertainty

- Pass 2 is proven locally. The CP10 run for this branch has not been observed
  executing yet; the workflow change must be confirmed green in CI.
- `tests/test_m02a_ci_gate_integrity.py`'s new parity test constrains the two
  filters to be equal, not to be *complete* — a surface the gate executes but neither
  filter names is still possible; `test_phase5_fixture_surface_triggers_the_boundary`
  covers the Phase 5 case specifically.

## Pass 3 — rebase onto the post-#113 main (base correction)

PR #113 (`gate10/cp10-range-evaluation`) merged at `2026-09-29T03:57:24Z` with
**Pass 1 only** (`9139039`). Pass 2 (`936f23f`) was committed after that merge, so it
was pushed to an already-closed branch and is **not** in `main`. This pass moved it
onto a fresh branch off the new main.

| | |
|---|---|
| base (main) | `760e7f9` — *Merge pull request #113* |
| branch | `gate10/cp10-trigger-parity` |
| commit | `40b8b1d` |

The Pass-2 measurements above were taken against `8f9d509`. Re-measured on the new
base, same method (failing-set diff, both sides on the identical merged base):

```
main   760e7f9 : 47 failed / 938 passed / 12 skipped / 2 errors
branch 40b8b1d : 46 failed / 941 passed / 12 skipped / 2 errors
only failing on main   : test_phase5_governed_execution.py::test_comparative_exam_i_authorization_change_reaches_k15_before_k3
only failing on branch : (none)
```

Zero new failures; one pre-existing failure fixed. The numbers in Pass 2 stand; only
the base SHA is corrected.

**Trigger parity, measured on `main` `760e7f9`** — the Pass-1 workflow change used
`paths-ignore`, so the two filters are *not* equal there, and `push` names four
surfaces `pull_request` does not:

```
push-only : lab/evolution/**  lab/execution/**
            tests/test_phase4_evolution_planner.py  tests/test_phase5_governed_execution.py
pr-only   : (none)
```

`paths-ignore` and `paths` are disjoint keys, so the corrected filters are written as
identical positive `paths` lists on both triggers — the parity guard asserts set
equality directly.

## Authority

No merge by automation. No M03. Human merge required.
