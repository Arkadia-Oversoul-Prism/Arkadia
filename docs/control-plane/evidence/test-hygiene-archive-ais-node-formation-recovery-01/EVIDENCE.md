# Recover the archived A.I.S node-formation write path and re-pin two stale assertions

**Workstream:** `test-hygiene/archive-ais-node-formation-recovery-01`
**Base:** `main` `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22, observed)
**Authority:** implementation + evidence only. No merge, no deployment, no acceptance (GOV-03).
**Status:** PASS locally (targeted + full suite node-set compared by identity).

---

## 1. Observation at pass start

| Fact | Value |
|---|---|
| `origin/main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (local `main` identical, 0 ahead / 0 behind) |
| Check-runs on that commit | 6 `success`, 1 `skipped` (`weaver_evolution`) |
| Open PRs | 21, all drafts |
| Live failing/error node set (full suite, `-rEf --continue-on-collection-errors`) | **20 nodes**, sha256 `8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` |

Classification of those 20 nodes at `bb19aabd`:

| Nodes | Class | Owner |
|---|---|---|
| `ERROR tests/test_autonomy.py` | CE-01 module-vs-package collision | sovereign-reserved |
| `test_mission_lifecycle_adapter_contract.py` (10) | environment: `web/arkadia_console/node_modules/typescript` absent in this sandbox | none |
| `test_solspire_r1_governance_convergence.py` (2) | test-side pins | PR #693 |
| `test_solspire_r3_execution_runtime.py` (1) | test-side pin | PR #691 |
| `test_static_ingestion_idempotency.py` (1) | order-dependent shared store | PR #698 |
| `test_m01_persistence.py` (1) | store signature | PR #690 |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | F-01 proxy invalidation awaiting a sovereign decision | sovereign-reserved (documented in the test) |
| **`test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`** | **stale assertion over a latent product defect** | **this pass** |
| **`test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key`** | **stale assertion** | **this pass** |

The two nodes owned by this pass were already diagnosed on the unmerged branch
`gate-hygiene/repair-two-standalone-stale-pins` (commit `20008f0c`, 2026-10-08). That repair
targeted the then-live `web/public_prism/...` paths; the Prism source was archived by
`c081d200` (2026-10-11) and the repair was never merged, so the tests now read the archive
and fail against it. This pass **recovers** that repair against the archive paths rather
than re-deriving it.

## 2. The latent defect (source, not only the assertion)

`archive/frontend/arkadia-prism/web/public_prism/src/pages/NodeEntry.tsx` referenced
`AIS_PROFILE_PATH` twice — the mount `GET` (`apiFetch(AIS_PROFILE_PATH, …)`) and the
completion `PATCH` (`apiFetch(AIS_PROFILE_PATH, {method:'PATCH', …})`) — and **never
defined it**. It defined `AIS_URL` from `API_BASE` and never used it.

Measured at `bb19aabd`:

| Symbol | Occurrences | Defined |
|---|---|---|
| `AIS_PROFILE_PATH` | 2 | **no** |
| `AIS_URL` | 1 | yes (dead) |
| `/api/me/ais-profile` | 1 | — |

Both references sit inside `try { … } catch {}` blocks, so the `ReferenceError` was
swallowed. Consequences in the recovered implementation:

- the mount read never reaches `setStage('result')` — a returning node never sees its saved
  pulse;
- `finish()` never reaches `setResult(pulse)` / `onAICComplete(portfolio)` — the A.I.S
  capability portfolio is never written, while the UI un-disables the button in `finally`.

The archive is not built or served, so this changes no shipped behaviour. It is repaired
because the archive is the recovery source for the console reconciliation workstream
(`docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §1–§2): carrying a dead
write path forward would replicate it into the console.

**Fix (1 line):** define `AIS_PROFILE_PATH` with the value the dead `AIS_URL` held, so the
constant is defined and `API_BASE` stays used.

## 3. Change inventory

| Path | Change |
|---|---|
| `archive/frontend/arkadia-prism/web/public_prism/src/pages/NodeEntry.tsx` | `const AIS_URL = …` → `const AIS_PROFILE_PATH = …` (defines the referenced constant, drops the dead one) |
| `tests/test_identity_spine_w1.py` | Re-pin the NodeEntry node to the capability the surface implements: the **definition** of `AIS_PROFILE_PATH` (regex), `/api/me/ais-profile`, `kind:'portfolio'`, `pulse`. Superseded literals recorded verbatim in a comment. |
| `tests/test_m02_reasomate_truth.py` | Re-pin `arkanaSessionId` → `ACTIVE_THREAD_KEY` + `threadStorageKey` + the `session_id: activeThreadId` call site. Superseded literal recorded verbatim. |

Non-goals: no assertion was dropped without a replacement property; no product decision was
taken (the Grove-catalogue question stays escalated in
`tests/test_ais_w2_living_gate_grove_handoff.py`); no other baseline node was touched;
`api/main.py` was not modified.

## 4. Proof

**Targeted:**

```
python -m pytest tests/test_identity_spine_w1.py tests/test_m02_reasomate_truth.py -q
20 passed in 0.97s
```

**Negative control (the definition guard bites):** revert only the source fix
(`AIS_PROFILE_PATH` → `AIS_URL`) in the working tree and re-run the node:

```
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
1 failed in 0.07s
```

Restore byte-identically → `1 passed`. The assertion measures the defect, not its absence.

**Positive control for the m02 re-pin:** the symbols asserted are the ones the archive
actually carries — `ACTIVE_THREAD_KEY` ×3, `threadStorageKey` ×5, `session_id: activeThreadId`
×1 (`grep -o … | sort | uniq -c`). The node is not vacuous: it fails if the shared key, the
derived per-project key, or the wire-level call site is removed.

**Full suite** (`PYTHONPATH=archive/legacy_python python -m pytest tests/ -q -rEf
--continue-on-collection-errors`) — node-set comparison by identity, not by count:

| Tree | result | failing/error nodes | sha256 |
|---|---|---|---|
| `main` `bb19aabd` | 19 failed, 4250 passed, 22 skipped, 1 error | 20 | `8d70e46e…` |
| this branch | 17 failed, 4252 passed, 22 skipped, 1 error | 18 | `726440c3…` |

`comm -3` between the two sorted node sets prints **three** lines, all "only in `main`":

- the two nodes this pass repaired;
- `tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`,
  the known order-dependent shared-store node (owned by PR #698) that happened to pass on
  this run. It is **not** attributable to this change and is not claimed as repaired.

**No node appears only on the branch** — zero regressions.


**Mutation boundary:**

```
printf '<the four changed paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

## 5. Result

Remaining live debt after this pass is the same set minus the two repaired nodes: CE-01
`test_autonomy.py` (sovereign), the 10 environment nodes that need
`web/arkadia_console/node_modules`, and the five nodes owned by open PRs
#690/#691/#693/#698 plus the documented F-01 node.

## 6. Unresolved, recorded not repaired

- **Open-PR composition hazard (measured, not assumed).** PRs #681 and #687 both modify
  `scripts/gate2_production_observation.py` and `tests/test_gate2_production_observation.py`.
  A real `git merge` of #687's branch onto #681's head reports
  `CONFLICT (content): Merge conflict in tests/test_gate2_production_observation.py`
  (1 conflicted file; the script auto-merges). Merge order is the human sovereign's; the
  pair must not be merged unreconciled.
- **`tests/fixtures/baseline_node_set.txt` is stale beyond the entries PR #693 removes.**
  It records `test_steward_filter.py` (3 nodes) as failing; those nodes **pass** live at
  `bb19aabd` (`12 passed`). The fixture is a recorded set, not a live measurement, so this
  does not redden a guard — but PR #693's "8 nodes" claim is itself not the live count.
  Recorded here; the baseline bookkeeping belongs to #693, not to this pass.
- **The 10 `test_mission_lifecycle_adapter_contract.py` nodes** are environment-only
  (`node_modules/typescript` absent here). They are not repository debt and were not
  "repaired".
- **Corroboration for PR #688 (not repaired here):** the full-suite run left an untracked
  `data/engineering_lab/agent_events.jsonl` (23 KB) in the tree. It was removed rather than
  committed; the sandboxing repair belongs to #688.


## 7. Next single bounded move

None claimed from this pass beyond human review of this PR. Merge execution, deployment,
and acceptance remain human-only (GOV-03).
