# gate-hygiene / steward-filter-repair-01

**Pass:** Arkadia Weaver hourly bounded execution, 2026-10-09
**Base main:** `24a00f856a0286cbb464a4b585117dd57a2646fa`
**Bounded objective:** repair the three unowned `tests/test_steward_filter.py` failures in
`weaver/filters/steward.py` without widening the filter's intent.

## 1. Selection — why this workstream

Reconstructed live state (all derived from the API at run time, not from prose):

- 16 open PRs. Every non-steward baseline failure node is already owned by an open PR:
  #347 (onboarding), #355 (n-atlas workflow), #356 (lab API), #357 (R1/R3), #361
  (agents-md adjudication), #363 (identity-spine / reasomate), #354 (CP10 allowlist).
  The remaining unowned nodes are the three `test_steward_filter` ones.
- **#364** (`gate10/baseline-fingerprint-ci-wiring-01`) is the concurrent pass, open,
  base `24a00f85`, `mergeable_state: clean`. It wires `scripts/baseline_fingerprint.py`
  into CI. This workstream does not touch `.github/workflows/`,
  `scripts/baseline_fingerprint.py`, or `tests/fixtures/baseline_node_set.txt`, so there
  is no overlap.

## 2. Environment correction (the baseline was polluted)

The environment was missing three dependencies. Their absence produced failures that were
**not repository debt** and must not be recorded as such:

| Missing dep | Symptom | After install |
|---|---|---|
| `google-generativeai` | `ModuleNotFoundError: No module named 'google'` — 9 voice nodes | all pass |
| `pytest-asyncio` | `@pytest.mark.asyncio` unregistered → coroutine never awaited, 3 nodes | all pass |
| (earlier) `pydantic`, `fastapi` | collection errors | resolved |

Measured baseline on `main` `24a00f85` after correction, with the documented invocation
`PYTHONPATH=<repo>/archive/legacy_python pytest tests/ -q -rEf --continue-on-collection-errors`:

```
20 failed, 1767 passed, 23 skipped, 3 warnings, 1 error in 145.46s
```

`-rEf` (not `-rf`) is required so the `ERROR` summary line is emitted; the 1 error is the
known CE-01 `weaver.autonomy` module-vs-package collision, reserved to the sovereign.

## 3. Defect

Three assertions in `tests/test_steward_filter.py` failed because four independent rules in
`weaver/filters/steward.py` were substring-based rather than semantic:

1. **Rule 1 (identity)** — `any(word in text_lower ...)` blocked the bare *mention* of any
   forbidden word. `"You have transcended"` passed only because the list carried
   `"transcendent"` and not `"transcended"` — the assertion was satisfied by a vocabulary
   accident, not by the rule.
2. **Rule 2 (pure symbolism)** — tested `"do" in text_lower`, which matches inside
   `"words"`. A passage was therefore action-grounded if it merely contained `words`.
3. **Rule 4 (mythic inflation)** — `mythic_count > len(text) / 100` is a density of 1%,
   so `"The field resonates. I will do this."` (2 hits / 34 chars) was blocked. The rule
   contradicted the documented intent that mythic language is admitted when action-grounded.
4. **`compress_to_choices`** — iterated `text.split("\n")` and kept whole lines, so a
   non-action sentence sharing a line with a decision point survived
   (`"More noise"` in `"Many words here. Do this. More noise. Quit that. Final thought."`).

## 4. Repair

Rule 1 matches an identity **claim** (subject + copula + predicate, or a possessive such as
`divine authority`). Rules 2/3 match action stems on word boundaries. Rule 4 blocks a
**dominant symbolic density** (> 0.25 of words, minimum 4 words) rather than 1% recurrence.
`compress_to_choices` splits on sentence boundaries before filtering.

Every repair preserves or sharpens the rule it touches; none removes a capability.

## 5. Verification

| Check | Command | Result |
|---|---|---|
| Target tests | `pytest tests/test_steward_filter.py -q` | **12 passed** (8 pre-existing + 4 new pins) |
| Negative control | 14 should-block + 6 should-allow cases | all blocked / all allowed |
| Architecture | `pytest tests/architecture -q` | **11 passed** |
| Full suite (branch) | `pytest tests/ -q -rEf --continue-on-collection-errors` | **17 failed, 1774 passed, 23 skipped, 1 error** |
| Mutation boundary | `cp10_mutation_boundary_policy.py --judge` on changed paths | **PASS** (exit 0) |
| Boot code | `python -m py_compile api/main.py` | compiles; 2462 / 2600 lines (unchanged) |

### Regression delta — node identity, not counts

Sorted `FAILED`/`ERROR` node set, baseline vs branch:

```
19,21d18
< tests/test_steward_filter.py::test_allows_mythic_with_action
< tests/test_steward_filter.py::test_blocks_identity_claims
< tests/test_steward_filter.py::test_compress_to_choices
```

Baseline 21 nodes → branch 18 nodes. The delta is **exactly** the three repaired nodes;
**zero** nodes were introduced. The `+7 passed` is 3 repaired + 4 new pins.

The four new pins cover the semantics the repair introduces, so a later substring
regression reddens them rather than passing silently:
bare-mention-is-not-a-claim, claim-with-intervening-words, action-requires-a-word-boundary,
and symbolic-density-is-what-blocks.

## 6. Authority boundary

Read-only reconstruction, source repair, tests, branch, and PR only. **No merge, no push to
`main`, no force-push, no workflow or governance change, no authority-path change.**
`AGENTS.md` is deliberately not modified: six open PRs already touch it and an append would
create avoidable conflicts.

## 7. Remaining uncertainty

- The 18 remaining baseline nodes are owned by other open PRs and were not touched here.
- The CE-01 collection error is reserved to the sovereign.
- This is a repository-source claim. It is **not** a production-parity claim; no deployment
  or runtime observation was performed in this pass.
