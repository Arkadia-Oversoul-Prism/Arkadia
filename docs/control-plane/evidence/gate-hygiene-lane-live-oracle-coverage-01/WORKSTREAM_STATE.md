# Workstream state — lane live-oracle coverage 01

**Status:** IMPLEMENTED (draft PR open; sovereign review required)
**Branch:** `gate-hygiene/lane-live-oracle-coverage-01`
**PR:** #576 (draft)
**Base:** `main` `36f53be22d753ffe269f05cbf3fb39212f744207` (re-measured before push; unchanged)
**Head:** `178996b48f828f91df794a81e05f534954f3522d`

## Objective (bounded)

Give `scripts/lane_state.py::_pr_state_findings` — the lane guard's live PR-state oracle —
decision-level test coverage. It had none.

## Evidence-backed defect

`--verify-live` is the only half of the lane guard that can see a PR *closed without
merging*, and the only state local git ancestry cannot prove. Coverage existed at the
**wiring** level only: `tests/test_lane_currency_ci_wiring.py` asserts the workflow
invokes the flag, never that the flag decides correctly.

`git grep -n "_pr_state_findings" origin/main -- tests/` → **0 hits**.
No open lane-state PR supplies it (`git grep -l "_pr_state_findings("` empty for #548,
#549, #550, #553, #554, #555, #562, #564, #568, #569, #570, #571, #572, #574, #575).

## Allowed paths (exact)

- `tests/test_lane_instruction_doc_currency.py` (modified — 6 controls appended)
- `docs/control-plane/evidence/gate-hygiene-lane-live-oracle-coverage-01/**` (new)

## Non-goals (explicit)

- Do **not** edit `scripts/lane_state.py`. It is byte-identical to `main`
  (`git diff --quiet scripts/lane_state.py` → clean).
- Do **not** edit lane docs or `lane-state.json` — owned by lanes and by #548 / #555 / #574.
- Do **not** "repair line 4" of any lane doc: the header/`declared_pr` last-wins
  convention is recorded as deliberate in `AGENT-01-SHELL.md`.
- Do **not** repair the snapshot's dead claims (#508, #563) or the dead lane pointers
  (lane 3 → #450 closed, lane 4 → #428 merged). Record only.

## Verification commands and expected outcomes

| command | expected | measured |
|---|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | 55 passed | 55 passed |
| `pytest tests/architecture -q` | 11 passed | 11 passed |
| `python scripts/lane_state.py --check` | exit 0 | exit 0, identical output |
| `python scripts/lane_state.py --verify-live` | exit 1 (pre-existing) | exit 1, 2 DRIFT + 2 NOTE, identical |
| `python -m py_compile api/main.py` | OK | OK |
| CP10 boundary on changed paths | PASS | PASS |

## Negative controls (proven, then restored byte-identically)

1. Swap `MERGED` / `CLOSED_UNMERGED` branches → **3 failed, 40 passed** (exactly the three
   nodes pinning those rows).
2. Transport failure returns `[]` → **1 failed, 42 passed** (fail-closed node).

## Regression boundary

Baseline measured in this pass, not inherited. `+6 passed` = exactly the six added nodes.
No existing node changed state. No test pins a node count for this file.

## Blockers / dependencies

None. `gh` auth verified working this pass (`gh api user` → 200).

## Next permitted action

Sovereign review of #576. Merge is sovereign-only. No further work inside this PR.

## Forbidden actions

Merge, push to `main`, force-push, deploy, mark ready, weaken a test to manufacture green,
reclassify `REGISTERED_ARCHITECTURAL_DEBT`, or edit a lane doc / the snapshot.
