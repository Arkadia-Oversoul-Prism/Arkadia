# WORKSTREAM_STATE — `gate-hygiene/queue-greenness-composition-01`

Pass: `gate-hygiene/queue-greenness-composition-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Status: **READY FOR SOVEREIGN REVIEW** — evidence + one apply-verified, unapplied patch.
Authority: no merge, no push to `main`, no force-push. Human-only merge.

---

## What this pass established

1. PR #158's recommended 14-step sequence is **conflict-free** (reproduced, all 14 clean).
2. It is **not green**: composing it exposes **1 new failure**,
   `test_documented_route_contract.py::test_health_route_documentation_matches_the_served_app`,
   caused by PR **#154** (`/health` route) + PR **#156** (route-contract guard) merging
   together — each correct alone (9 passed alone), contradictory in union.
3. Two baseline improvements are attributed: **#148** fixes both scheduler-bootstrap
   failures; **#149** clears the `test_render_codex.py` collection error.
4. A **2-hunk, docs-only repair** is published as an apply-verified patch; with it applied the
   composed tree is green (0 new failures).

## Live baseline (re-measured this pass, not inherited)

| measurement | value |
|---|---|
| main SHA | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| `tests/architecture` | **11 passed** |
| full suite (`PYTHONPATH=archive/legacy_python`, `--continue-on-collection-errors`) | **20 failed / 1039 passed / 13 skipped / 2 errors** |
| `api/main.py` | 2519 / 2600 lines; `py_compile` OK |

> The contract's stated baseline (`804 passed / 54 failed / 12 skipped`, arch `9/10`) and the
> ledger's (`1008 / 20 / 13`, arch `10/10`) are both **stale**. The numbers above are live.

## Composed-queue result

| tree | full suite |
|---|---|
| composed, no repair | 19 failed / 1090 passed / 15 skipped / 1 error |
| composed, repair applied | **18 failed / 1091 passed / 15 skipped / 1 error** |

Failure-set delta vs baseline (repaired): **2 fixed** (#148), **18 unchanged**, **0 new**.

## Deliverables on this branch

- `EVIDENCE.md` — method, isolation table, fingerprint, attribution, scope boundary.
- `patches/health-row-doc-repair.patch` — 2 hunks, `DEPLOYMENT_GUIDE.md` only; applies once
  #156 has merged; **not applied to `main`**.

## Next bounded task

**Preferred:** sovereign applies `patches/health-row-doc-repair.patch` at the #154 step of the
queue drain (see EVIDENCE §7). This requires **no new engineering pass** — the artifact is
verified and ready.

**If a pass is opened instead:** the next unowned measurement on this workstream is the
**remaining 18 failures** as a bounded triage batch — but only by *classification*, not
repair: `SH-07` (`test_m02_reasomate_truth.py`) and `SH-09` (`test_identity_spine_w1.py`) are
already escalated as **product/architecture decisions**, not test repairs, and must not be
folded into a hygiene batch. The remaining cluster (`test_steward_filter.py` ×3,
`test_spiral_grove_activity_runtime.py` ×4, `test_spiral_grove_registry.py` ×2,
`test_solspire_r1_governance_convergence.py` ×2, `test_solspire_r2_github_mutation.py`,
`test_solspire_r3_execution_runtime.py`, `test_gate_status.py`, `test_gate_serve_script.py`,
`test_ais_w2_living_gate_grove_handoff.py`) is unclassified and is the natural next unit.

**Do not** re-run the composition measurement — it is settled and reproducible from a full
clone (§2 of EVIDENCE).

## Open boundary

All 17 open PRs have **green CI** at their current heads (verified this pass via
`commits/<sha>/check-runs`, full SHA). The only merge-order hazard in the queue is the
#154/#156 pair documented above. Merge remains **human-only**.
