# Lane 2 — discharge the DEFECT 3 claim and audit doc test-node citations

Pass: 2026-11-07. Base: `origin/main` `6c42f55efa1739b3871717fd9ac84605cdac0e15`.
Branch: `feat/prism-l2-doc-task-currency-defect3-01`. Lane: 2.

## 1. What was measured

`AGENT-02-NOVANET-OPPORTUNITY.md:37` recorded, as current truth:

> **MEASURED DEFECT 3 in `solspire/buyer_recon.py` (open, not repaired):** …
> `create_entry` normalizes; `update_entry` does not. Pinned by
> `test_update_does_not_normalize_a_lowercase_status`.

Both halves of that sentence are stale.

**The defect is repaired.** `8f4a6ea0` (`fix(solspire): one combined buyer-recon
update_entry repair (#538 + #544)`) normalises status into a local mapping so validation
and persistence agree (`normalized["status"] = status`; `solspire/buyer_recon.py:333-339`).

Measured on `main` `6c42f55e`, driving the manager directly:

```
create_entry({"status": "UNCONTACTED"})                 -> "UNCONTACTED"
update_entry({"status": "conversation"}, board_id=…)    -> "CONVERSATION"
in STATUSES?                                             True
```

**The cited pin no longer exists.** `grep -rn
test_update_does_not_normalize_a_lowercase_status tests/ --include=*.py` returns nothing.
That merge *deleted* it and replaced it with `test_update_normalizes_a_lowercase_status`
(`tests/test_prism_opportunity_entry_flow.py:919`), because a node that pins a defect is
replaced by that defect's positive form — the two are mutually exclusive. The merge
message says so: "Exactly one node is removed —
`test_update_does_not_normalize_a_lowercase_status`, which pins the defect the [repair]
fixes."

So a successor agent reading the lane doc was sent to re-repair delivered work, and the
citation it was given resolved to nothing.

The repair record already existed at
`docs/control-plane/evidence/l2-buyer-recon-combined-01/EVIDENCE.md`; what drifted was the
instruction doc, which was never re-pointed. The earlier task-currency pass
(`lane-doc-task-currency-01`) discharged three other `AGENT-02` claims and missed this one.

## 2. Why the existing guards did not see it

`scripts/lane_state.py` judges *which PR a doc names* (`check_lane_docs`,
`_declared_pointer_findings`), whether a self-declared idle lane really is idle, and
whether the snapshot is stale against guarded-path movement. It has no notion of whether a
**task or a test node** a doc cites still exists. A doc can be green on every currency
check while instructing a successor to resume finished work.

## 3. Change

Two files, one bounded slice.

**`AGENT-02-NOVANET-OPPORTUNITY.md`** — the DEFECT 3 paragraph is corrected in place,
dated by the merge that repaired it, and carries the supersession explicitly. Its heading
changes from "open, not repaired" to "REPAIRED". The predecessor pin is *named* in the
prose without backticks, deliberately: the new audit flags any backticked `test_…` token
that no module defines, so a bare mention is the only way to record a deleted node's name
without the record becoming the defect.

**`tests/test_lane_instruction_doc_currency.py`** — a citation audit over the lane docs,
derived from the snapshot's own doc list:

| helper / test | property |
|---|---|
| `_node_names_in_file` | node names **parsed with the AST**, so a name in a comment or string is not a node |
| `_test_node_universe` | union across every `tests/test_*.py` |
| `_dangling_citations` | cited name not in the universe |
| `_audited_docs` | derived from `lane-state.json`, not a hand-written list |
| `test_lane_docs_cite_only_test_nodes_that_exist` | the audit, with a corpus-size floor so it cannot pass by finding nothing |
| `test_citation_audit_is_not_trivially_empty_on_the_live_docs` | the live docs really do carry citations |
| `test_citation_control_flags_a_planted_dead_citation` | negative control |
| `test_citation_control_is_silent_for_a_real_node` | positive control |
| `test_citation_detector_ignores_names_that_are_not_nodes` | comment/string are not definitions |
| `test_citation_audit_covers_every_declared_lane_doc` | the audited set is the declared set |

## 4. Verification at the branch head

```
python -m pytest tests/test_lane_instruction_doc_currency.py -q   -> 55 passed
--collect-only                                                     -> 55 (49 before, +6)
python -m pytest tests/test_lane_currency_ci_wiring.py -q          -> 12 passed
python -m pytest tests/architecture -q                             -> 11 passed
python scripts/lane_state.py --check                               -> exit 0
python scripts/lane_state.py --check --verify-live                 -> exit 0
printf '<changed paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
                                                                   -> PASS (exit 0)
```

### Live negative control (on the real document, not a synthetic fixture)

Restoring the backticks around the deleted pin on the actual `AGENT-02` line reddens
**exactly one** node:

```
FAILED tests/test_lane_instruction_doc_currency.py::test_lane_docs_cite_only_test_nodes_that_exist
1 failed, 54 passed
```

Restored byte-identically (the file is back to the committed blob) and the suite returns
`55 passed`. A control that reddened on nothing, or on everything, would be measuring the
wrong thing.

## 5. Baseline

Full suite once at `main` `6c42f55e`, this environment, with `requirements.txt` and the
console toolchain installed:

```
10 failed, 3982 passed, 18 skipped, 3 warnings, 1 error in 266.12s
failing/error node set: 11 nodes
sha256 b498d456b85a413aeb3d6d1b87db17c3030af6d1c42fc8d310afb2f8d9da96b7
```

The single collection error is the pre-existing CE-01 `weaver.autonomy` module-vs-package
collision (`ERROR tests/test_autonomy.py`), reserved to the sovereign. None of the 11
nodes is in a lane-owned file. This branch adds no node to that set: it changes one lane
doc and one test file, and its +6 nodes are accounted for above by `--collect-only`.

Environment note, so a later pass is not misled: the derived console-contract domain
reports `1133 passed` **with** `web/arkadia_console/node_modules` installed and `10 failed`
(one file, `test_mission_lifecycle_adapter_contract.py`) without it. That is a missing
toolchain in the sandbox, not repository debt — both trees agree.

## 6. Boundaries observed

No backend code, console source, shared endpoint/type registry, authority surface, or
deployment configuration is touched. No merge, deployment, or acceptance claim. `#631`
(Lane 1) was **not** merged or marked ready — this session is `IMPLEMENTATION_AGENT :=
OPENHANDS`, which holds no merge authority under GOV-01 §9 / `AGENTS.md`, and `#631` is
still a draft; both facts are for the Weaver/human sovereign, not this agent.

Paths changed: `docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`,
`tests/test_lane_instruction_doc_currency.py`, and this record. All three are Lane 2's (the
lane doc) or the lane-currency shared guard it is judged by; `SHARED-CONTRACTS.md` §1
assigns `AGENT-02` to workstream 2 and the lane instruction docs to their lanes.

*This record was created by an AI agent (OpenHands) on behalf of the user.*
