# Lane ownership map omits the lanes' own test files

**Base main:** `4b91c2f416a104589283c3846a0766e252a08900` (2026-11-20)
**Branch:** `gate-hygiene/lane-ownership-test-path-coverage-01`
**Measured:** 2026-11-21

## Defect

`scripts/lane_state_refresh.py::LANE_OWNERSHIP` lists no test path for lanes 2-4 while
lane 1 lists five. Four lane PRs were open at `4b91c2f4`; the derivation assigned three of
them **unassigned**:

```
$ python scripts/lane_state_refresh.py            # pre-repair
lane 1: doc_guard=current  active=#671 open=[671]
lane 2: doc_guard=idle     active=#None open=[]
lane 3: doc_guard=idle     active=#None open=[]
lane 4: doc_guard=idle     active=#None open=[]
unassigned open PRs: [672, 673, 674, 675]
```

A lane thread the currency check cannot see is a lane thread it cannot judge. The lane docs
already name the omitted files as their own work:

- `AGENT-02-NOVANET-OPPORTUNITY.md:292` -> `tests/test_prism_novanet_engagement_readings.py`
- `AGENT-03-SOLARIUN-KNOWLEDGE.md:115` -> `tests/test_knowledge_graph_provenance_boundary.py`

Lane 4's doc does not name `tests/test_arkana_signal_schema_guard.py`; its assignment rests on
`SHARED-CONTRACTS.md` §1 (lane 4 owns Arkana feature-local tests) and on
`.github/workflows/arkana-signal-conformance.yml`, which executes that file.

## Repair (3 inserted paths, 1 script)

```
lane 2 += tests/test_prism_novanet_engagement_readings.py
lane 3 += tests/test_knowledge_graph_provenance_boundary.py
lane 4 += tests/test_arkana_signal_schema_guard.py
```

Post-repair derivation — every lane now sees its own open thread, and the only remaining
unassigned PR is #675, an ops directive document that belongs to no lane:

```
lane 1: doc_guard=current  active=#671 open=[671]
lane 2: doc_guard=current  active=#673 open=[673]
lane 3: doc_guard=current  active=#672 open=[672]
lane 4: doc_guard=current  active=#674 open=[674]
unassigned open PRs: [675]
```

The committed snapshot is **not** re-derived here. It records every lane idle, which is what
the merge wave returns to; re-deriving it now would write a snapshot that reddens
`lane-doc-currency` on `main` the moment each lane PR merges, and would require editing four
guarded lane docs. Currency refresh stays a separate action, taken against the post-merge state.

## Verification

| Command | Result |
|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py -q -rEf` | **60 passed** (55 before; +5 = 4 parametrized + 1 negative control) |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py tests/test_lane_aggregate_pr_classification.py -q` | **87 passed** (82 at `4b91c2f4`) |
| `python scripts/lane_state.py --check` | exit **0** |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | not required — `api/main.py` untouched |

`--collect-only` attributes the delta: 55 -> 60 nodes in the guard file, which is exactly the
five added nodes; the other two lane files are unchanged.

### Live negative control

The ownership map was reverted in the working tree (not in a synthetic fixture) and the guard
re-run:

```
FAILED ...::test_lane_owned_test_file_is_assigned_to_its_lane[2-tests/test_prism_novanet_engagement_readings.py]
FAILED ...::test_lane_owned_test_file_is_assigned_to_its_lane[3-tests/test_knowledge_graph_provenance_boundary.py]
FAILED ...::test_lane_owned_test_file_is_assigned_to_its_lane[4-tests/test_arkana_signal_schema_guard.py]
3 failed, 57 passed
```

Lane 1's parametrization and the negative control stay green under the revert, so the detector
discriminates the three repaired lanes rather than reporting every path. The script was then
restored byte-identically (`diff -q` clean) and the guard returns to 60 passed.

The negative control (`test_unowned_test_file_is_assigned_to_no_lane`) pins the other polarity:
an unowned test path is assigned to no lane, so the matcher cannot pass by admitting everything.

## Scope

Changed paths: `scripts/lane_state_refresh.py`, `tests/test_lane_instruction_doc_currency.py`,
this record. No lane doc, no snapshot, no source module, no authority surface, no deployment
configuration. `api/main.py` untouched.

## Not claimed

- No merge, no deployment, no production acceptance. Under GOV-03 merge execution is human-only;
  this record is eligibility evidence, not authorization.
- The four lane PRs' own test files were **not** proven green in this sandbox:
  `tests/test_arkana_signal_schema_guard.py` and
  `tests/test_knowledge_graph_provenance_boundary.py` fail collection on missing `httpx`/`fastapi`,
  and `tests/test_console_legacy_route_coverage.py` fails 6 nodes on missing `cryptography` — a
  sandbox dependency gap, not repository debt. Their CI evidence is the `console-contract`,
  `conformance`, `test` and `arkana-signal-conformance` checks on each PR.

## Addendum — the inventory gap reappears by composition (PR #680)

Measured 2026-11-21 at `main` `1bff8c42e78f153203641db6d8a90818f7ff6ab2`, with the six open PRs
(#675, #676, #677, #678, #679, #680) composed onto it in a detached worktree: **zero** conflicted
files.

The composed tree reintroduced the defect this PR repairs. `LANE_OWNERSHIP` listed
`tests/test_arkana_signal_schema_guard.py` for lane 4, but lane 4's *open* PR #680
(`lane4/details-scanner-nesting-control-01`, head `0023c781`) adds
`tests/test_lab_repository_surface_contract.py`, which the derivation assigned to **no lane**:

```
tests/test_lab_repository_surface_contract.py -> []
tests/test_console_shell_nav_contract.py      -> ['1']
tests/test_prism_novanet_engagement_readings.py -> ['2']
tests/test_knowledge_graph_provenance_boundary.py -> ['3']
```

No single PR could observe this: #676 measured its inventory before #680 opened, and #680's own
branch does not carry #676's map. It is the composition hazard already recorded for content-derived
gate domains — the branch that adds a member cannot validate the domain it joins.

Repair (both inside this PR's declared objective, "assign the lanes' own test files to their lanes"):

1. `tests/test_lab_repository_surface_contract.py` added to lane 4's paths.
2. The pinned `LANE_TEST_PATHS` dict updated to the lane-4 path that actually exists on the
   composed tree.
3. A **derived** guard added so a *newly added* map entry cannot escape the same assertion:
   `_declared_lane_test_paths()` reads every `tests/` path the map declares, and
   `test_every_declared_lane_test_path_is_assigned_to_its_lane[lane]` requires each to classify to
   its own lane. A hand-maintained list in one place drifts; a derivation cannot.
4. A floor, `test_every_lane_declares_at_least_one_test_path`, so the derivation cannot be emptied
   into vacuity, plus `test_the_floor_bites_on_a_lane_with_no_test_path` proving the floor predicate
   reports a lane carrying only product paths.

After the repair, on the same tree: `tests/test_lab_repository_surface_contract.py -> ['4']`.

### Negative controls (live, on the real files)

- Remove the added lane-4 line from `scripts/lane_state_refresh.py` →
  `1 failed, 3 passed`, failing exactly
  `test_lane_owned_test_file_is_assigned_to_its_lane[4-tests/test_lab_repository_surface_contract.py]`.
- Declare a lane-1-owned test under lane 2 →
  `2 failed, 2 passed`, failing
  `test_every_declared_lane_test_path_is_assigned_to_its_lane[1]` and `[2]` — the derived guard
  discriminates a cross-lane declaration rather than reporting everything.
- Both files restored byte-identically (`sha256sum -c` OK).

### Measured on this branch

- `tests/test_lane_instruction_doc_currency.py` **66 passed** (60 before this addendum; `+6` = 1
  floor test, 1 floor control, 4 derived parametrizations).
- `tests/test_lane_instruction_doc_currency.py` + `tests/test_lane_currency_ci_wiring.py`
  **78 passed**; `tests/test_lane_aggregate_pr_classification.py` **15 passed**.
- `python scripts/lane_state.py --check` → exit **0**.
- `tests/architecture` **11 passed**.
- Composed tree (#675–#680 in a worktree): touched test files **178 passed**, architecture
  **11 passed**, composition-hazard guards (`test_m02a_ci_gate_integrity`,
  `test_prism_console_ci_wiring`, `test_economic_seam_ci_wiring`, `test_lane_currency_ci_wiring`,
  `test_ci_gate_trigger_coverage`) **242 passed**.

### Not claimed

- No merge, no deployment, no acceptance. GOV-03: merge execution is human-only; this is
  eligibility evidence.
- The console frontend was not rebuilt locally for #679; its `frontend` CI job passed at that head.

## Addendum 2 — composed-tree verification, and the sandbox gap closed (2026-11-22)

Measured 2026-11-22T01:0x at `main` `1bff8c42e78f153203641db6d8a90818f7ff6ab2` with this branch's
head `529e4e94` and the other five open PRs (#675, #677, #678, #679, #680) merged into a detached
worktree in that order. **Zero conflicted files.**

| Command (composed tree) | Result |
|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_prism_novanet_engagement_readings.py tests/test_console_shell_nav_contract.py tests/test_knowledge_graph_provenance_boundary.py tests/test_lab_repository_surface_contract.py -q` | **184 passed** |
| `pytest tests/test_m02a_ci_gate_integrity.py tests/test_prism_console_ci_wiring.py tests/test_economic_seam_ci_wiring.py tests/test_lane_currency_ci_wiring.py tests/test_ci_gate_trigger_coverage.py tests/architecture -q` | **253 passed** (architecture **11 passed**) |
| `python scripts/lane_state.py --check` | exit **0** |

Re-proved the live negative control on this head (`529e4e94`): removing the lane-4
`tests/test_lab_repository_surface_contract.py` line from the real `scripts/lane_state_refresh.py`
yields `1 failed, 65 passed`, failing exactly
`test_lane_owned_test_file_is_assigned_to_its_lane[4-tests/test_lab_repository_surface_contract.py]`;
restoring the file byte-identically returns `66 passed` with a clean `git status`.

### Supersedes the earlier dependency limitation

The first "Not claimed" bullet in this record reported that the four lane PRs' own test files could
not be run in the sandbox for want of `httpx`/`fastapi`/`cryptography`. That was a sandbox gap, and
it is now closed: after `pip install -q -r requirements.txt` each lane PR's targeted file was
measured **on its own head**, and every count matches the number its own evidence records.

| PR | head | targeted file | measured |
|---|---|---|---|
| #677 | `8352c095` | `tests/test_prism_novanet_engagement_readings.py` | **17 passed** |
| #678 | `b9b910af` | `tests/test_console_shell_nav_contract.py` | **55 passed** |
| #679 | `a9bef9aa` | `tests/test_knowledge_graph_provenance_boundary.py` | **31 passed** |
| #680 | `0023c781` | `tests/test_lab_repository_surface_contract.py` | **15 passed** |

### Not claimed

- No merge, no deployment, no acceptance. GOV-03: merge execution is human-only; this is
  eligibility evidence.
- This addendum commit touches only this evidence file. The composition above was measured at
  `529e4e94`; the code under test is unchanged by the addendum.
