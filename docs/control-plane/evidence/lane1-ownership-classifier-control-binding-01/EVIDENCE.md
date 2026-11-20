# EVIDENCE — lane 1: bind the surface-ownership classifier to a control

**Pulse:** Weaver hourly bounded execution, 2026-11-20T07:06Z
**Base:** `main` `4b91c2f416a104589283c3846a0766e252a08900` (PR #670)
**Branch:** `lane1/ownership-classifier-control-binding-01`
**Lane:** 1 (shell / navigation / design system / integration seam)
**Owned paths touched:** `tests/test_console_legacy_route_coverage.py` (lane-1 owned per
`SHARED-CONTRACTS.md` §1 and `scripts/lane_state_refresh.py::LANE_OWNERSHIP`), this
evidence record.
**Disposition:** IMPLEMENTED. Merge execution is human-only (GOV-03); this PR stays draft.

---

## 1. Defect — a classifier that answers `True` made two assertions vacuous

`test_every_non_map_inbound_path_has_a_reconciliation_disposition` carries two
`== []` assertions, and **both** are decided by one helper:

```python
unaccounted = sorted(p for p in inbound if ... and not _claimed_by_a_declared_surface(p, declared_paths))
assert unaccounted == [], ...

fell_through = sorted(p for p, target in resolved.items()
                      if not _claimed_by_a_declared_surface(target, declared_paths))
assert fell_through == [], ...
```

A classifier that returns `True` unconditionally satisfies both. Measured at `main`
`4b91c2f4` by replacing the body of `_claimed_by_a_declared_surface` with
`return True`:

```
MUTATION A (classifier neutered to `return True`):  19 passed in 1.54s
MUTATION B (classifier neutered to `return False`): 1 failed, 18 passed in 1.54s
```

The asymmetry is the defect. `return False` is caught (it reports every path as
unaccounted). `return True` — the *silent-pass* direction — was not caught by any node
in the module. That is the direction that matters: a path resolving outside every
declared surface, or an archive inbound path with no disposition, would read as
accounted while the guard judged nothing.

The existing control `test_detector_flags_a_legacy_path_that_falls_through_to_home`
(module line 863) proves the **resolver** can see a fall-through, and its docstring says
so. It never calls `_claimed_by_a_declared_surface`, so it cannot bind the classifier.

### Why this is the same defect class as #670, in a file #670 did not touch

PR #670 repaired exactly this shape one function away — `_pathname_parsers` held inline
was replaced by a module-level helper that a control calls in both polarities. The
classifier here was module-level already, so the *relocation* half was done; the
*binding* half was not. A scan of every `_`-prefixed helper taking a `sources`/`text`-like
argument across `tests/test_console_*.py` for "called from no control test" returned 11
modules; this helper was then confirmed disarmable by constant substitution, which the
call-graph scan alone does not prove.

---

## 2. Repair

One new test, `test_detector_flags_a_path_outside_every_declared_surface`, binding the
classifier in **both polarities**, plus a docstring on the helper recording the measured
defect so the next reader does not delete the control as redundant.

- Positive: `/solariun` (a declared root) and `/solariun/knowledge` (a section beneath it)
  must be owned. The section case is why the helper exists — string equality would report
  every lens path as unaccounted.
- Negative: `/totally-invented`, `/solariunish` (the prefix trap), and `/solspire` (the
  reserved backend namespace the SPA must never claim) must not be owned.

No production source is touched. The detector was already correct; only its binding was
missing.

---

## 3. Proof

### 3.1 The control is decisive under the mutation it exists to catch

```
LIVE (control present, classifier correct):        20 passed in 1.52s
NEUTERED (classifier `return True`):                1 failed, 19 passed in 1.60s
   FAILED ...::test_detector_flags_a_path_outside_every_declared_surface
BARE-PREFIX (`startswith(root)` instead of `root + "/"`): 1 failed, 19 passed in 1.60s
   FAILED ...::test_detector_flags_a_path_outside_every_declared_surface
```

Both mutations redden **exactly** the new control and nothing else, and the file was
restored byte-identically after each. Before the repair, the first mutation produced
19 passed / 0 failed.

The bare-prefix mutation is included because it is a *plausible* rewrite of the helper,
not a synthetic one: dropping the `/` terminator would let `/solariunish` borrow
`/solariun`'s ownership, and the live suite previously had no node that noticed.

### 3.2 Targeted and integration checks

| Check | Command | Result |
|---|---|---|
| Changed module | `pytest tests/test_console_legacy_route_coverage.py -q` | **20 passed** |
| Lane-1 console contracts | `pytest tests/test_console_{legacy_route_coverage,shell_nav_contract,endpoint_registry_contract}.py -q` | **95 passed** |
| Architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| Lane doc currency | `python scripts/lane_state.py --check` | exit **0** |
| CP10 mutation boundary | `printf '<path>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS**, exit 0 |
| Gate domain membership | `python scripts/console_contract_domain.py \| grep -c test_console_legacy_route_coverage` | **1** |

`console_contract_domain.py` already names this file, so the `prism-console-contract`
gate executes the new control with **no workflow edit**.

### 3.3 Delta attribution by node identity

`--collect-only` for this file: **19** on `main` `4b91c2f4` → **20** on the branch.
`+1` is exactly the new control; no existing node was renamed, removed, or re-scoped.

### 3.4 Baseline, measured this pulse

Full suite on `main` `4b91c2f4`, once, with
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

```
19 failed, 4234 passed, 22 skipped, 6 warnings, 1 error in 290.58s (0:04:50)
```

Sorted `FAILED`/`ERROR` node set: **20 nodes**, sha256
`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`. **Zero** of those
nodes are `test_console_*`. The single `ERROR` is the sovereign-reserved CE-01
`weaver.autonomy` module-vs-package collision (`tests/test_autonomy.py`), recorded and not
repaired.

The branch adds one passing node to this file and touches no other file, so the
failing/error node set is unchanged by construction. This is stated as a property of the
diff, not as a second full-suite run — the contract permits one full pass per pulse.

---

## 4. Reconciliation state this pulse

- **Open PRs: 0.** Enumerated via `GET /pulls?state=open` (`per_page=100`), and
  cross-checked against `GET /issues?state=open` filtered to non-PR entries (8 open
  issues, 0 open PRs). There is no eligible merge, no dependency, no repairable PR and no
  justifiable closure. Reconciliation is **exhausted**, so §11 lane new-PR authorization
  applies.
- **`main` CI:** all 5 check-runs `completed/success` at `4b91c2f4`
  (`console-contract`, `boot-syntax`, `test`, `Full-history secret scan`,
  `posture-currency`).
- **N1–N8:** N1 exhausted (above); N2 lane 1 holds no open PR (live re-measured);
  N3 `tests/test_console_legacy_route_coverage.py` is lane-1 exclusive in both
  `SHARED-CONTRACTS.md` §1 and `LANE_OWNERSHIP`; N4 branch from `4b91c2f4`, recorded;
  N5 one bounded slice, one file; N6 no merged or closed thread continues this work;
  N7 targeted tests + negative control + baseline above; N8 no authority, identity,
  governance, approval-enforcement, constitutional or deployment surface touched.

### 4.1 An in-flight human action on an adjacent lane-1 file — recorded, not acted on

At `2026-11-20T06:23:40Z`, 46 seconds after #670 merged, the human sovereign account
created branch `revert-670-lane1/second-router-control-binding-01`
(`3b0aca70`, author `spiralcommand.network@gmail.com`) reverting #670. It has **no open
PR** (`GET /pulls?state=open&head=…revert-670…` → 0).

This slice therefore deliberately does **not** touch `tests/test_console_shell_nav_contract.py`,
which is the one file that revert modifies. #670's own repair was independently verified
sound this pulse — neutering `_pathname_parsers` reddens exactly
`test_detector_flags_a_second_pathname_parser` (`1 failed, 53 passed`), the shape its
commit message claims. Whether to revert it is a human decision and is **not** acted on,
argued, or pre-empted here.

### 4.2 A snapshot field that is written but never judged — recorded, not repaired

`docs/control-plane/parallel-ui/lane-state.json` lists PR **#669** under
`unassigned_open_prs`. #669 merged as `bec86f3d` and that commit **is** an ancestor of
`HEAD` (`git merge-base --is-ancestor bec86f3d HEAD` → true), so a merged PR is recorded
as "unassigned **open**". `grep -rn unassigned_open_prs` finds writers and printers in
`scripts/lane_state_refresh.py` but **no reader** in `scripts/lane_state.py` or its tests.

Wiring that field into a decision changes what the gate judges, so it is recorded here as
a separate bounded workstream rather than repaired inside this slice. Refreshing the
snapshot is also out of scope: `--check` exits 0 and no guarded lane doc changed after
the snapshot was written, so there is no currency defect to repair.

---

## 5. Boundaries

- No merge, no deployment, no acceptance claim. `main` is unchanged by this work.
- No production observation is claimed. The canonical origin is
  `https://arkadia-qzu4.onrender.com` (ADR-016); this change is repository-source only and
  does not reach a running deployment.
- No other lane's file is edited. No workflow is edited.
- `api/main.py` is untouched, so the 2600-line budget and the `py_compile` boot guard are
  not implicated.

## 6. Next permitted action

Human review of this draft PR. Lane 1 then holds no open PR after merge, and its next
bounded slice resumes from the new `main`. The `unassigned_open_prs` defect in §4.2 is the
strongest candidate for a separate gate-hygiene thread, and the `revert-670` branch in
§4.1 awaits a human decision.

### 6.1 Why the lane doc and snapshot were deliberately NOT edited

This slice touches no path under `docs/control-plane/parallel-ui/`, so `lane-doc-currency`
keeps its current green verdict (`--check` exit 0, `--verify-live` exit 0) and the merge
cannot redden `main` after the fact.

That is intentional, not an omission. A lane PR's snapshot is written while its PR is
**open**, so recording that PR under `open_prs` is self-contradicting: the merge closes it
and the snapshot then claims a merged PR is open, which is exactly how #610 and #614
reddened `lane-doc-currency` on `main`. Measured this pulse by driving the live
`scripts/lane_state.py::_pr_state_findings` with a synthetic MERGED record for a real,
present, ancestor merge commit (`bec86f3d`):

```
doc_guard=current   -> ['PR #669 (lane 1 open_prs) is recorded as open but is MERGED (merge commit bec86f3d); re-measure the lane PRs and re-point the lane']
doc_guard=deferred  -> ['PR #669 (lane 1 open_prs) is recorded as open but is MERGED (merge commit bec86f3d); re-measure the lane PRs and re-point the lane']
doc_guard=idle      -> ['PR #669 (lane 1 open_prs) is recorded as open but is MERGED (merge commit bec86f3d); re-measure the lane PRs and re-point the lane']
open_prs=[]         -> []
```

`doc_guard` does not exempt the claim; only `open_prs == []` returns none. The snapshot is
re-derived by the next `lane_state_refresh.py --write` once this PR's fate is known, which
is where its re-measurement belongs.

The control also had to carry the field its classifier reads. Fed a record with
`state: "closed"` but **no** `merged` key, the same call returns a different finding:

```
no `merged` field  -> ["PR #669 (lane 1 open_prs) has an unrecognised live state 'closed'; classified UNKNOWN, not a pass"]
```

Both messages are correct behaviour, but only the first is the control. `pr_status`
consults `record["merged"]` before `record["state"]` because GitHub returns
`state == "closed"` for merged and unmerged alike; a record carrying only `state` is
deliberately classified UNKNOWN. A control that omits the field silently lands on the
UNKNOWN branch and still returns a non-empty finding, so it *looks* like it proved the
defect while proving a different property — read the returned **message**, not its
non-emptiness.


