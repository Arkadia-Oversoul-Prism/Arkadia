# ARK-OPS-CONTINUOUS-001 — cycle 25: the lane snapshot claimed a merged PR was open

**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
**Cycle:** 25
**Measured at:** `main` `cb2841956bcc0397007b9efffbaa8cc6d0801836` (2026-11-26)
**Branch:** `lane2/lane-snapshot-currency-refresh-01`
**Merge execution:** none. Human-only (GOV-03; GOV-04 delegation is not invoked here).

## 1. Reconciliation of the cycle's starting state

Every value below was measured this cycle, not carried forward.

| item | measured |
|---|---|
| canonical `main` | `cb2841956bcc0397007b9efffbaa8cc6d0801836` |
| production `/api/version` | `source_revision` = `cb2841956bcc0397007b9efffbaa8cc6d0801836`, `revision_source` = `RENDER_GIT_COMMIT`, `revision_conflict` = `false` |
| production `/health` | `200` |
| `main` check-runs | `Full-history secret scan` success; `weaver_evolution` skipped. The merge (`#675`) touched only `docs/`, so every path-filtered gate correctly did not run. |
| open PRs | **65** (64 draft, 1 ready, 1 `CONFLICTING`) |
| full suite | `22 failed, 4251 passed, 22 skipped, 1 error` — **23** failing/error nodes |
| architecture suite | **11 passed** |
| CI-wiring guards (console, economic-seam, route-composition, boot-syntax, baseline-fingerprint) | **95 passed** |
| lane currency | `--check` exit 0; `--check --verify-live` exit 0 |
| console declared endpoints vs deployed `/openapi.json` | **45 / 45 served** |
| console declared surface paths served on production | **15 / 15** return the SPA |
| anonymous parameterless `GET` sweep (101 routes) | **1** server error: `/api/codex/github-tree` → `502` |

### The 23 failing/error nodes are fully classified; none is an unclaimed actionable defect

| count | nodes | classification |
|---|---|---|
| 10 | `tests/test_mission_lifecycle_adapter_contract.py` | **environment-only** — `AssertionError: the repository TypeScript compiler is missing at web/arkadia_console/node_modules/typescript/lib/typescript.js`. CI installs it before the suite. |
| 1 | `tests/test_autonomy.py` (ERROR) | **sovereign-reserved** — CE-01 `weaver.autonomy` module-vs-package collision |
| 1 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | **sovereign-reserved** — FINDING F-01, a persistence-boundary decision deliberately left failing; re-pinning would loosen the boundary |
| 11 | `test_gov04_bounded_merge_delegation` (1), `test_solspire_r1_governance_convergence` (2), `test_solspire_r3_execution_runtime` (1), `test_prism_w4_lab_pr_state` (2), `test_m05_files` (1), `test_identity_spine_w1` (1), `test_m02_reasomate_truth` (1), `test_static_ingestion_idempotency` (1), `test_m01_persistence` (1) | **claimed by open PRs** #725, #693, #691, #683, #690, #700, #698 |

Claim status was derived, not assumed: the file list of every open PR was fetched
(`pulls/<n>/files`) and each failing test file was matched against that union. Only
`test_ais_w2_living_gate_grove_handoff.py` and `test_mission_lifecycle_adapter_contract.py`
matched no PR, and both are non-actionable for the reasons above.

### The one production server error is already claimed

```
GET /api/codex/github-tree → 502
{"error":"Client error '401 Unauthorized' for url
 'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1'"}
```

PR #701 (`fix/github-corpus-credential-fallback-01`) claims exactly this defect, with the
same measurement at an earlier revision. It is unmerged, so the defect is still live in
production. Independent reproduction is a corroboration of #701, not a new finding.

## 2. The unclaimed defect: `lane-state.json` lists a merged PR as open

`docs/control-plane/parallel-ui/lane-state.json` on `main` carried:

```json
"unassigned_open_prs": [
  { "number": 669,
    "branch": "gate-hygiene/lane-snapshot-post-integration-refresh-01",
    "head_sha": "32c7b5f991f9b3093197fde1d1db6d73e9ce70de",
    "draft": true, ... }
]
```

Measured live:

```
$ gh pr view 669 --json number,state,mergedAt,headRefOid
#669 state=MERGED mergedAt=2026-11-20T06:22:32Z head=b5b05f294b49d68aaefac9b3e39073e17606cd00
$ git log --oneline --grep="#669" -1 HEAD
bec86f3d fix(lane-currency): re-derive the lane snapshot after the #664-#667 merge wave (#669)
```

The snapshot's `observed_at` is `2026-11-20T04:56:38Z` — **before** #669 merged at
`06:22:32Z`. #669 was the PR whose purpose was to re-derive this snapshot, so the snapshot
recorded its own author as an open PR and was then merged, leaving a false claim on `main`.
This is the self-reference class already recorded for #610/#614, arriving here through the
**unjudged** field instead of `open_prs`.

Two further staleness facts, measured against the live derivation:

- `base_main` is `b842892b9fc64dede5e655db0d293da77248a430`, **12 commits** behind `main`.
- The derivation assigns **13** open PRs to lanes (`[685,692,704]`, `[708]`, `[679,718]`,
  `[680,717,731]`) and **56** to `unassigned_open_prs`; the committed snapshot records
  `0` lane-open and `1` unassigned.

## 3. Why the defect survived: the field has no reader

```
$ grep -rn unassigned_open_prs scripts/ tests/ --include=*.py
scripts/lane_state_refresh.py:19,218,445,553      # writer + printer
tests/                                            # no match
```

`unassigned_open_prs` is written and printed but never judged. Proven as a negative
control on `main`'s own snapshot (with the merged #669 entry still present):

```
$ python scripts/lane_state.py --check
lane instruction docs consistent with snapshot (4 guarded lanes)
EXIT=0
$ python -m pytest tests/test_lane_instruction_doc_currency.py -q
66 passed
```

The gate cannot see the false claim. That blindness — not the single stale entry — is the
load-bearing finding: any future stale entry in this field is equally invisible.

## 4. What was repaired

One entry, in one file: the merged #669 record was removed from `unassigned_open_prs`,
leaving `[]`.

This is a correction toward the file's own derivation, not an independent hand-edit: the
derivation at `cb284195` does not contain #669 (it is merged, so it is not open). The
remaining derivation delta is **not** silently applied — see §5.

Verification:

| check | result |
|---|---|
| `python -c "json.load(...)"` | valid JSON |
| `python scripts/lane_state.py --check` | exit 0, `lane instruction docs consistent with snapshot (4 guarded lanes)` |
| `tests/test_lane_instruction_doc_currency.py` + `test_lane_currency_ci_wiring.py` + `test_lane_aggregate_pr_classification.py` | **93 passed** |
| diff | `1 file changed, 1 insertion(+), 10 deletions(-)` |

## 5. The full re-derivation is blocked, and measured rather than asserted

The obvious repair — re-derive the whole snapshot — was attempted first and **fails**:

```
$ python scripts/lane_state_refresh.py --write --base-main cb284195
wrote docs/control-plane/parallel-ui/lane-state.json      (539 insertions, 23 deletions)

$ python -m pytest tests/test_lane_instruction_doc_currency.py -q
2 failed, 76 passed
  DRIFT lane 1 (AGENT-01-SHELL.md): declares no active thread, but the snapshot lists open
        lane PRs [685, 692, 704] -- re-point it at a live lane PR
  DRIFT lane 2 ... [708]      DRIFT lane 3 ... [679, 718]      DRIFT lane 4 ... [680, 717, 731]
```

A re-derived snapshot is only consistent once **four** lane instruction docs
(`AGENT-01-SHELL.md`, `AGENT-02-NOVANET-OPPORTUNITY.md`, `AGENT-03-SOLARIUN-KNOWLEDGE.md`,
`AGENT-04-ARKANA-WEAVER-LAB.md`) each declare a live lane PR. Those four documents are
owned by four different lanes under `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §1,
so re-pointing all of them is a four-lane edit, not a bounded change. It was reverted
(`git checkout -- docs/control-plane/parallel-ui/lane-state.json`) rather than merged into
this slice.

Consequence, stated plainly: the snapshot remains derived against `b842892b`, still omits
56 unassigned open PRs and 13 lane-assigned open PRs, and `base_main` was deliberately left
unchanged. Changing `base_main` without the full derivation would claim a measurement that
was not made.

## 6. Next permitted action

| item | state |
|---|---|
| current state | `main` `cb284195`; production sha-identical; 65 open draft PRs |
| evidence | this record; negative control in §3; blocked-repair measurement in §5 |
| blocker | the snapshot's lane data can only be re-derived by editing four lane-owned docs |
| authorized action | this one-entry correction, on this branch, as a draft PR |
| forbidden | merge, deployment, protection bypass, re-pointing another lane's doc, wiring `unassigned_open_prs` into the gate |
| completion condition | this record and the one-entry correction reviewed by a human; the full re-derivation scheduled as a four-lane change |

### Proposed separate workstreams (recorded, not executed)

1. **Judge `unassigned_open_prs`.** The field carried a false claim undetected for six days.
   Wiring it into `lane_state.py`'s decision changes what the gate judges, so it is a
   separate bounded change with its own negative control.
2. **Re-derive the lane snapshot** once the four lane owners have re-pointed their docs.
   PR #684 (`gate-hygiene/lane-state-completeness-oracle-01`) is adjacent and open; it
   should be reconciled with this record rather than duplicated.
3. **Cycle numbering.** PR #746 already carries a cycle-25 record
   (`…-cycle-25-stellar-contract-gate/`), so this record uses a distinct slug. The ledger's
   own "Known limits" section records that cycle numbers are not authoritative across
   concurrent runners; that remains true and is not repaired here.
