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

## Slice 2 — the read that feeds the oracle (pass 2)

Measured at branch head `ab5be5e7`, advanced to `eb99f38e`.

Slice 1 covered the **decide** half (`_pr_state_findings`). The **read** half had zero
coverage: `grep -n "fetch_pr_records\|_github_token" tests/ --include=*.py` → **0** hits,
on this branch head and on `main`. The decision table was therefore judged on a record set
no test ever built through the code path that produces it.

The class is the silent-pass shape one layer out, and `fetch_pr_records`'s own docstring
names it: a read degrading to *empty-but-successful* "would look identical to 'no PRs
exist' and pass every claim". Nine controls appended to the same single test file
(non-200 / raised `HTTPError` / transport-by-type / malformed body / absent credential /
credential hygiene / partial-read dominance, plus a positive control for the authorised
GET-dedupe-sorted walk and a negative control requiring the five failure modes to remain
distinct messages). `scripts/lane_state.py` byte-identical afterwards.

Measured: slice-1 baseline **55 passed** → **64 passed** (+9 = exactly the added nodes).
Architecture **11 passed**. `--check` exit 0; `--verify-live` exit 1 with 2 DRIFT + 2 NOTE,
identical to `main`. CP10 mutation-boundary judge on the touched path → exit 0, PASS.

Negative controls (guard mutated, run, restored byte-identically):
no-token → `({}, None)` and transport/parse → `(records, None)` ⇒ **4 failed, 48 passed**;
`sorted(set(numbers))` → `numbers` ⇒ **1 failed, 51 passed**.

Regression: full-suite FAILED/ERROR node set **identical** to `main` `36f53be2` measured in
the same environment (`diff` → empty), node-set sha256
`c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`.

### Inherited gate failure — measured, not caused by this diff

At `eb99f38e` the `lane-doc-currency` job runs four steps: three pass (the currency guard,
the wiring guard, and the guard-as-the-gate-executes-it) and only
`Verify lane PR state against GitHub (authoritative oracle)` fails. That step is red on
`main` `36f53be2` for the same reason: the snapshot claims **#508** (lane 4) and **#563**
(lane 3) open while both are closed without merging. This diff touches no file the gate
reads (`scripts/lane_state.py` untouched; `tests/` and `docs/control-plane/evidence/` are
not guarded paths), so the gate's verdict is invariant across it. Re-pointing lanes 3/4 and
refreshing the snapshot is lane-owned work — **recorded here, not performed**.

## Blockers / dependencies

None. `gh` auth verified working this pass (`gh api user` → 200).

## Next permitted action

Sovereign review of #576 at head `eb99f38e`. Merge is sovereign-only. No further work
inside this PR. The lane-doc-currency red is inherited from `main` and is lane-owned;
it is recorded, not repaired here.

## Forbidden actions

Merge, push to `main`, force-push, deploy, mark ready, weaken a test to manufacture green,
reclassify `REGISTERED_ARCHITECTURAL_DEBT`, or edit a lane doc / the snapshot.
