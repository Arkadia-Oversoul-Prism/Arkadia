# Lane 2 — the Opportunity Radar stops claiming a repaired backend defect

**Workstream:** `lane2-opportunity-radar-repaired-claim-01`
**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`, cycle 05
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**Branch:** `lane2/opportunity-radar-repaired-claim-01`
**Scope:** `web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts`
(one doc comment) and `tests/test_prism_opportunity_radar_module.py` (+2 nodes, +1 detector).
No product code, no backend behaviour, no lane snapshot, no lane-instruction doc.
**Authority:** implementation, testing and evidence only. `MERGE_AUTHORITY := NONE`,
`DEPLOY_AUTHORITY := NONE`. No merge, no push to `main`, no deployment, no acceptance.

---

## 1. Reconstructed state at the start of this cycle

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `git rev-parse origin/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` → `false`) | `git rev-parse` |
| open PRs | **30**, every one a draft, every one `MERGEABLE`, 0 reviews | `gh pr list --state open` |
| branch protection / rulesets | none (`/branches/main/protection` → 404; rulesets → 0, as recorded in cycle 04) | REST |
| `api/main.py` | **2597** lines (budget 2600) | `wc -l` |
| console typecheck | `tsc --noEmit` → **exit 0** | `corepack pnpm exec tsc --noEmit` |
| console unit tests | **61 passed** across 8 files | `corepack pnpm exec vitest run` |

## 2. The defect, measured

`opportunityRadarContract.ts` justifies its `offVocabulary` counter with a claim about the
backend, written in the present tense:

```text
* The backend can persist one: `update_entry` validates `status.upper()` but
* writes the value it was sent (`solspire/buyer_recon.py`, MEASURED DEFECT 3).
```

That claim is false on `main`. `solspire/buyer_recon.py::update_entry` normalises into a
local mapping before writing, so validation and persistence agree:

```python
normalized = dict(patch)
status = patch.get("status")
if status is not None:
    status = str(status).upper()
    if status not in STATUSES:
        raise ValueError("invalid status")
    normalized["status"] = status
```

The repair landed in `8f4a6ea0` (`fix(solspire): one combined buyer-recon update_entry
repair (#538 + #544)`) and is pinned by
`tests/test_prism_opportunity_entry_flow.py::test_update_normalizes_a_lowercase_status`,
which carries its own two negative controls. So the console — the one place a *product
reader* meets this defect — was the last surface still asserting it as live.

`offVocabulary` itself is not wrong and is not removed: a row written **before** the repair
can still hold an off-vocabulary value in an existing database, and a direct write that
bypasses the manager can produce one. The defect is the *justification*, not the field.

Measured at `main` `bb19aabd`, the claim was the only instance of its class in the console
source:

```console
$ grep -rn "MEASURED DEFECT\|can persist one" web/arkadia_console/src
…/opportunityRadarContract.ts:244:   * The backend can persist one: `update_entry` validates `status.upper()` but
…/opportunityRadarContract.ts:245:   * writes the value it was sent (`solspire/buyer_recon.py`, MEASURED DEFECT 3).
```

## 3. The change

1. The `offVocabulary` comment now states the measured reality: the write path cannot
   produce an off-vocabulary status (DEFECT 3 repaired, with the pin named), and the
   counter exists for pre-repair rows and direct writes.
2. `tests/test_prism_opportunity_radar_module.py` gains a guard that **binds the claim to a
   measurement of its subject** rather than to prose:
   - `test_off_vocabulary_counter_is_justified_by_the_measured_write_path` sends
     `{"status": "conversation"}` through the real `PATCH …/entries/{id}` route against the
     real manager, asserts the persisted value is inside `buyer_recon.STATUSES`, and then
     asserts the contract module no longer makes the present-tense claim.
   - `test_negative_control_the_claim_detector_flags_the_pre_repair_wording` feeds the
     detector the exact pre-repair sentence and asserts it is flagged.

The detector is module level (`_claims_a_live_off_vocabulary_write`), so the live assertion
and the control exercise the same code — the repository's convention for this file.

## 4. Verification (measured in this environment)

| check | before | after |
|---|---|---|
| `pytest tests/test_prism_opportunity_radar_module.py` | `25 passed` | **`27 passed`** |
| `--collect-only` for that file | 25 | **27** (+2 = the two added nodes) |
| `pytest tests/test_prism_opportunity_radar_module.py tests/test_prism_opportunity_entry_flow.py` | — | **`120 passed`** |
| derived console-contract domain (`pytest $(python scripts/console_contract_domain.py)`) | — | **`2 failed, 1284 passed, 4 skipped`** — the two failures are the `#683` credential-premise pair (§5) |
| `tsc --noEmit` (console) | exit 0 | **exit 0** |
| `api/main.py` | 2597 | **2597** |
| CP10 mutation boundary on the new evidence path | — | **PASS** (`--judge` → exit 0) |

### Live negative control

Restoring the pre-repair wording in the real file, with nothing else changed, reddens
**exactly** the two new nodes and nothing else:

```console
$ pytest tests/test_prism_opportunity_radar_module.py -q      # pre-repair wording restored
2 failed, 25 passed
$ cp /tmp/contract.bak …/opportunityRadarContract.ts           # restored byte-identically
$ pytest tests/test_prism_opportunity_radar_module.py -q
27 passed
```

### The guard is executed by a gate

`tests/test_prism_opportunity_radar_module.py` is inside the derived console-contract
domain (`python scripts/console_contract_domain.py` lists it), which
`.github/workflows/prism-console-contract.yml` executes. No workflow edit is needed.

## 5. Baseline reconciliation — 22 nodes here, 20 recorded by cycle 04

This cycle's full-suite pass on `main` `bb19aabd`:

```console
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
21 failed, 4248 passed, 22 skipped, 6 warnings, 1 error in 301.27s
```

The failing/error set is **22** nodes
(`sha256 828d330f6d73ae7c1ed39bfbf4a3498eba040a1090ab4ce3f57ed720bb673b75`), two more than
cycle 04's 20 at the same SHA. The delta is **ambient credentials, not drift**:

```console
$ pytest tests/test_prism_w4_lab_pr_state.py -q            # this shell carried GH_TOKEN
2 failed, 17 passed
$ env -u GH_TOKEN -u GITHUB_TOKEN -u GITHUB_PERSONAL_ACCESS_TOKEN pytest tests/test_prism_w4_lab_pr_state.py -q
19 passed
```

`api/lab_routes.pr_state` branches on `os.environ.get("GITHUB_TOKEN")`, so with a token in
the shell the handler takes its AVAILABLE branch and the two no-token nodes fail. That class
is owned by open **#683** (`lane4/pr-state-premise-enforcement-01`), whose evidence records
the identical `2 failed / 19 passed` pair. This cycle's measurement independently reproduces
it; it is not branch debt and not a new failure.

The full 22-node set decomposes with no unclaimed, non-reserved defect:

| nodes | count | classification |
|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | sovereign-reserved — CE-01 `weaver.autonomy` collision |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | sovereign-reserved — FINDING F-01 |
| `tests/test_identity_spine_w1.py`, `tests/test_m02_reasomate_truth.py` | 2 | owned by open **#700** |
| `tests/test_m01_persistence.py`, `tests/test_m05_files.py` | 2 | owned by open **#690** |
| `tests/test_solspire_r1_governance_convergence.py` | 2 | owned by open **#693** |
| `tests/test_solspire_r3_execution_runtime.py` | 1 | owned by open **#691** |
| `tests/test_static_ingestion_idempotency.py` | 1 | owned by open **#698** |
| `tests/test_prism_w4_lab_pr_state.py` | 2 | environment — ambient token; owned by open **#683** |
| `tests/test_mission_lifecycle_adapter_contract.py` | 10 | environment — needs `web/arkadia_console/node_modules` |

The last row is measured, not inferred: with `pnpm install` completed in this cycle, the file
is **`10 passed`** (`pytest tests/test_mission_lifecycle_adapter_contract.py -q`), which is why
the derived console-contract domain run above carries no mission-lifecycle failures.

## 6. Recorded, not repaired (separate bounded workstreams)

- **`lane-state.json` records a merged PR under `unassigned_open_prs`.**
  PR **#669** is listed there as open; it merged at `2026-11-20T06:22:32Z`
  (`GET /pulls/669` → `merged: true`) — it is the snapshot-refresh PR that *wrote* the
  snapshot, so the file records its own PR. `scripts/lane_state.py --check` and
  `--verify-live` both exit 0, because `claimed_open_prs()` iterates `open_prs` and
  `deferred_to_pr` only; `unassigned_open_prs` has no reader. This is the recorded
  "a field that is derived and printed but never judged" class, and wiring it would redden
  `main` on each of the 25 currently-unassigned merges, so it is a governance change for a
  separate bounded workstream — not a slice of this one.
- **The remaining non-reserved failing nodes are all owned** by open PRs: #683 (2), #690 (2),
  #691 (1), #693 (2), #698 (1), #700 (2). CE-01 (`weaver.autonomy`) and FINDING F-01
  (`test_no_firebase_persistence_in_gate`) remain sovereign-reserved. The ten
  `test_mission_lifecycle_adapter_contract.py` nodes need `web/arkadia_console/node_modules`
  and are provisioned by the gate.

## 7. Non-goals

- No change to `offVocabulary` behaviour, to `summarize`, or to any surface component.
- No backend change: `solspire/buyer_recon.py` is already correct and is not touched.
- No lane snapshot or lane-instruction doc edit (§6 explains why the snapshot's defect is a
  separate workstream).
- No test weakened or removed; the only test edit is additive.

## 8. Next permitted action

Human review of this draft PR. Merge is human-only under GOV-03. After merge, the next
lane-2 move is the next measured product gap in NovaNet / project Opportunity Radar — not a
second claim-currency guard.
