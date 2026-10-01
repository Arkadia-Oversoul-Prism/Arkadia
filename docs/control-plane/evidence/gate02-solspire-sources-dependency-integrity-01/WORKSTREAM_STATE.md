# GATE-02 — SolSpire Sources Dependency Integrity — WORKSTREAM STATE

**Observation timestamp:** 2026-10-01T16:06Z (pass start).
**Pass:** Weaver hourly bounded execution.
**Branch:** `gate02/solspire-sources-dependency-integrity-01`
**Base:** `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f` (`main`)

## Live repository state at pass start

| Fact | Value | Source |
|---|---|---|
| `main` SHA | `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f` | `git log -1 origin/main` |
| Open PRs | **2** — #174, #175 | `gh pr list --state open` |
| #166 | MERGED as `47e4128` | `git merge-base --is-ancestor` |
| #163 | MERGED as `40ac3f3` | `gh pr view 163` |
| Working tree | clean on `main` | `git status --short` |

**Queue reconciliation (Step 04/10 — "prefer the oldest open PR").** Both open
PRs are GATE-01/02 work from other workstreams, both `MERGEABLE` /
`mergeStateStatus: CLEAN`, both awaiting **human** merge:

| PR | Branch | Gate | Independent verification this pass |
|---|---|---|---|
| #174 | `gate02/capability-chamber-union-repair-02` | GATE-02 | head `4c1bc70` tested in worktree: **4 failed → 1 failed** (3 fixed, 0 new) |
| #175 | `gate01/relational-lineage-canonical-provenance` | GATE-01 | not tested (out of this workstream's scope) |

Neither is continued or superseded here: #174 is complete and measured, #175
belongs to GATE-01. This pass therefore opens its **own** bounded branch rather
than stacking unrelated work onto either.

## Classification

**BLOCKED → resolved to IMPLEMENTED.**

The prior pass classified the `gate2_backend_observation.py` result as
`CONTRADICTED`. That classification was **wrong** and is corrected in the
evidence: the observer environment lacked `cryptography`, so the local route
signature omitted the four `/solspire/sources` operations. With the dependency
present the digest is byte-identical to production.

Root defect: **undeclared module-scope dependency.** `cryptography` was reached
only transitively via `pdfminer.six`; nothing declared it, and the
`try/except Exception` mount guard in `api/key_routes.py` converted its absence
into silence rather than failure.

## Changed

| Path | Change |
|---|---|
| `requirements.txt` | declare `cryptography`, with the reason |
| `tests/test_solspire_sources_dependency_integrity.py` | new — 6 tests, 2 negative controls |
| `docs/control-plane/evidence/gate02-solspire-sources-dependency-integrity-01/EVIDENCE.md` | new |

## Verification

- guard tests **6 passed**; architecture fitness **11 passed**
- full suite: baseline `22F/1127P/13S/1E` → branch `22F/1133P/13S/1E`
- failing-node fingerprint **identical (23 nodes)** — no new test-node delta
- `py_compile api/main.py` OK; 2531/2600 budget (file untouched)
- CP10 `--judge` on changed paths: **PASS**
- harness re-run: `backend runtime observation VERIFIED (undiscriminating)`,
  `backend <-> source lineage VERIFIED (undiscriminating)`, digest
  `359677ac7fa906d7e952…` = production

## Gate 2 boundary states (unchanged by this work except lineage)

| Boundary | State |
|---|---|
| current main resolved | VERIFIED |
| main → backend deployment identity | **UNKNOWN** — Render publishes no source SHA |
| backend runtime observation | VERIFIED (undiscriminating) |
| backend ↔ source lineage | VERIFIED (undiscriminating) |
| production acceptance | **NOT CLAIMED** (human authority) |

Deployment identity is **not** promoted by repetition. The route-set oracle is
undiscriminating — all candidate revisions share one signature — so equality
cannot separate the deployed commit. PR #143 parity remains open.

## Next bounded task (for the next heartbeat — do not assume, re-measure)

1. **Reconstruct first.** `main` may have moved; re-resolve the SHA and re-run
   `gh pr list`.
2. **If #174 and #175 are still open and still CLEAN:** they are complete,
   human-authorized-merge candidates. Do not re-touch them.
3. **Next smallest valid task:** the residual `ActivityRuntime` renderer defect
   (`test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`). It is
   the single remaining failure of the four, is **not** fixed by #174, and is a
   clean bounded unit: `ActivityRuntime.tsx` renders
   `data-testid={`activity-surface-${kind}`}` while the test requires a literal
   per-kind attribute. It needs its own branch, and it must land **after** #174
   or it will conflict on the same file.
4. **Proposed, not authorized:** boot-manifest observability (see EVIDENCE §9).

## Authority boundary

Human merge only. No merge, no push to `main`, no force-push performed.
`api/main.py` untouched. No guard removed. No baseline debt repaired.
