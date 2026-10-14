# Lane 2 — repair `buyer_recon.update_entry` status normalization (DEFECT 3)

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §7.1.

Bounded objective: repair the status-normalization asymmetry measured in
`prism-opportunity-entry-flow-01` (MEASURED DEFECT 3). Authority: human retains
merge, production deployment, and acceptance. Nothing here claims any of the three.

## Revision binding

- Branch: `fix/prism-l2-buyer-recon-status-normalization-01` (draft PR #538).
- `origin/main` at the start of this pass: `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
  (`Merge pull request #533 from Arkadia-Oversoul-Prism/aeas/engineering-lab-composition-01`).
- Branch head: `4e888421ccdce5c5a45543823b3730c43a5cdebb`.
- A re-fetch of `main` was performed immediately before branching; the earlier
  recorded baseline `f390526ab14e122fef358ef9b9e1cd438509463c` had already moved.

## 1. The defect (measured, not assumed)

`BuyerReconManager.update_entry` validated the status in upper case and then
persisted the raw, as-sent value:

```python
allowed = set(...) - {...}
status = patch.get("status")
if status is not None:
    status = str(status).upper()          # validated in upper case
    if status not in STATUSES:
        raise ValueError("invalid status")
scope = "id=? AND subject_ref=?"
...
for key, value in patch.items():          # ... but `patch` is never reassigned
    if key in allowed:
        current[key] = str(value) if value is not None else ""
```

The `status` local is rebound but discarded; the loop iterates the caller's
`patch`. `create_entry` assigns the upper-cased local into the dataclass, so the
two write paths disagreed. A row could therefore carry a status outside the
declared vocabulary, and any consumer that groups or counts by `STATUSES` — this
radar's own `summarize`, the archived Prism column counts — silently missed it.

Reproduced live before the repair: create stored `UNCONTACTED`; `PATCH
{"status": "conversation"}` answered `200` and stored `"conversation"`, and
`"conversation" in STATUSES` was `False`.

## 2. The repair

Normalise into a local mapping and apply that mapping, leaving the caller's dict
untouched (a caller may reuse it):

```python
normalized = dict(patch)
status = patch.get("status")
if status is not None:
    status = str(status).upper()
    if status not in STATUSES:
        raise ValueError("invalid status")
    normalized["status"] = status
...
for key, value in normalized.items():
    if key in allowed:
        current[key] = str(value) if value is not None else ""
if "evidence" in normalized:
    current["evidence_json"] = json.dumps(normalized["evidence"] or [])
```

Deliberately not changed:

- The vocabulary is **not** widened. A value outside `STATUSES` after upper-casing
  is still refused (`400`), and the refusal does not write.
- No auth, execution, budget, or authority change.
- No new endpoint, route, migration, or column.

## 3. Test change (the pin became a repair assertion)

`tests/test_prism_opportunity_entry_flow.py` previously carried
`test_update_does_not_normalize_a_lowercase_status`, which **asserted the defect**
(`stored == "conversation"`, `stored not in STATUSES`) and told a future reader to
treat a `CONVERSATION` result as "defect 3 was repaired". Leaving that pin in place
would turn the repair red. Per the repository's own convention for repaired
defects (see the board-scope repair), the pin is rewritten:

- `test_update_normalizes_a_lowercase_status` — the repair assertion. The stored
  value is `CONVERSATION` and `in STATUSES`; the response echoes the persisted row.
- `test_negative_control_an_unknown_status_is_still_refused` — normalisation must
  not widen the vocabulary; a non-vocabulary value is `400` and does not persist.
- `test_negative_control_a_raw_off_vocabulary_write_is_detectable` — the invariant
  is not vacuous: writing a raw off-vocabulary row directly makes
  `stored not in STATUSES` true, so the detector is proven to see the shape a
  regression would reintroduce.
- `test_create_normalizes_a_lowercase_status` is retained unchanged as the control
  that the create path already normalised.

## 4. Proof

Targeted, all Lane-2 files that touch the surface:

```
python -m pytest tests/test_prism_opportunity_entry_flow.py \
  tests/test_buyer_recon_board_contract.py \
  tests/test_buyer_recon_router_board_scope.py \
  tests/test_prism_opportunity_radar_module.py \
  tests/test_m03_novanet_public_field.py -q -rEf
-> 105 passed in 7.43s
```

`python -m pytest tests/test_sovereign_field.py -q` -> `2 passed`.

**Live negative control (the guard bites).** Reverting only the repair (loop reads
`patch` again) and re-running the entry-flow file:

```
FAILED tests/test_prism_opportunity_entry_flow.py::test_update_normalizes_a_lowercase_status
E         - CONVERSATION
E         + conversation
1 failed, 49 passed in 3.95s
```

Restored byte-identically, then `50 passed`. A detector that passed on both trees
would be vacuous; this one does not.

`python -m py_compile solspire/buyer_recon.py` -> clean.
`python -m pytest tests/architecture -q` -> `11 passed`.

## 5. Regression boundary — node identity, not counts

Full suite once on the branch
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`):

```
8 failed, 3107 passed, 20 skipped, 2 warnings, 1 error in 215.95s
```

Branch failing/error node set (9 nodes):

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

The two `test_engineering_lab_api.py` nodes are pre-existing drift (the known
`/api/lab/engineering/n-atlas/*` endpoint pins), **not branch-caused**: re-measured
in a `main` worktree at the same revision they fail identically
(`2 failed, 15 passed`) and identically on the branch. All remaining nodes are
recorded baseline debt. No node appears or disappears.

Delta attribution by `--collect-only` on both trees, not by a second full run:

```
MAIN   tests/test_prism_opportunity_entry_flow.py --collect-only -> 48 tests collected
BRANCH tests/test_prism_opportunity_entry_flow.py --collect-only -> 50 tests collected
```

The `+2` is exactly the two new negative controls.

## 6. Remaining uncertainty / not claimed

- The off-vocabulary row is reachable only through the manager/route write path;
  the console `<select>` offers only the declared vocabulary, so it is not
  user-reachable from the current UI. It is repaired because it is a truthfulness
  defect in the store and a direct API caller can produce it.
- Runtime observation of this change is **NOT CLAIMED**. No browser or deployed
  runtime observation was made.
- Production deployment and acceptance are **NOT CLAIMED**. Production
  (`https://arkadia-qzu4.onrender.com`, ADR-016) is not deployed from this branch.

## 7. Next task (one, bounded)

Lane 2's next verified capability remains the `evidence_status` / `evidence`
capture path, gated on an independently verified owner- and board-scoped handler,
as recorded in `prism-opportunity-entry-flow-01` §7. Unrelated to this repair.

## 8. Composition with the other open Lane-2 PR (#492)

The other open Lane-2 PR, #492 (`feat/prism-next7-02-pipeline-strip`), also touches
`tests/test_prism_opportunity_entry_flow.py`, so the composition was measured rather
than assumed.

`git -c user.name=... merge --no-edit acfbf521` onto this branch in a detached
worktree: **clean, zero unmerged files**. On the composed tree:

```
python -m pytest tests/test_prism_opportunity_entry_flow.py -q -rEf
-> 83 passed in 4.49s
```

with the repair assertions among them (9 passed on
`-k "normaliz or defect_3 or off_vocabulary"`).

**Recorded mis-step, so it is not repeated.** An earlier, cheaper probe applied
*only* #492's diff of that one test file and read `7 failed / 37 errors`. That was
not a real conflict: #492's additions depend on frontend files (`ProspectEntryForm.tsx`,
`ProjectOpportunityRadar.tsx`, the `novaNet/**` components) that are absent from a
test-file-only composition, and the diff was taken against a HEAD carrying unrelated
`main` drift rather than against #492's own merge base. A single-file patch is not a
composition; compose the branch and run the tests. `git apply --3way --check` is a
textual check only, and it also passed on the broken probe.
