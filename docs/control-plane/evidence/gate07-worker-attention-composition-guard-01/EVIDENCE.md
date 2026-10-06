# GATE-07 · Worker→attention composition seam — a clean hourly stop is composed into a pushed block

**Workstream:** hourly bounded-execution loop repair (scheduler → trajectory → router → worker → attention)
**Gate:** GATE-07 (durable Weaver loop)
**Status:** IMPLEMENTED (repository-source proof; not a production claim)
**Base main:** `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd`
**Branch:** `gate07/worker-attention-composition-guard-01`
**Change class:** test-only guard (no production code, no authority, no mutation path)

## 1. Defect

The two halves of the hourly stop are already pinned, and neither pins the seam between
them:

- `tests/test_engineering_router_status_truthfulness.py` (PR #322) proves the router
  *names* an unrecognized move status instead of silently skipping it.
- `tests/test_attention_truthfulness.py` (PR #323) proves
  `build_engineering_attention_event` *classifies* `NO_LEGAL_MOVE`-with-blockers as a
  pushed HIGH `WEAVER_BLOCKED`.

PR #323 introduced this distinction deliberately — `weaver/attention_bus.py:264`:

```python
return status == "NO_LEGAL_MOVE" and bool(result.get("blockers"))
```

That predicate can only ever see `NO_LEGAL_MOVE` **with** blockers, because
`weaver/engineering_router.py:158` appends a blocker unconditionally when no move is
routable:

```python
    if not blockers:
        blockers.append("no legal pending move (all complete or dependencies unresolved)")
    return None, blockers
```

So the router emits a non-empty blocker list on **both** a genuine clean completion and a
structural block. The predicate is therefore always true for `NO_LEGAL_MOVE`, and every
composed `NO_LEGAL_MOVE` becomes `WEAVER_BLOCKED` / `HIGH` / push.

This contradicts the scheduler, which treats `NO_LEGAL_MOVE` as a **clean stop/success**
(`.github/workflows/arkadia-engineering-scheduler.yml:108`: only `FAILED` exits 1). The
hourly loop would push a HIGH false alert on every idle session.

## 2. The seam, and why the half-guards miss it

| layer | pinned by | what it proves |
| --- | --- | --- |
| router names the defect | `test_engineering_router_status_truthfulness.py` | a blocker string is produced |
| attention classifies a blocker | `test_attention_truthfulness.py` | `NO_LEGAL_MOVE`+blockers → HIGH push |
| **worker composes the two** | **unpinned before this PR** | — |

`EngineeringWorker.run()` (`weaver/engineering_worker.py:69,99`) is what the scheduler
actually invokes; it calls `_record_attention` → `build_engineering_attention_event` and
projects the event onto the result and the outbox. The chain could break at that seam
(worker not calling the builder, not recording, not projecting) while both half-guards
stayed green. It is also where the two halves disagree.

## 3. Measured before the repair (base `4587890`)

Driven through `EngineeringWorker.run()` with a synthetic trajectory in a `tmp_path`
sandbox:

```
terminal-only  {DONE: completed}                    -> NO_LEGAL_MOVE  blockers=['no legal pending move …']
                                                       attention_event=WEAVER_BLOCKED sev=HIGH push=True
unrecognized   {F-A: merged_acceptance_pending}     -> NO_LEGAL_MOVE  blockers=['unrecognized move status: …']
                                                       attention_event=WEAVER_BLOCKED sev=HIGH push=True
routable       {NEXT: pending}                      -> READY_FOR_REVIEW
                                                       attention_event=… human_authority_required=True
```

Row 1 is the defect: a genuine clean completion composes into a pushed HIGH block.
Underlying assertion failure (`tests/test_worker_attention_composition.py:152`):

```
AssertionError: assert 'WEAVER_BLOCKED' == 'WEAVER_STATE_CHANGED'
```

## 4. Change

`tests/test_worker_attention_composition.py` — test-only. Five tests drive the real
`EngineeringWorker.run()` against a synthetic trajectory written under `tmp_path` (the
repository tree is never touched; the outbox resolves to `tmp_path/docs/control-plane/…`):

| test | role |
| --- | --- |
| `test_unrecognized_frontier_is_composed_into_a_pushed_block` | the live G12-A/G12-C shape survives the seam into a pushed block |
| `test_composed_block_is_durable_in_the_outbox` | the event is recorded per channel, not merely returned in memory |
| `test_clean_completion_stays_quiet_through_the_worker` | **strict xfail** — the recorded defect |
| `test_routable_move_still_reaches_the_review_boundary` | ordinary routing unchanged; no merge/deploy |
| `test_negative_control_seam_detector_flags_a_worker_that_skips_the_builder` | the detector fails on a worker that never consults the builder |

The xfail is `strict=True`, so it flips to a **failure** the moment the router's blockers
contract is repaired — the pin cannot be disarmed by leaving it green.

## 5. Why the repair is not in this PR

Repairing the defect requires changing `select_next_move` to distinguish "nothing to
route, nothing wrong" from "nothing to route *because* something is wrong" — i.e. a
change to the router's `blockers` contract, consumed by `_engineering_result_is_blocked`
and by the router's own status-truthfulness pins. That is a separate bounded workstream
with its own regression boundary. This PR records the defect and pins the seam; it does
not widen scope to repair it.

## 6. Verification

```
tests/test_worker_attention_composition.py                             4 passed, 1 xfailed
  + tests/test_engineering_router_status_truthfulness.py
  + tests/test_attention_truthfulness.py                              22 passed, 1 xfailed
python -m pytest tests/architecture -q                                11 passed
```

Full suite, `-rEf --continue-on-collection-errors`, guard present vs. moved aside:

```
guard present : 10 failed, 1589 passed, 20 skipped, 1 xfailed, 1 error
guard absent  : 10 failed, 1585 passed, 20 skipped,          1 error
fingerprint (both): outcomes f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48
                    ids      92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413
failing/error nodes: 11 (10 failed, 1 error) — identical set on both sides
```

Zero failing/error **node-set** delta. The `+4 passed` is exactly the four non-xfail
guard tests; the xfail is a fifth node, counted separately. Pre-existing debt
(unattributed to this change):

```
ERROR  tests/test_autonomy.py                                    (CE-01 module-vs-package collision, reserved to sovereign)
FAILED tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_compress_to_choices
```

`python -m py_compile` is not required (no boot code touched); the guard imports
`weaver.engineering_worker` only.

## 7. Boundary

Test-only. No production module, no authority path, no mutation path, no merge/deploy
surface. The guard writes only inside `tmp_path`; the repository tree is untouched
(`git status --porcelain` → the single untracked test file). `docs/control-plane/evidence/attention-events.jsonl`
is pre-existing and gitignored (`.gitignore:71`).

## 8. Next bounded task

Repair the router's `NO_LEGAL_MOVE` blockers contract so a clean completion carries no
blocker, then remove the strict xfail. That is a separate workstream and requires
sovereign authorization to change a contract consumed by two existing test files.

## 9. CI wiring (added in pass 2 of this workstream)

The gap recorded by `fcdfa1a` is closed inside this same PR: the seam guard and the
attention half-guard now run in `weaver-mvp2-validation.yml`, the workflow that already
owns the router half-guard.

| change | file |
| --- | --- |
| `tests/test_attention_truthfulness.py` + `tests/test_worker_attention_composition.py` added to **both** the `push` and `pull_request` path filters | `.github/workflows/weaver-mvp2-validation.yml` |
| new step `Worker→attention composition seam guard` executes both files on every event | `.github/workflows/weaver-mvp2-validation.yml` |
| `test_guard_is_selected_and_executed_by_a_workflow` pins the above | `tests/test_worker_attention_composition.py` |

The self-guard is the same pattern the router half-guard uses (PR #322): it asserts both
files appear in the `push` **and** `pull_request` filters, that the two filters are
identical sets, and that both files are named in the seam-guard run step — a guard that
is merely *triggered* but not *executed* is decoration.

Negative controls, each measured by mutating the workflow and reverting:

```
remove the seam-guard entry from the pull_request filter only
  -> FAILED … "pull_request filter does not select tests/test_worker_attention_composition.py"
rename the run step
  -> FAILED (step not found)
drop the file from the run step's pytest argument list
  -> FAILED ("the seam guard step does not execute …")
```

All three fire; the detector is not vacuous. Re-measured after the wiring:

```
guards + injection boundary + architecture          47 passed, 1 xfailed
python -m pytest tests/architecture -q              11 passed
full suite, -rEf --continue-on-collection-errors    10 failed, 1590 passed, 20 skipped,
                                                    1 xfailed, 1 error
fingerprint (identical to §6)                       outcomes f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48
                                                    ids      92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413
```

The `+1 passed` over §6 is exactly the new self-guard node; the failing/error node set is
unchanged, so the wiring is regression-free. `api/main.py` is untouched (2432 lines);
`python -m py_compile api/main.py` passes; CP10 boundary judge PASS on the changed paths.

Boundary note: this edits a CI workflow, which §8 of pass 1 had classified as a distinct
surface. It is a bounded, in-workstream change — the workflow that already owns the router
half-guard gains the seam and attention halves, with no new authority or mutation path —
and it is recorded here rather than silently folded in.

### 9.1 Runtime observation of the wired guard (pushed head `a8692c1`)

The wiring above was verified against the live workflow run, not inferred from the file.
Head `a8692c1` was pushed to `gate07/worker-attention-composition-guard-01` and GitHub
Actions selected and executed the guard:

```
run 37444445640   Weaver MVP2 validation   a8692c10   completed success
  job mvp2-validation  completed success
    step 8  Engineering-router status truthfulness guard      -> success
    step 9  Worker→attention composition seam guard           -> success
    log: python -m pytest -q tests/test_attention_truthfulness.py \
                             tests/test_worker_attention_composition.py
         14 passed, 1 xfailed in 0.22s
run 37444445553   security-secret-scan       a8692c10   completed success
check-runs         Vercel Preview Comments                success
```

The run was triggered **by the new `pull_request` path filter** (the previous head
`fcdfa1a` produced no `mvp2-validation` run), which is direct evidence that the filter
selects the guard and that step 9 executes it. This converts the pass-1 finding from a
source-level claim into an observed CI fact.

## 10. Encoding repair of this document (added in pass 3)

The EVIDENCE.md introduced by this workstream was itself written through a
Windows-1252 encoder. Sixteen lines carried mojibake: `U+00C2 U+00AC` where a
section sign belongs, `U+00E2 U+2020 U+2019` where an arrow belongs, `U+00E2
U+20AC U+201D` where an em dash belongs. Repaired in this PR, in scope: it is
the document this PR introduced, and no prose, count, or claim changed.

The repair is decidable from the bytes, not from a remembered marker list:

```
corrupt(repair(line)) == line          # proven for all 16 changed lines
```

`corrupt` is the forward defect - UTF-8 bytes read back as CP1252, with the five
undefined C1 positions (`0x81 0x8D 0x8F 0x90 0x9D`) passed through as identity.
A line is corrupt iff its CP1252 encoding decodes as UTF-8; a line that is
already clean, or whose bytes are not valid UTF-8, is left byte-identical. After
the repair the only non-ASCII characters left are genuine typography
(`U+00A7 U+00B7 U+2014 U+2026 U+2192`), and re-running the classifier finds
nothing to change.

Scope note: the two pre-existing evidence documents under
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`
and `.../gate-hygiene-queue-drain-verification-01/` carry the same defect. They
are **not** touched here - repairing them is a separate bounded workstream with
its own evidence, not a silent widening of this one.
