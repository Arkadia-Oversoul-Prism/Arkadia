# GATE-10 / gate-hygiene — Baseline Fingerprint CI Wiring — Evidence

**Gate:** GATE-10 (Governed Execution) — gate hygiene / CI wiring
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `24a00f856a0286cbb464a4b585117dd57a2646fa`
**Branch:** `gate10/baseline-fingerprint-ci-wiring-01`
**Status:** IMPLEMENTED — tests + negative controls measured; merge is human-only.

## 1. Objective (bounded)

`tests/test_baseline_fingerprint.py` pins the recorded baseline node set
(`tests/fixtures/baseline_node_set.txt`) to a published fingerprint and fails when the
recorded set drifts from it.

**Corrected scope (measured this pass).** An earlier draft of this section said the guard
"reconciles the recorded node set with a live measurement and fails when the two drift
apart". That is an overclaim, and this pass disproved it. The guard hashes the *fixture*
against hardcoded constants (`CANONICAL_OUTCOMES_FINGERPRINT` / `CANONICAL_IDS_FINGERPRINT`)
and never invokes the suite; `grep -nE "subprocess|pytest\.main|--collect" tests/test_baseline_fingerprint.py`
returns nothing. The live suite on `main` @ `24a00f85` reports **17** failing/error nodes
(§7) while the recorded set holds **10**, and the guard passes on both trees. Its verdict is
therefore a function of the fixture and of the four `FINGERPRINT_DOCS`, not of the
repository's live debt.

What remains true, and is what this pass wires: no workflow executed the guard. Measured on
`main` @ `24a00f85`:

```
grep -rn baseline_fingerprint .github/workflows/     -> 0 matches
```

No workflow executed it. The reconciliation therefore held only when a human invoked it
by hand — the defect class this repository names elsewhere: **a guard no workflow
executes is decoration**.

This pass gives the guard an executable surface, and states the wiring invariant once,
generically, so it cannot be silently disarmed.

## 2. Change set

| File | Change |
|---|---|
| `.github/workflows/baseline-fingerprint.yml` | **New.** Runs `tests/test_baseline_fingerprint.py` + `tests/test_baseline_fingerprint_ci_wiring.py` on `pull_request`, `push` to `main`, and `workflow_dispatch`. Full-history checkout (`fetch-depth: 0`). |
| `tests/test_baseline_fingerprint_ci_wiring.py` | **New.** 9 test functions: 5 negative controls over the detectors plus the wiring invariants, parametrized over every workflow that runs the guard. |
| `docs/control-plane/evidence/gate10-baseline-fingerprint-ci-wiring-01/EVIDENCE.md` | This document. |

Explicit non-goals: no change to `tests/test_baseline_fingerprint.py` (the guard), no
fixture change, no CP10 allowlist change, no baseline-debt repair, no scope expansion.

## 3. The invariant, and why it is stated generically

Four properties, asserted over **every** workflow that runs the guard (so a second
wiring is judged by the same rule, and deleting this one cannot make the assertions
vacuous). The first three are stated here; the fourth is the derived-input invariant in
§3.1 below. Every cited name is one of the suite's 9 test functions, verified by
`grep -n "^def test_" tests/test_baseline_fingerprint_ci_wiring.py`:

1. **Some workflow runs the guard.** `test_a_workflow_executes_the_fingerprint_guard`.
2. **That workflow is selected by the surfaces it judges.**
   `test_guard_workflow_is_selected_by_the_guard_and_its_fixtures` requires the
   `pull_request` path filter to name the guard file, `tests/fixtures/**`, *and* every
   document in the guard's `FINGERPRINT_DOCS`.
3. **The guard step can fail the job.** `test_guard_workflow_judges_its_guard_step`
   rejects `continue-on-error: true`. `test_guard_workflow_checks_out_full_history`
   requires `fetch-depth: 0`, because the guard's node set is documented as
   clone-depth sensitive.

### The measured defect this pass also repaired

The first draft of the workflow named only the guard, the script and `tests/fixtures/**`.
That is **incomplete**: the guard's verdict is a function of its inputs, and it also
asserts that four published documents carry the canonical fingerprint
(`FINGERPRINT_DOCS` = `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`,
`docs/phase1/CONTINUATION_LEDGER.md`). A commit editing `.bootstrap/01_STATE.md` could
change what the guard asserts without executing the guard. The filter now names all four
on both `pull_request` and `push`.

`test_guard_workflow_is_selected_by_the_guard_and_its_fixtures` failed on the incomplete
filter and passes on the complete one — the detector bit on the real defect, not only on
a synthetic one.

### The input list is derived, not restated

4. **The published-doc list is read from the guard, not restated.**
   `test_published_doc_list_is_read_from_the_guard_not_restated`. This is what makes
   property 2 non-vacuous: the coverage assertion consumes the guard's own list.

`_guard_published_docs()` reads `FINGERPRINT_DOCS` from the guard's source by AST. A
second hand-maintained copy would drift, and a drifted copy would make the coverage
assertion vacuous. Consequence, deliberately accepted: if a future pass adds an entry to
`FINGERPRINT_DOCS`, this workflow must add the same path to its trigger filter in the
same change or CI reddens. That is the intended behaviour (an input whose edit must
execute the guard), and it is exercised as negative control 5 below.

## 4. Verification

```
python -m py_compile api/main.py                                  -> OK (boot code untouched)
python -c "yaml.safe_load(.github/workflows/baseline-fingerprint.yml)" -> OK
   pull_request paths 9 / push paths 9, sets identical
grep -nE 'github\.event|\$\{\{' .github/workflows/baseline-fingerprint.yml -> no untrusted interpolation
pytest tests/test_baseline_fingerprint_ci_wiring.py -q            -> 9 passed
pytest tests/test_baseline_fingerprint.py tests/test_baseline_fingerprint_ci_wiring.py -q
                                                                  -> 33 passed (CI-shaped: no PYTHONPATH)
printf '...two paths...' | python scripts/cp10_mutation_boundary_policy.py --judge
                                                                  -> Mutation boundary PASS
```

## 5. Negative controls (each restored after measurement)

The detectors were proven against the forms they are meant to catch. A guard that cannot
go red is not a guard.

| # | Mutation | Expected | Measured |
|---|---|---|---|
| 1 | Workflow omits its own file from the trigger filter | red | red |
| 2 | `fetch-depth: 0` removed (shallow checkout) | red | `test_guard_workflow_checks_out_full_history[baseline-fingerprint.yml]` failed |
| 3 | `tests/fixtures/**` removed from the filter | red | `_selects_path(...)` false; assertion failed |
| 4 | `MISSION.md` removed from the filter | red | `test_guard_workflow_is_selected_by_the_guard_and_its_fixtures[baseline-fingerprint.yml]` failed (1 failed, 8 passed) |
| 5 | `AGENTS.md` added to the guard's `FINGERPRINT_DOCS` only (workflow unchanged) | red | same node failed (1 failed, 8 passed) — proves the coverage assertion is derived, not a stale copy |

Control 5 is the load-bearing one for §3: it proves that extending the guard's inputs
without extending the workflow's filter is detected.

## 6. Regression boundary

Full-suite node-set comparison, `main` @ `24a00f85` vs this branch, both with
`PYTHONPATH=archive/legacy_python` and `--continue-on-collection-errors -rEf`, both
measured in this environment on the same day:

```
main   24a00f85 : 16 failed, 1772 passed, 22 skipped, 1 error  (17 nodes)
branch          : 16 failed, 1786 passed, 22 skipped, 1 error  (17 nodes)

outcomes  main  26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798
outcomes  branch 26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798
ids       main  571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224
ids       branch 571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224
```

**Node-set delta: zero** — identical fingerprints, byte for byte, on both derivations.

The `+14 passed` is exactly the `+14` collected nodes the branch adds, measured by
`--collect-only` on both trees (1809 → 1823). Every contributor was found by diffing the
per-file collected count across the two trees, not inferred from the total:

| Source | New nodes |
|---|---|
| `tests/test_baseline_fingerprint_ci_wiring.py` (new file) | 9 |
| `tests/test_ci_gate_trigger_coverage.py` — parametrized over the new workflow | 3 |
| `tests/test_ci_suite_collection_continuation.py` — parametrized over the new workflow | 1 |
| `tests/test_workflow_injection_boundary.py` — parametrized over the new workflow | 1 |

Three generic suites iterate `.github/workflows/*.yml`, so a new workflow adds passing
nodes to them by construction. That is why the branch's passing count rises by more than
its own test file contributes, and why a count delta alone is not attributable here.

Fingerprints re-derived with `scripts/baseline_fingerprint.py` (the reproducible
derivation, not a hand-computed hash).

### Architecture fitness

```
python -m pytest tests/architecture -q   -> 11 passed
```

The architecture suite is green on `main` and on this branch (the contract's "9/10"
baseline does not reproduce here — the live suite is 11 nodes and all pass).

## 7. Pre-existing debt observed (NOT owned by this workstream)

These are red on `main` @ `24a00f85` and unchanged by this branch. They are recorded,
not repaired — a different workstream owns each.

### 7.1 Owned elsewhere (each has an open PR)

| Node | Owner |
|---|---|
| `tests/test_ci_gate_trigger_coverage.py::test_pr_pytest_workflow_is_selected_by_its_own_file[n-atlas-developer-lab.yml]` | open PR #355 (touches `n-atlas-developer-lab.yml`) |
| `tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix` | open PR #354 (`GATE-10: admit tracked deploy/ surface to CP10 allowlist`) |
| `tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface` | open PR #354 |
| `tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface` | open PR #354 |

The CP10 omission is real and pre-existing. `deploy/n-atlas-server/` was added by
`e074a63b` (2026-10-07) and merged as PR #352 (`a27c6c80`, 2026-10-07 23:18), and no rule
in `scripts/cp10_mutation_boundary_policy.py::LEGIT` matches it
(`git show origin/main:scripts/cp10_mutation_boundary_policy.py | grep deploy` → nothing).
**This pass does not touch that policy module**, so it neither fixes nor worsens the gate.

### 7.2 Unowned drift — three nodes red on live `main` with no owner

These three are red on live `main` and no open PR covers them. Each was introduced by a
commit that post-dates the recorded fixture. They are recorded here and **not repaired**:
`tests/architecture/LAYER_MAP.py` classifies `api/lab_routes.py` as an **authority
surface**, and `api/lab_routes.py` carries the Engineering Lab mutation boundary
(`record_authorization` rejects non-`human` origin). Editing either to make a test green
is an authority-boundary change, which is sovereign-only. Proposing that work is in
scope; executing it inside this pass is not.

| Node | Introduced by | Date | Why it is red |
|---|---|---|---|
| `tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | `2b87e8ef` (PR #276) | 2026-10-04 | asserts the Landing copy `One intelligence. Four ways to work with it.`; the landing now renders `…ONE SYSTEM · MANY SURFACES · ONE CONTINUOUS FIELD` |
| `tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | `72432353` (2026-10-07) | 2026-10-07 | `/api/lab/engineering/n-atlas/run` and `/api/lab/engineering/n-atlas/test-session` are now mutating Lab endpoints; the pinned `ALLOWED_MUTATION_ENDPOINTS` set predates them |
| `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` | `f96d5fd2` (PR #353) | 2026-10-07 | asserts `require_auth` is a router dependency; the router now carries `require_lab_auth` |

### 7.3 The recorded set is stale, and the guard does not detect it

The recorded set holds **10** nodes; live `main` reports **17** (§6). The seven-node
difference is exactly §7.1 (4) + §7.2 (3). The guard passes on both because it hashes the
fixture rather than measuring — see the corrected scope in §1. This is why §1's original
wording was wrong, and why the guard's green is not evidence that the recorded set
describes live debt.

Provenance check that distinguishes drift from an ignored baseline: at the reconciliation
commit `05e031a1` (2026-10-04, `gate-hygiene: reconcile baseline node set to live main`)
neither `deploy/n-atlas-server/Dockerfile` nor `.github/workflows/n-atlas-developer-lab.yml`
existed (`git cat-file -e 05e031a1:<path>` → absent for both), and the CP10 `LEGIT` list at
that commit contained no `deploy` rule. The surfaces arrived on 2026-10-07, so these four
nodes are **drift after** the reconciliation, not debt the reconciliation chose to ignore.
The other three post-date it as well (2026-10-04 → 2026-10-07).

## 8. Authority boundary

Merge is human-only. This pass created no authorization path and no second mutation
path. The workflow carries no `contents: write`, no merge step, and interpolates no
untrusted event text into `run:`.
