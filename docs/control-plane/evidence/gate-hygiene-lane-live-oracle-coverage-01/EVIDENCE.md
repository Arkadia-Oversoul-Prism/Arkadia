# Lane live PR-state oracle — decision-level coverage

Bounded workstream: `gate-hygiene/lane-live-oracle-coverage-01`.
Base: `main` `36f53be22d753ffe269f05cbf3fb39212f744207` (measured this pass).

## Defect

`scripts/lane_state.py::_pr_state_findings` is the **only** half of the lane guard that
can see a PR *closed without merging* — the state a lane instruction most needs to stop
naming, and the one local git ancestry can never prove. It was covered at the **wiring**
level only: `tests/test_lane_currency_ci_wiring.py` asserts that
`.github/workflows/lane-doc-currency.yml` invokes `--verify-live`, never that the flag
**decides** correctly.

Measured across the live corpus: `git grep -n "_pr_state_findings" origin/main -- tests/`
returns **0** hits. No open lane-state PR supplies it either —
`git grep -l "_pr_state_findings(" <pr-N>` is empty for #548, #549, #550, #553, #554,
#555, #562, #564, #568, #569, #570, #571, #572, #574, #575. (#568 mentions the function
in a comment only, in `tests/test_lane_guard_stacked_pr.py`.)

This is the "a surface that computes the right answer and then discards it" class. The
oracle *is* executed by the gate, but an inversion of its decision table reddened no
test.

## Change

One file: `tests/test_lane_instruction_doc_currency.py`. Six controls appended, each
pinning one row of the documented decision table (OPEN / MERGED / CLOSED_UNMERGED /
UNKNOWN-absent / UNKNOWN-transport / `deferred_to_pr`), plus a positive control that
requires the oracle to be **silent** for a genuinely open PR — without it every finding
assertion below could be a constant.

No source, workflow, snapshot, or lane doc is modified. `scripts/lane_state.py` is
byte-identical to `main` after the pass (`git diff --quiet scripts/lane_state.py` → clean).

## Verification

| command | result |
|---|---|
| `python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **55 passed** (baseline 49 passed → +6 = the six added controls) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python scripts/lane_state.py --check` | exit **0**, output identical to `main` |
| `python scripts/lane_state.py --verify-live` | exit **1**, 2 DRIFT + 2 NOTE — identical to `main` |

### Negative controls (the controls must be able to fail)

Two inversions of `scripts/lane_state.py`, applied in the working tree, run, then
restored byte-identically:

1. Swap the `MERGED` / `CLOSED_UNMERGED` branches of the decision table →
   **3 failed, 40 passed**, reddening exactly the three nodes that pin those rows
   (`..._flags_a_claim_that_is_actually_merged`,
   `..._flags_a_claim_closed_without_merging`,
   `..._judges_a_deferral_owner_not_only_open_prs`).
2. Make a transport failure return `[]` (a silent pass in the dangerous direction) →
   **1 failed, 42 passed** (`..._fails_closed_when_github_cannot_be_reached`).

`git diff --quiet scripts/lane_state.py` → clean afterwards; the shipped tree carries the
tests only.

## Attribution

The `+6 passed` is exactly the six added nodes. No existing node changed state. No test
pins a node count for this file (`grep -rn test_lane_instruction_doc_currency tests/`
returns one filename reference in the wiring guard, no count).

## Boundaries and non-claims

- **Not repaired, recorded.** The live snapshot still carries two dead open-PR claims
  (#508 lane 4, #563 lane 3) and two lanes declare dead pointers (lane 3 → #450 closed,
  lane 4 → #428 merged). Those are snapshot/doc currency defects owned by the lanes and
  by PR #548 / #555 / #574; they are **reported** here, not fixed. The guard's
  `--verify-live` exit 1 is the pre-existing measured state, unchanged by this pass.
- **Not addressed.** The header/`declared_pr` last-wins blind spot (a lane doc's top-of-file
  pointer may name a closed PR while `declared_pr` reads a later, open mention) is a
  separate design question. `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` records the
  last-wins convention as deliberate, so "repair line 4" is **not** the fix and was not
  attempted.
- **Not claimed.** No merge, deployment, production parity, or lane acceptance.
