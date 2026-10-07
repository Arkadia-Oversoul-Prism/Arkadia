# EVIDENCE — gate07 router dependency-block truthfulness (a blocked frontier must be named)

Pass: `gate07/router-dependency-block-truthfulness-01`
Reconstructed: 2026-10-06 · BASE_MAIN `17e626cd27f8ea1e31f711fb787e6c7e5027ec70` (#333)

## Objective

Make `select_next_move` name the move it cannot route **because a dependency is unmet**, not
only the move it cannot route because its status is unrecognized.

Bounded engineering fix. No trajectory edit, no status-vocabulary change, no schema change, no
workflow change, no authority change, no gate promotion, no merge.

## Defect (observed live, not inferred)

The predecessor fix (PR #322) made a *malformed* status visible. A move carrying a perfectly
legal status whose dependency is unmet was still dropped silently, and the fallback reason
`no legal pending move (all complete or dependencies unresolved)` then stood in for the real
cause — a claim that reads as "there is nothing to do" while a live frontier is waiting.

Measured on `main` `17e626cd` with
`ARKADIA_ENGINEERING_TRAJECTORY=docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`:

```
status: NO_LEGAL_MOVE
blockers:
  - unrecognized move status: G12-A ('merged_acceptance_pending'), G12-C ('merged_acceptance_pending')
    — cannot route; expected one of accepted, completed, in_progress, merged, pending, revision_required
```

`G12-B` is the **sole `in_progress` move** in that trajectory and depends on `G12-A`. It was
absent from the report entirely. The operator could not see which move was next, nor what it
was waiting on. Note also that the legacy string `no legal pending move (all complete or
dependencies unresolved)` bundled two distinct conditions into one phrase, so a blocked
frontier and a finished trajectory were indistinguishable in the output.

## Change

`weaver/engineering_router.py` — `select_next_move` only:

- track the frontier moves that were skipped because a dependency is not done, recording the
  move id, the dependency id, and the dependency's current status;
- emit them as a `dependency-blocked frontier: …` blocker instead of letting the fallback
  message speak for them;
- leave the `unrecognized move status: …` blocker and the fallback message unchanged, so the
  predecessor guard (`tests/test_engineering_router_status_truthfulness.py`) still holds.

Post-fix output for the same live trajectory:

```
status: NO_LEGAL_MOVE
blockers:
  - unrecognized move status: G12-A ('merged_acceptance_pending'), G12-C ('merged_acceptance_pending')
    — cannot route; expected one of accepted, completed, in_progress, merged, pending, revision_required
  - dependency-blocked frontier: G12-B (depends on G12-A, still merged_acceptance_pending),
    G14 (depends on G12-C, still merged_acceptance_pending),
    G15 (depends on G14, still pending),
    G16 (depends on G15, still pending)
```

The whole blocked chain is now visible in one read: G12-A → G12-B, G12-C → G14 → G15 → G16.
The default trajectory (`ARKADIA-TRUTHFULNESS-01`) output is **unchanged** — its moves are
genuinely terminal, so it still reports the fallback message alone. That is the intended
distinction, and it is pinned by a test.

## Files changed

- `weaver/engineering_router.py` — `select_next_move` reporting only (+16 lines).
- `tests/test_engineering_router_status_truthfulness.py` — 5 new tests (+130 lines). This file
  is already in `weaver-mvp2-validation.yml`'s `push` **and** `pull_request` path filters and is
  executed by that workflow's guard step, so the guard is judged by the workflow it protects.
  `weaver/**` is likewise a trigger path.
- `docs/control-plane/evidence/gate07-router-dependency-block-truthfulness-01/EVIDENCE.md` (this file)
- `docs/control-plane/evidence/gate07-router-dependency-block-truthfulness-01/WORKSTREAM_STATE.md`

No boot code touched; `api/main.py` unchanged. CP10 mutation-boundary judge: **PASS**.

## Tests added (5)

| test | asserts |
|---|---|
| `test_dependency_blocked_frontier_is_named_when_no_move_is_legal` | a blocked frontier is named, with both the move and its dependency |
| `test_dependency_blocked_is_not_misreported_as_all_complete` | a **dependency cycle between two recognized active moves** names the frontier and does **not** emit the fallback — the load-bearing case, chosen so no `unrecognized` blocker can mask it |
| `test_negative_control_dependency_blocker_absent_when_move_is_routable` | a routable frontier is not reported as blocked (positive control: prevents "always emit the blocker" from passing) |
| `test_missing_dependency_is_named_once_not_as_dependency_blocked` | a *missing* dependency stays a distinct defect from an *unmet* one |
| `test_live_console_trajectory_names_its_blocked_frontier` | the live trajectory's own blocked frontier is named — conditional on live state, so it stays true after G12-A is accepted |

## Verification

**Negative control (the guard can detect the defect it claims to detect).** With the pre-fix
router restored from `HEAD` and the new tests kept:

```
FAILED test_dependency_blocked_frontier_is_named_when_no_move_is_legal
FAILED test_dependency_blocked_is_not_misreported_as_all_complete
FAILED test_live_console_trajectory_names_its_blocked_frontier
3 failed, 11 passed
```

With the fix in place: `14 passed`. The guard is not self-satisfying.

**Targeted suite.**

```
python -m pytest tests/test_engineering_router_status_truthfulness.py \
  tests/test_engineering_scheduler_bootstrap.py \
  tests/test_trajectory_schema_conformance.py \
  tests/test_scheduler_trajectory_conformance.py -q
→ 49 passed
```

**Architecture fitness.** `python -m pytest tests/architecture -q` → **11 passed** (main is
11/11, not the 9/10 recorded in older prose).

**Full-suite regression fingerprint.** Same tree, same invocation
(`python -m pytest tests/ -q --continue-on-collection-errors -rEf`), measured in this
environment on both revisions:

| revision | result | outcomes fingerprint | ids fingerprint |
|---|---|---|---|
| `main` @ `17e626cd` | 10 failed, 1585 passed, 20 skipped, 1 error | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` | `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` |
| branch | 10 failed, 1590 passed, 20 skipped, 1 error | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` | `92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413` |

**Byte-identical failing/error node set — zero regression.** The `+5 passed` is exactly the five
new tests. The pre-existing debt (10 failed / 1 collection error) is main's, is not attributable
to this pass, and is **not** fixed here. `-rEf` was used, not `-rf`: `-rf` omits `ERROR` summary
lines and would have silently fingerprinted a subset.

## Boundaries preserved

- No merge, no push to `main`, no force-push. Human authority over merge is untouched.
- No change to `ACTIVE_STATUSES` / `TERMINAL_DONE` — closing the `merged_acceptance_pending`
  vocabulary is PR #332's sovereign decision and is deliberately untouched. This pass reports
  the seam either way.
- No new endpoint, store, mutation path, or authorization path.
- No gate promotion. G12-B remains blocked on G12-A; this pass makes that legible, it does not
  unblock it.

## Relationship to adjacent open PRs (no duplication)

| PR | what it does | relationship |
|---|---|---|
| #335 `scheduler-session-report-truthfulness-01` | prints `blockers` in the scheduler's human-readable report | **composes.** This pass enriches the `blockers` array #335 prints; no file overlap (it edits the workflow + `test_scheduler_trajectory_conformance.py`). |
| #334 `router-schema-vocabulary-closure-01` | pins `schema ⊆ router` vocabulary | same seam, different direction; no file overlap |
| #332 `trajectory-status-vocabulary-decision-01` | sovereign decision on the status vocabulary | untouched — `merged_acceptance_pending` remains unrecognized by design pending that decision |
| #331 / #329 / #330 | scheduler failure-path reporting; worker→attention seam | no file overlap |

## Remaining uncertainty

- The five new tests are the only executable proof; the CLI output above was observed in this
  environment, not in CI. CI confirmation is the workflow run on this PR.
- The dependency-block detail string is operator-facing prose, not a machine contract. If a
  consumer parses `blockers`, it should treat the array as human-readable text (as the
  scheduler report already does).

## Authorization required

**Sovereign review and merge.** This PR is `READY_FOR_SOVEREIGN_MERGE` at the time of writing;
the branch is not to be merged by an agent.
