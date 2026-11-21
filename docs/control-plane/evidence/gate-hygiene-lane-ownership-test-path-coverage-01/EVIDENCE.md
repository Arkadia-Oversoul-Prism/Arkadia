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
