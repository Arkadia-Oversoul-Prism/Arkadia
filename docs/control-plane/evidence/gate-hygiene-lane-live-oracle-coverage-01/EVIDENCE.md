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

## CI attribution — `lane-doc-currency` is red on `main` itself

The `lane-doc-currency` gate runs `python scripts/lane_state.py --check --verify-live`.
On this branch it **fails**, and the failure is **not branch-caused**. Proven by
measurement, not argument:

- A detached worktree at pristine `main` `36f53be2` (verified `git diff --quiet HEAD --
  scripts/lane_state.py`) exits **1** with output **byte-identical** to the branch's
  (`diff /tmp/main_guard.txt /tmp/branch_guard.txt` → identical).
- Both carry the same 2 DRIFT lines (#508 lane 4, #563 lane 3) and 2 NOTE lines.
- The last `main` run, `3a1088c5` (run `40164716935`, success), **predates** `36f53be2`;
  the two later `main` commits moved the snapshot's claims to closed PRs without
  re-pointing them, so the gate reddened on `main` and no PR was needed to cause it.

The diff in this PR touches **no** file the gate reads (`scripts/lane_state.py` untouched;
`tests/` and `docs/control-plane/evidence/` are not guarded paths), so the gate's verdict
is invariant across this change. The repair — re-pointing lanes 3 and 4 and clearing the
stale snapshot claims — is owned by the lanes and by #548 / #555 / #574, and is
**recorded here, not performed**.

Note: `--check` alone exits **0**; it is the `--check --verify-live` combination the
workflow runs that exits 1.

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

## Slice 2 — the read that feeds the oracle (`fetch_pr_records`)

Measured at branch head `ab5be5e7`. Slice 1 pinned every row of the oracle's decision
table, but the **read** that produces the record set had **zero** coverage:
`git grep -n "fetch_pr_records\|_github_token" tests/ --include=*.py` returned **0** hits
on the branch head *and* on `main`. The decision table was judged on a record set no test
ever constructed through the code path that builds it.

The class is the same silent-pass shape one layer further out. `fetch_pr_records` is the
only place the guard talks to an authority, and its docstring names the hazard: a read that
degrades to *empty-but-successful* "would look identical to 'no PRs exist' and pass every
claim". An inversion there reddens nothing.

Nine controls appended (still one file, `tests/test_lane_instruction_doc_currency.py`):

| control | row pinned |
|---|---|
| `..._reads_each_distinct_pr_once_with_an_authorised_get` | positive control; dedupe, sorted walk, `GET` only, bearer header |
| `..._reports_a_non_200_response_as_a_failure` | 200-vs-non-200 gate (`HTTP 404`) |
| `..._reports_an_http_error_as_a_failure` | raised `HTTPError` (`HTTP 403`) |
| `..._reports_a_transport_error_by_type_and_never_raises` | `URLError` named by type, never escapes |
| `..._reports_a_malformed_body_as_a_failure` | 200 with non-JSON body (`JSONDecodeError`) |
| `..._without_a_token_fails_closed_without_a_request` | no credential ⇒ `UNKNOWN`, and **no request issued** |
| `..._never_prints_the_token` | credential hygiene |
| `test_a_partial_read_is_discarded_when_a_later_pr_fails` | the failure dominates a partial read |
| `test_the_failure_classifier_does_not_collapse_to_one_message` | negative control: five modes ⇒ five distinct messages |

`scripts/lane_state.py` is byte-identical to the branch head after the pass
(`git diff --quiet scripts/lane_state.py` → clean). No source, workflow, snapshot, or lane
doc is modified.

### Verification

| command | result |
|---|---|
| `python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **64 passed** (slice-1 baseline 55 → +9 = the nine added controls) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python scripts/lane_state.py --check` | exit **0**, output identical to `main` |
| `python scripts/lane_state.py --verify-live` | exit **1**, 2 DRIFT + 2 NOTE — identical to `main` |
| `printf 'tests/test_lane_instruction_doc_currency.py\n' \| python scripts/cp10_mutation_boundary_policy.py --judge` | exit **0**, mutation boundary PASS |

### Negative controls (the new controls must be able to fail)

Three inversions of `scripts/lane_state.py`, applied in the working tree, run, then restored
byte-identically (`git diff --quiet scripts/lane_state.py` → clean afterwards):

1. no-token branch returns `({}, None)` — a silent pass in the dangerous direction →
   **4 failed, 48 passed**, reddening `..._without_a_token_fails_closed_without_a_request`
   and `test_the_failure_classifier_does_not_collapse_to_one_message`.
2. transport/parse branch returns `(records, None)` → the same run reddens
   `..._reports_a_transport_error_by_type_and_never_raises` and
   `..._reports_a_malformed_body_as_a_failure`.
3. `sorted(set(numbers))` → `numbers` (the dedupe/ordering walk) →
   **1 failed, 51 passed**, reddening
   `..._reads_each_distinct_pr_once_with_an_authorised_get`.

### Regression boundary

Full suite, one pass, `python -m pytest tests/ -q -rEf --continue-on-collection-errors`:
`8 failed, 3469 passed, 20 skipped, 1 error`. The sorted FAILED/ERROR node set is
**identical** to `main` `36f53be2` measured in the same environment (`diff` → empty);
node-set sha256 `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`.
Zero regression; the `+9` is exactly the added controls. All eight failures plus the one
collection error are pre-existing `main` debt and are **not** repaired here.

