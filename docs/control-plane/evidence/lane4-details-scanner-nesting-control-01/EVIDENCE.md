# Lane 4 — the details scanner's nesting claim was unproven

Bounded lane-4 slice: bind `tests/test_lab_repository_surface_contract.py::_matching_details_close`
to a control in both polarities. Test-side only; no product, authority, routing, or deployment change.

## Base

- Repository `Arkadia-Oversoul-Prism/Arkadia`, canonical branch `main`.
- `BASE_MAIN` = `1bff8c42e78f153203641db6d8a90818f7ff6ab2` (measured live this pulse).
- Branch `lane4/details-scanner-nesting-control-01`, created from that SHA.

## The defect (measured, not inferred)

`_matching_details_close` scans structurally — it counts nested `<details>` elements so the
returned close is the one that actually closes the container. Two tests depend on it through
`_engineering_details_span`:

- `test_repository_context_is_contained_in_the_engineering_details_container`
- `test_mission_workspace_is_the_first_child_of_the_page`

Neither reaches the nesting branch, because the live page holds **exactly one** `<details>`
element:

```
open <details: 1  close: 1
marker at 2334   first close after open: 4471   last close: 4471
```

So `first close == last close == the container's own close`, and the nesting-aware scan is
indistinguishable from a naive `page.find("</details>", open_index)`. The docstring's nesting
claim was asserted, never exercised: a regression to the naive scan reddened nothing.

## The control

Two nodes appended to the same module, both calling the live helper (not a restated predicate):

- `test_the_details_scanner_counts_nesting_rather_than_the_first_close` — feeds a nested
  container and requires the **outer** close; also asserts that a naive first-close scan
  disagrees with the returned index on that page, so the control cannot be satisfied by a
  scanner that ignores nesting.
- `test_the_details_scanner_returns_the_first_close_on_a_flat_container` — the opposite
  polarity, so a scanner that always returned the document's last close cannot pass either.

## Evidence

Targeted proof (same tree, same environment):

| Run | Result |
| --- | --- |
| `pytest tests/test_lab_repository_surface_contract.py -q -rEf` before the change | **13 passed** |
| after the change | **15 passed** |
| live negative control (helper body replaced by the naive first-close scan) | **1 failed, 14 passed** — the failing node is exactly `test_the_details_scanner_counts_nesting_rather_than_the_first_close` |
| restored byte-identically | **15 passed**, `git diff --stat` = 1 file, +43 insertions |

The negative control is the load-bearing measurement: under the naive scan the thirteen
pre-existing nodes stay green, which is precisely the invisibility this slice repairs.

Dependencies were installed once this pulse (`pip install -q -r requirements.txt`); without it
the module's one handler-binding node errors on `httpx`/`cryptography`, which is an environment
gap, not repository debt.

## Boundaries

- Files touched: `tests/test_lab_repository_surface_contract.py` and this evidence file. Both
  inside lane 4's ownership (`SHARED-CONTRACTS.md` §1); no shared shell, routing, token,
  NovaNet, Solariun, or authority surface.
- No product behaviour changed. Read-only surface; no authorize/execute/merge/deploy control.

## Deliberately not done

- **The lane-4 instruction doc and `lane-state.json` were not edited.** Both are guarded paths:
  `scripts/lane_state.py::_freshness_findings` reports a snapshot stale when *any* commit in
  `(base_main, current_main]` touches a guarded lane doc. A lane PR that edits its own pointer
  reddens `lane-doc-currency` on `main` the moment it merges (the #659 / #664 to #669 class), and
  recording this PR's own number in the snapshot is the self-reference defect. The pointer and
  the re-derivation belong to a dedicated lane-currency change after the open lane PRs land.
- `#677`, `#678`, `#679`, `#676`, `#675` were not modified. They are drafts with green checks;
  merge execution is human-only under GOV-03.
