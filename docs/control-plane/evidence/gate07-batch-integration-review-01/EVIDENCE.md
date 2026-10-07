# Gate-07 — composed-batch integration review (PRs #329, #331, #332, #334, #335, #336, #340, #344)

**Workstream:** `gate07/batch-integration-review-01`
**Authority:** review + evidence only. No merge, no push to `main`, no mutation of any subject
PR, no scope expansion.
**Status:** IMPLEMENTED — integration measured twice; the released serialization constraint is
identified and now covers the second conflict seam (#334 × #344); subject PRs are individually
mergeable today; the constraint applies only to a *batch* merge.

> **Pass 2 (§7) supersedes the batch scope in §1–§6.** The pass-1 batch (#329, #331, #332, #334,
> #335, #336) is stale: four of its members have been superseded by **#344**
> (`gate07/strict-xfail-reconciliation-companion-01`, head `0127780c`), and the whole-batch
> superset {#331, #332, #334, #335, #336, #340, #344} now composes and executes with **zero
> regression**. §1–§6 remain as the pass-1 record; read §7 for the current integration truth.

## 1. Why this pass exists

Six open GATE-07 PRs (#329, #331, #332, #334, #335, #336) each declare a green check-run and
`mergeable: true`, and five of the six are **test-only or docs-only**. But *mergeable* is a
Git textual property, not a semantic one — the repository has paid for this lesson twice
(`AGENTS.md`: "Git conflict-free is not proof of semantic compatibility"; "a merge can invent a
state present in neither parent"). No pass has ever composed this batch and executed it. This
pass reconstructs the batch, merges it, resolves the one real conflict, and measures the
composed tree against a freshly re-measured baseline.

## 2. Reconstruction (live, this pass)

| item | measured value |
|---|---|
| canonical `main` | `74e8ea53a30213db8783e6733679d2f11903de0b` |
| batch base (all subject PRs) | `main` @ `17e626cd27f8ea1e31f711fb787e6c7e5027ec70`, i.e. `4587890..#333` |
| subject PRs | #329 `9c7c5764`, #331 `be1f3f05`, #332 `2a2a8fa1`, #334 `3a29fdea`, #335 `ef5df651`, #336 `0dc5383d` |
| #330 | verification-only companion of #329 (`main`/`4587890`); carried in the compose as a README-only no-op for #329's ancestry |
| composed tip | `90e80b5c1abc4dd3178240ecb7a5481efba6f14d` (see §3) |

Changed-path inventory was read from each PR's diff against its own base, not from PR prose.
Two checks are worth stating because they correct a stale reading:

- **#336 is four files, not thirty-two.** `git diff origin/main pr336` shows 32 paths and
  −7091 lines because #336's own base is `17e626c`, which already removed the `solspire/voice_*`
  tree that `74e8ea5` then re-added. `git diff 17e626c pr336` shows the real change: 4 files,
  +370 lines, `weaver/engineering_router.py` +16. A future pass must diff against the PR's base,
  not `main`.
- **#331 and #335 are not duplicates and not redundant.** Both edit
  `.github/workflows/arkadia-engineering-scheduler.yml` and
  `tests/test_scheduler_trajectory_conformance.py`, but add disjoint tests:
  #331 adds `test_session_reports_status_and_move_before_any_failure_exit` (+2 ordering
  negative controls) and writes the outcome **before** the FAILED early-exit; #335 adds the
  `Session report` step's blocker surface (`test_session_report_surfaces_router_blockers`,
  `test_session_report_runs_even_after_a_failure_exit`, `test_session_report_states_an_absent_session_result`,
  `test_negative_control_pre_fix_report_is_silent`). Neither test name appears in the other.
  A former plan to open a "dedup verification" PR over #331/#335 is therefore **unfounded** —
  recorded here as `CONTRADICTED`, not executed.

## 3. The one real conflict, and its resolution

The composed merge is clean for #329→#331→#332, then:

```
Auto-merging .github/workflows/weaver-mvp2-validation.yml
CONFLICT (content): Merge conflict in .github/workflows/weaver-mvp2-validation.yml
```

**#329 and #334 both add their guard file to the same two lists in
`weaver-mvp2-validation.yml`** — the `on.push.paths` filter and the `on.pull_request.paths`
filter — and #334 also appends its test to the existing `Engineering-router status truthfulness
guard` step's `run:` block, at the exact position #329 inserted a whole new step. Three regions
conflict.

The resolution is a **union**: on both path filters, keep #329's `test_attention_truthfulness.py`
and `test_worker_attention_composition.py` *and* #334's `test_router_schema_vocabulary_closure.py`;
in the job steps, keep the truthfulness step's `run:` block *including* the closure-guard line
(so #334's own wiring stays intact), and keep #329's separate
`Worker→attention composition seam guard` step. This is the same union the repository already
applies to the sibling `gate07/scheduler-*` workflow in #335. The resolved file is committed
verbatim as `weaver-mvp2-validation.resolved.yml`; its composed blob is
`a37b4b911b93a474605462749648b73155a5afce`.

The resolved workflow parses (`yaml.safe_load` → triggers `push`, `pull_request`,
`workflow_dispatch`).

## 4. Measurement — the composed tree

Composed in a throwaway worktree of `main` + {#329,#330,#331,#332,#334,#335,#336}, clocking the
0.27 s timezone-sensitive test with `TZ=America/New_York` so its date word is correct.

**GATE-07 guard set (the six files the batch adds or touches):**

```
python -m pytest -q -rEf \
  tests/test_attention_truthfulness.py tests/test_worker_attention_composition.py \
  tests/test_router_schema_vocabulary_closure.py tests/test_engineering_router_status_truthfulness.py \
  tests/test_engineering_scheduler_bootstrap.py tests/test_scheduler_trajectory_conformance.py
=> 81 passed, 1 xfailed
```

**Full suite, composed vs baseline, same environment:**

```
main   (74e8ea5) : 10 failed, 1703 passed, 20 skipped, 1 error
composed (batch) : 10 failed, 1737 passed, 20 skipped, 1 xfailed, 1 error
```

Failing/error **node set** sha256 (identity, not counts):

```
92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413   (11 nodes, main AND composed)
```

The node set is **byte-identical** — regression is **unchanged**. `+34 passed` is exactly the
batch's new passing tests (#334's `test_router_schema_vocabulary_closure.py` + #336's added
`test_engineering_router_status_truthfulness.py` cases + #329's composition guard), and the
`1 xfailed` is #329's strict xfail of the router cleaner-stop contract, which is expected.

**Architecture fitness:** `python -m pytest tests/architecture -q` → **11 passed** on the
composed tree (and on `main`).

**The 11 baseline nodes** are pre-existing main debt, unrelated to this batch, and are recorded
not fixed: `test_autonomy.py` (CE-01 collection error), `test_ais_capability_profile_onboarding.py`,
`test_ais_w2_living_gate_grove_handoff.py`, `test_identity_spine_w1.py`,
`test_m02_reasomate_truth.py`, `test_solspire_r1_governance_convergence.py` (×2),
`test_solspire_r3_execution_runtime.py`, `test_steward_filter.py` (×3).

> The published baseline (`804/54/12/2` at `6038989`) does not reproduce in this environment, as
> the repository already records. Attribution here is made from the sorted `FAILED`/`ERROR` node
> list only — the technique the repository records as correct.

**CP10:** all 30 changed paths across the batch resolve under the policy `LEGIT` allowlist
(`docs/`, `tests/`, `weaver/`, `.github/`, and root `[^/]+\.md$`); this pass adds only
`docs/control-plane/`. The composed tree touches no path outside the allowlist, so
`--judge` is `PASS`.

## 5. Defects surfaced, correctly scoped out of this pass

Both were already recorded by the subject PRs and are **not** this pass's to repair:

- **Router "clean stop" contract (flips #329's strict xfail).** `select_next_move()` always emits
  a blocker when it finds no routable move, so a genuinely complete trajectory composes a pushed
  HIGH `WEAVER_BLOCKED` every idle hour. #329 pins it as a strict xfail; repairing it changes the
  router's blockers contract and needs its own bounded workstream.
- **Live trajectory vocabulary.** `TRAJECTORY-CONSOLE-COMPLETION-01.yaml` still routes to
  `NO_LEGAL_MOVE` because G12-A/G12-C sit at `merged_acceptance_pending`, a status the router does
  not recognize. #332 records the vocabulary decision and #334 pins the seam; **neither edits the
  live trajectory**, so a future session will still hit this until the decision in #332 is executed
  under authorization. Observed live this pass (`ARKADIA_ENGINEERING_TRAJECTORY=…CONSOLE-COMPLETION-01.yaml`)
  → `status: NO_LEGAL_MOVE`, one blocker naming both moves.

## 6. Authorization boundary

- Review only. **No merge; the sovereign merges.**
- Individually, every subject PR is mergeable against `main` today (the conflict is only between
  #329 and #334 when composed).
- If the sovereign merges two or more of these PRs, #329 and #334 **must not be merged in the
  order either alone advertises as conflict-free** — GitHub will present the same three
  conflicts. Merge the batch as a reviewed whole using §3's union so no guard is dropped from
  either path filter.

---

## 7. Pass 2 — the batch has moved; re-measured with #344 in the union

Pass 1 measured six PRs against `main` @ `74e8ea5`. Between passes the batch changed shape, so
the pass-1 batch is **superseded**. Pass 2 re-derived the union from live evidence, composed it,
and executed it. No subject PR was mutated; no branch other than this one was touched.

### 7.1 Reconstruction (live, this pass)

| item | measured value |
|---|---|
| canonical `main` | `74e8ea53a30213db8783e6733679d2f11903de0b` (unchanged) |
| superseding PR | **#344** `gate07/strict-xfail-reconciliation-companion-01` @ `0127780cb8013ec48976330f61cc6c17ec142333` (open, mergeable, moving under an active session) |
| pass-2 union | {#331, #332, #334, #335, #336, #340, #344} |
| #341 head (this PR) | `e66a5f1935cc74d816fe10237885bd5742c18951` |

### 7.2 Supersession, verified by per-file content parity (not by prose)

Each of #329/#330/#342/#343 was compared **file by file** against #344's head tree:

| superseded | file | verdict |
|---|---|---|
| #329 | `.github/workflows/weaver-mvp2-validation.yml` | **same bytes** as #344 |
| #329 | `tests/test_worker_attention_composition.py` | DIFF — #344 removes #329's `strict=True` xfail and re-materializes the assertion as a live invariant (`CLEAN_STOP_BLOCKER` sentinel) |
| #342 | all 5 files (test, bus, router, 2 docs) | **same bytes** as #344 |
| #343 | all 4 files (`AGENTS.md`, test, 2 docs) | **same bytes** as #344 |
| #330 | 2 evidence docs | 1 same, 1 DIFF (`WORKSTREAM_STATE.md`) |

So #344 carries #342 and #343 **byte-identically**, and supersedes #329 by *resolving* it (the
strict xfail flips to a passing assertion). Merging #329/#330/#342/#343 alongside #344 is
redundant; merging them *instead of* #344 would drop the clean-stop repair.

### 7.3 The second conflict seam — #334 × #344, and why the pass-1 union still holds

#344's contribution to `.github/workflows/weaver-mvp2-validation.yml` is **byte-identical to
#329's** (verified: `diff` of the two `main...head` diffs is empty; the two head-tree files are
identical). It therefore does **not** contain #334's
`tests/test_router_schema_vocabulary_closure.py` in either path filter, nor #334's closure-guard
line in the status-truthfulness step. Composing #334 with #344 reproduces the **same three
conflict regions** pass 1 found between #334 and #329 — the peer session is working from the
same seam.

The §3 union resolution is unchanged and is the resolution for this seam too: keep **both**
#334's closure-guard path/step entries **and** #344's (== #329's) composition-guard step. The
artifact `weaver-mvp2-validation.resolved.yml` committed in pass 1 is **byte-identical** to the
resolution pass 2 applied to the #344-inclusive union (`diff` empty) — pass 1's artifact is
already correct for the new batch; it was not regenerated.

Composition method: `git apply --3way` each PR's `main...head` diff in order
{#331, #332, #335, #336, #340, #344}, applying #344 with
`--exclude=.github/workflows/weaver-mvp2-validation.yml`, then #334 with the same exclude, then
dropping in the resolved workflow. **All applications CLEAN** — the only conflict is the
workflow, and it is resolved by union.

### 7.4 Measurement — the composed tree, vs a freshly re-measured baseline

Same environment, same command, both trees:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
main   (74e8ea5)          : 10 failed, 1703 passed, 20 skipped, 1 error
composed (union)          : 10 failed, 1760 passed, 21 skipped, 1 error
```

Failing/error **node set** sha256, identical convention on both sides
(`FAILED|ERROR` line, strip the status word, strip the trailing ` - message`, sort):

```
92d344d0fbebcc3636e30509a1bfd72235f1ede2bede28d0b37edb6f0dcf6413   (11 nodes, main AND composed)
```

The node set is **byte-identical** — regression is **unchanged**. `+57 passed` is the union's
new passing tests; `+1 skipped` is #344's clean-stop repair turning #329's strict xfail into a
skip/pass (the composed guard set below shows **no xfail**).

> **Fingerprint convention, stated so it is not mistaken for drift.** The same node set hashes
> differently depending on the transform: stripping only the trailing ` - message` yields
> `f3e73647…`; stripping the status word as well yields `92d344d0…` — the value pass 1 recorded.
> Both are the *same 11 nodes*; `92d344d0…` is the convention this workstream uses. No divergence.

**GATE-07 guard set** (the batch's own files, composed):

```
python -m pytest -q \
  tests/test_worker_attention_composition.py tests/test_attention_truthfulness.py \
  tests/test_router_clean_stop_contract.py tests/test_gate07_strict_xfail_composition_reconciliation.py \
  tests/test_router_schema_vocabulary_closure.py tests/test_engineering_router_status_truthfulness.py \
  tests/test_scheduler_trajectory_conformance.py tests/test_voice_authority_boundary.py
=> 91 passed, 1 skipped        (pass 1, without #344: 81 passed, 1 xfailed)
```

**Architecture fitness:** `python -m pytest tests/architecture -q` → **11 passed** on the
composed tree (and on `main`).

**CP10 mutation boundary:** `scripts/cp10_mutation_boundary_policy.py --judge` over the composed
tree's 28 changed paths → **PASS** (exit 0).

### 7.5 What pass 2 changes for the sovereign

- The merge set is **{#331, #332, #334, #335, #336, #340, #344}** — not the pass-1 six.
  #329, #330, #342, #343 are **superseded by #344** and should be closed, not merged.
- The serialization constraint now names **#334 × #344** (same seam as #334 × #329); use the
  union resolution on `.github/workflows/weaver-mvp2-validation.yml`.
- Nothing else moved: `main` is still `74e8ea5`; every subject PR is individually mergeable.

### 7.6 Authorization boundary (unchanged)

Review and evidence only. **No merge, no self-authorization, no push to `main`, no mutation of
any subject PR, no scope expansion.** The sovereign merges. A batch merge must apply the §3 union
so neither #334's nor #344's workflow guard is dropped from the path filters.

### 7.7 Remaining uncertainty (not claimed)

- **#344 is under an active session** (`0127780c` at this pass; commits through `17:17:33Z`).
  Its head may move again; §7 is a measurement of `0127780c`, not of its future head. Re-measure
  before merging #344.
- `test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository` is
  intermittent under the full suite (`AGENTS.md`); it did **not** appear in either node set this
  pass, so it is not affecting the comparison — but a future run may show it as a
  count-only wobble. Attribute by node name, never by count.
