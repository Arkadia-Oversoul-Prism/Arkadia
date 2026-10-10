# gate-hygiene — CP10 enforcement-cluster composition measurement (01)

Status: EVIDENCE (measurement). Authority required: human merge of this PR only.
No repository behavior is changed by the measurement itself; the harness and its
guard are the durable, re-runnable artifacts.

## 1. Objective (bounded)

The CP10 gate-hygiene line has three open PRs that each edit the **same CP10
enforcement decision surface** and all branch from the current `main`:

- **#354** `gate10/cp10-allowlist-deploy-surface-01` — admits the tracked
  `deploy/` surface to the CP10 allowlist.
- **#388** `gate10/cp10-enforcement-step-truthfulness-01` — pins the CP10
  enforcement step's `steps.<id>.outcome` truthfulness in
  `tests/test_m02a_ci_gate_integrity.py`, rewrites the enforcement block.
- **#390** `gate-hygiene/ci-gate-trigger-coverage-02` — adds a
  `steps.trigger_coverage.outcome` assertion **into the same enforcement block**
  in `.github/workflows/sg-02-fe-2-v.yml` and adds
  `tests/test_ci_gate_trigger_coverage.py`.

The decision question is specific and previously unmeasured: **do #388 and #390
compose into one tree without a semantic collision?** #390 inserts an assertion
into the exact workflow block #388 pins. A textual-only check answers neither
"which paths do they share" nor "what does the composed tree actually do".

Deliverable: a reproducible measurement **plus** a reusable harness so the next
composition claim is one command, not a hand-run again.

Non-goals: repairing `deploy/` (#354 owns it), repairing any baseline node,
merging, or widening to other PR pairs.

## 2. Base and inputs (observed)

- `BASE_MAIN` = `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` (`origin/main`, local
  `main` identical, after `git fetch --all --prune`).
- PR #388 head = `63b3ce9b7c643f99ffe3d5a776a0e7fc99ea3408` (base `f9ced6b6`).
- PR #390 head = `277585512ead857f4855b20594c52403edba7ff1` (base `f9ced6b6`).
- Environment: python 3.13.15, pytest 9.1.1, git 2.47.3, `pyyaml` +
  `pytest_asyncio` present, non-shallow clone. Runnable here (the contract's
  `vite_build := environment-blocked` note concerns the frontend, not this work).

## 3. Method (real merge, not a patch apply)

A `git apply --3way` proves *no textual conflict*. It does not perform the merge
Git would, and it cannot report which paths the two branches share. This pass uses
a **real `git merge` in an isolated worktree**, in **both orders**, and compares
the composed **tree object id** (a byte identity, not a patch identity).

```
python scripts/compose_pr_pair.py pr/388 pr/390 --repo .
```

## 4. Result

```
refs        : pr/388 x pr/390
merge base  : f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8
overlap     : 1 path(s)
              AGENTS.md
forward     : clean=True tree=a0bd8d1ac4fecaed5eb5f0f87428accb1b876ec3
reverse     : clean=True tree=a0bd8d1ac4fecaed5eb5f0f87428accb1b876ec3
order-indep : True
composed    : CLEAN
```

- **Overlap = 1 path** (`AGENTS.md`). It is append-only memory prose; git
  auto-merged it. **This is a disclosure, not a conflict** — the harness reports
  "both touched X" even when the merge is clean, because the semantic-
  compatibility question is a reviewer's, not git's.
- **Order-independent**: forward and reverse merges produce the **identical tree**
  `a0bd8d1a…`. There is therefore no load-bearing merge order between #388 and
  #390.
- The two PRs touch **no** shared *code* surface despite the subject-matter
  overlap: #388 changes only the *test* (`test_m02a_ci_gate_integrity.py`) and
  #390 changes only the *workflow* it pins. The apparent collision is a property
  overlap, not a textual one.

## 5. Composed-tree verification

Composed tree = real merge of `pr/388` + `pr/390` (worktree, both orders).

### 5.1 Targeted

| Test | Composed result |
|---|---|
| `tests/test_m02a_ci_gate_integrity.py` (#388's guard) | **64 passed, 3 failed** |
| `tests/test_ci_gate_trigger_coverage.py` (#390's guard) | **120 passed** |
| `tests/architecture` | **11 passed** |

The 3 failures in `test_m02a_ci_gate_integrity.py` are **only** the pre-existing
CP10 `deploy/` allowlist nodes owned by #354:

```
FAILED test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
```

They fail identically on `main` and are repaired by #354, not by #388/#390.

**Critical interaction check:** #390 inserts `steps.trigger_coverage.outcome`
into the enforcement block #388 rewrites. On the composed tree, #388's
truthfulness pin still passes:
`test_m02a_ci_gate_integrity.py::test_continue_on_error_gates_are_still_enforced_by_outcome`
→ **1 passed**. The inserted assertion does not violate the pin.

### 5.2 Full suite (node-set comparison)

Composed tree, `-rEf --continue-on-collection-errors`:
**15 failed, 1907 passed, 36 skipped, 1 error**.

Failing/error node set (16 nodes):

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
FAILED tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
FAILED tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_compress_to_choices
```

**Composed-tree failing/error node-set fingerprint:**

```
node ids sorted, newline-joined:  6580ebe7dd3c96405b9b8e35fa45b50af12c5a9f61648fa020a8d650e01a3982
node ids, + trailing newline:     bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733
```

The contract's baseline (`6038989` / `804p 54f`) does **not** reproduce on
`f9ced6b6`; this pass re-measured rather than inherit it. The load-bearing fact
is the node **set**, not the counts.

### 5.3 Regression boundary

`main` at `f9ced6b6` was re-measured in this same environment (never inherited
from prose or a ledger): full suite **15 failed / 1838 passed / 36 skipped / 1
error**, failing/error node-set fingerprint **`bfcfe592…`** — the **same 16
nodes, in the same order**, as the composed tree (`diff` of the sorted node lists
is empty).

**Zero regression**: no fixed node, no new node.

The passed-count delta (1838 → 1907, **+69**) is fully accounted for and is
**not** a signal about regression: the two PRs' own guard files collect **+69**
tests (`test_m02a_ci_gate_integrity.py` + `test_ci_gate_trigger_coverage.py`:
118 → 187 collected). The entire delta is new passing tests by construction; none
is a baseline node moving from fail to pass.

## 6. Durable artifact (this PR)

- `scripts/compose_pr_pair.py` — stdlib-only, read-only harness. Real merge in an
  isolated temporary worktree, both orders, tree-id comparison, overlap report,
  non-zero exit on conflict. Never pushes, never touches `main`, never prints a
  token. *(No open PR adds a reusable harness; #375/#376/#377/#391 add evidence
  docs for one specific cluster only.)*
- `tests/test_compose_pr_pair.py` — **6 tests** driving the harness against a
  throwaway repo (no network, no PR refs). Carries **two negative controls**: an
  always-`clean` detector and an always-empty overlap detector would pass naively,
  so the colliding shape is fed in and must be reported. Also pins the CLI exit
  code as a decision gate.
- This document.

### 6.1 This branch's own verification

Measured on the branch head (`main` + the artifacts above), same environment:
full suite **15 failed / 1844 passed / 36 skipped / 1 error** — failing/error
node set **identical to `main`** (fingerprint `bfcfe592…`). The `+6` passed over
`main` is exactly this PR's new guard tests. `tests/architecture` **11 passed**;
`scripts/compose_pr_pair.py` and `api/main.py` both `py_compile` clean;
`api/main.py` = **2450** lines (under the 2600 budget). The CP10 policy judge
returns **PASS, rc=0** for the three added paths.

### 6.2 CI-wiring note (not claimed)

Like `tests/test_m02a_ci_gate_integrity.py` (which #388 itself notes is executed
by nowhere), this guard is not named in a workflow trigger path, so it is a
repository convention rather than a CI gate. Wiring it into
`sg-02-fe-2-v.yml` — the workflow whose executed decisions it would then be able
to protect — is left as a **separate proposed bounded task**, because that step's
`steps.<id>.outcome`/`conclusion` semantics are the subject of #388 and must not
be entangled with this measurement PR.

## 7. Remaining uncertainty / what is NOT claimed

- **NOT claimed:** that the composed PR pair should merge, or in what order.
  Merge is the sovereign's decision; this pass measured composition only.
- **NOT claimed:** that #354 composes with #388/#390. #354 was out of scope here;
  its `deploy/n-atlas-server/*` nodes are the pre-existing red on `main`.
- The three `deploy/` nodes remain red on the composed tree. They are owned by
  #354 and deliberately not repaired here (baseline rule).
- `api/main.py` was not touched; the 2600-line budget is unaffected.

## 8. Next permitted action

Human review of this evidence PR. If accepted, the sovereign may then decide the
CP10 cluster order; #388 and #390 are demonstrated order-independent.
