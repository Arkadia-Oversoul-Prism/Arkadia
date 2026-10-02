# CP10 allowlist reconciliation — `reconciliation/` surface

Gate: GATE-10 (governed execution) — CP10 mutation boundary (`SG-02-FE.2-V`)
Class: allowlist omission (the recurring defect class recorded in `AGENTS.md`)
Status: IMPLEMENTED — proof complete locally; sovereign merge required

## Observation

Base main: `ae847ddfd4bd01bd61e3c26545f90f3fe217f5a5` (2026-10-02T04:32:16+01:00).

`tests/test_m02a_ci_gate_integrity.py` was **3 failed / 46 passed** on `main`:

```
FAILED test_allowlist_admits_every_tracked_top_level_prefix
FAILED test_allowlist_covers_every_tracked_surface
FAILED test_delegated_verdict_admits_every_tracked_surface
```

All three fail on a single tracked path:

```
reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md
  -> Unexpected path outside legitimate surfaces
```

Measured directly against the policy module:

```
tracked=1579 rejected=1
  reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md
rejected prefixes: ['reconciliation']
```

`git log --diff-filter=A -- reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md`
returns `ae847dd` (PR #180) — the surface was merged by the same PR whose gate
judged it, and the completeness invariant caught the omission on `main` rather
than on the next unrelated merge.

## Diagnosis

The allowlist in `scripts/cp10_mutation_boundary_policy.py` (`LEGIT`) is an
**inventory of legitimate surfaces**, not a filter. PR #180 merged
`reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md` without enumerating the
`reconciliation/` prefix, so the surface is rejected by the gate that watches
`main`. A later non-merge commit touching `reconciliation/` reddens CP10.

This is not a boundary tightening question: the gate's teeth are the `forbid`
stage (constitutional `SolSpireExperienceV2/V3.tsx`) and the rejection of
**unknown** roots. `reconciliation/` is a tracked control-plane artifact
(the upstream causal-continuity forensic record), so it must be admitted.

## Change

- `scripts/cp10_mutation_boundary_policy.py` — add `reconciliation/` to `LEGIT`,
  with the omission history recorded beside the entry. This module is the
  **single** source of the boundary decision; the workflow executes it via
  `--judge` / `--resolve-range` and carries no second copy.
- `tests/test_m02a_ci_gate_integrity.py` — pin the surface so it cannot silently
  regress: `test_reconciliation_surface_is_legitimate`,
  `test_shipped_reconciliation_changeset_passes_policy`, plus the
  `reconciliation_evil/x.md` lookalike in the two negative-control tests.

## Proof

| Command | Baseline (`main`) | After change |
|---|---|---|
| `pytest tests/test_m02a_ci_gate_integrity.py -q` | 3 failed / 46 passed | **51 passed** |
| `pytest tests/architecture -q` | 11 passed | **11 passed** |
| tracked paths rejected by `evaluate_changed_paths` | 1 of 1579 | **0 of 1579** |

Negative controls (must stay outside the boundary), measured after the change:

```
reconciliation_evil/x.md   -> rejected  (prefix lookalike)
vault/Ideas/x.md           -> rejected  (generated vault note)
secret-backdoor/bin/x      -> rejected  (unknown root)
somewhere/conftest.py      -> rejected  (nested conftest)
```

The delegated CLI (`--judge`) and the imported module agree — asserted by
`test_delegated_verdict_admits_every_tracked_surface` and
`test_judge_cli_decision_matches_the_module_the_tests_import`, both green.

## Scope

Bounded to the CP10 allowlist and its fitness tests. `api/main.py` untouched
(budget unchanged). No workflow change: the workflow already delegates to the
policy module. No new mutation or authorization path.

## Remaining uncertainty

- `Provider Routing Verification` (red on PR #181) is a **separate** workstream:
  `tests/test_autonomy.py` fails at collection because `weaver/autonomy.py`
  resolves `governance/autonomy.json` via `os.getcwd()`. Not touched here.
- `vite build` remains environment-blocked; no frontend change is involved.

## Authorization required

Sovereign merge of this PR. The gate is a `main`-watched boundary, so the fix
must land through the governed path.
