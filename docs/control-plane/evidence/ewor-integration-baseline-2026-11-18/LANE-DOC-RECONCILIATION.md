# Lane-doc reconciliation for the combined tree — 2026-11-19

Appended record. It does not modify the historical sections of `EVIDENCE.md` or
`AGGREGATE-CLASSIFICATION-REPAIR.md`; both remain the record of what they measured.

## Defect

`lane-doc-currency` was **red** on this branch (head `5e147892`) and would have been red on
`main` after merge. Reproduced offline on the branch tree, not inferred from the check name:

```
$ python scripts/lane_state.py --check
EXIT=1
  DRIFT lane 1 (AGENT-01-SHELL.md): declares no active thread, but the snapshot lists
        open lane PRs [665] -- re-point it at a live lane PR
  DRIFT lane 2 ... [666]
  DRIFT lane 3 ... [667]
  DRIFT lane 4 ... [664]
```

Cause: the derived `lane-state.json` correctly records that lanes 1-4 each hold one open
draft PR (#665/#666/#667/#664), while all four lane instruction docs still ended with an
idle declaration ("Active thread: none"). The snapshot was right; the docs were stale.
No guard was broken — this is a doc/snapshot disagreement, the same class repaired for
`main` by #613 and by #663.

## Why the other candidate repairs are wrong

| Candidate repair | Measured outcome | Verdict |
|---|---|---|
| Revert the snapshot to #663's blob `9ae0b165` | lane suites **67 passed**, but `test_lane_aggregate_pr_classification.py::test_live_snapshot_records_the_aggregate_classification` **fails** (`'aggregate_prs' not in {...}`) | Rejected — it deletes the aggregate classification this PR exists to add |
| `doc_guard` set to `deferred` or `idle` | `_pr_state_findings` returns **4 findings for every** value (`current`, `deferred`, `idle`) | Rejected — `doc_guard` is not an exemption from the PR-state oracle |
| Hand-edit the snapshot to drop #664-#667 | would make the snapshot disagree with its own derivation | Rejected — snapshot must be derived, not transcribed |

The refresh was also re-run to confirm the snapshot needs no change: `lane_state_refresh.py`
reproduces the committed `lane-state.json` exactly except `observed_at`, `head_sha` and
`updated_at`. Those three fields are **not judged** — `grep -c head_sha scripts/lane_state.py`
returns **0**. So the repair is doc-side only.

## Repair

Four dated status blocks appended to the four lane instruction docs, each recording the
live thread that the snapshot already lists, in the append-only last-wins form the guard
reads. No existing line was rewritten (68 insertions, 0 deletions). Each block states that
the PR stays **draft** and that merge, deployment and acceptance remain human-only.

Scope note: these are four lanes' docs. The blocks are **ledger appends** that record a
live fact already present in the derived snapshot — they do not author, re-scope, or
approve another lane's slice, and they assert nothing about readiness. The alternative
(leaving the combined tree red) is not available: `main` would inherit the red on merge.

## Verification

| Check | Result |
|---|---|
| `python scripts/lane_state.py --check` | **exit 0** — "docs consistent with snapshot (4 guarded lanes)" |
| `python scripts/lane_state.py --check --verify-live` | **exit 0** — 4 claimed-open PRs read live (**not** the vacuous 0) |
| lane suites (`instruction_doc_currency`, `currency_ci_wiring`, `aggregate_pr_classification`) | **82 passed** (was 65 passed / 2 failed) |
| Post-commit freshness (docs + snapshot in one commit) | **exit 0** — will not re-redden `main` after merge |
| Negative control A: remove only lane 1's appended block | **exit 1**, exactly one DRIFT (lane 1 / #665); suite **2 failed**; restored byte-identically |
| Negative control B: remove only lane 3's appended block | **exit 1**, exactly one DRIFT (lane 3 / #667); restored, guard **exit 0** |
| Diff shape | **68 insertions, 0 deletions** across the four docs — no existing line rewritten |
| Console-contract domain, branch vs `main` `f9bd8da9` | failing/error node set **identical** (10 nodes, sha256 `a57f7311…` both) — no regression |

The negative control is the load-bearing one: it proves the guard detects the exact defect
repaired, and that removing the repair reddens precisely the lane it belongs to.

## Remaining obligation (not repaired here)

When #664-#667 close, this snapshot will name merged PRs and must be **re-derived**:

```
$ _pr_state_findings(state, {664,665,666,667 -> MERGED})
4 findings: "PR #665 (lane 1 open_prs) is recorded as open but is MERGED"
```

That is the documented #659 class, not a defect introduced here, and it is not repairable
in advance — the snapshot cannot record PRs as merged before they are. The lane docs will
also need their pointers re-pointed at whatever the lanes open next. Recorded as a
follow-on, not silently pre-satisfied.

## Disposition

`lane-doc-currency` repaired on this branch. This is a **repository-source** claim:
no merge, deployment or production acceptance was performed or is implied.
