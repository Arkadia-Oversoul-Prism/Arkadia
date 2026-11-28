# ARK-OPS-CONTINUOUS-001 — cycle 29: the queue gets an integration oracle

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Branch:** `gate-hygiene/pr-integration-oracle-01`
**Pulse:** 2026-11-27T12:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion, no pull-request closure.

This is a **fix** record, so it takes the `…-cycle-NN-<slug>` path. It records one bounded
task: the missing ability to decide whether an open pull request's work has already landed.

---

## 1. Reconstruction (live, not remembered)

Read from GitHub at 2026-11-27T12:06Z:

| repository | default branch | head | open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 2 (#9, #10) | 2026-11-27T10:25:30Z |
| `family-safety-network` | `main` | `18c729735fd4` | 7 (#10–#18) | 2026-11-27T11:12:00Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 63 | 2026-11-27T09:12:14Z |

`Arkadia` carried the oldest verified progress, so the directive's fairness rule selected
it. The tie-break order (Sonata → FSN → Arkadia) was never reached. This is the same
selector `scripts/portfolio_state_refresh.py` implements on PR #744; it was re-derived from
the API, not read from a prior cycle's prose.

The rotation is behaving as designed: cycle 27 landed FSN work (11:12Z), cycle 28 landed
Sonata work (10:25Z), so Arkadia was next.

## 2. Residual revalidation (directive §5) — all three are closed

The directive says not to assume the residuals remain missing. Measured on `main`
`8f746f9eab6d`:

| residual | claim | measurement | verdict |
|---|---|---|---|
| **R482** history-depth coverage | `AGENTS.md` is an input of a guard but named by no workflow filter | `.github/workflows/provider-routing.yml:24` lists `- "AGENTS.md"` with the derivation comment; `tests/test_history_depth_ci_wiring.py` exists | **INTEGRATED** |
| **R572** shallow-clone detection | an incomplete local history is indistinguishable from a history rewrite | `scripts/baseline_preflight.py:84` and `scripts/lane_state.py:245` both define `clone_is_shallow()`; `_freshness_findings` and `_liveness_findings` split on it | **INTEGRATED** |
| **R499** `merged_acceptance_pending` | the router vocabulary seam is guarded in one direction only | `tests/test_router_schema_vocabulary_closure.py` pins the reverse direction (a schema-legal status must be routable **or explicitly named unroutable**) | **GUARD INTEGRATED**; the vocabulary *choice* stays sovereign |

```
$ python -m pytest tests/test_history_depth_ci_wiring.py tests/test_baseline_preflight.py \
      tests/test_router_schema_vocabulary_closure.py \
      tests/test_engineering_router_status_truthfulness.py -q -rEf
64 passed in 3.18s
```

R499 is recorded as **HUMAN_DECISION_REQUIRED**, not BLOCKED. The decision record
(`docs/control-plane/evidence/gate07-trajectory-status-vocabulary-decision-01/EVIDENCE.md`
§4–§5) measures three candidate repairs producing three different routing outcomes, and
states that repair A "asserts completion on behalf of the sovereign". The guard behaviour
the directive asks about **already exists under different vocabulary** — the seam is now
named rather than silently skipped — so no new implementation is owed here. Teaching the
router `merged_acceptance_pending` would change what a merge is allowed to mean. That is an
authority question and is not repaired in this cycle.

## 3. The verified gap

The queue holds 63 open draft PRs. The directive requires reducing that accumulation
"through verified consolidation, completion, or justified closure — not through destructive
cleanup". Three read-only tools already exist and none answers the question a closure
decision needs:

| tool | question it answers |
|---|---|
| `scripts/open_pr_inventory.py` | is this PR `mergeable`? (a *detail*-endpoint field) |
| `scripts/pr_wave_dry_run.py` (#736, open) | do these heads compose without a `git merge` conflict? |
| `scripts/pr_batch_reconcile.py` (#733, open) | which PRs share paths / declare dependencies? |

None answers **"has this PR's work already landed?"** That is the only input that can
justify closing a PR as obsolete, so the queue could not distinguish an already-landed
draft from live work.

**Why not `git cherry`.** A squash merge rewrites commits, so patch-id comparison reports
every squashed PR as unlanded. The oracle is content-addressed instead: GitHub's
`GET /pulls/{n}/files` carries the *blob sha* of each changed path at the PR head, and
comparing that to the blob at the base-branch head decides the question without depending
on commit identity.

## 4. What landed

| file | role |
|---|---|
| `scripts/pr_integration_oracle.py` | read-only oracle: `blob_map()`, `classify()`, CLI |
| `tests/test_pr_integration_oracle.py` | 11 tests against a real temporary git repository |

Verdicts: `INTEGRATED` (every changed path already carries the PR's content at base),
`PARTIAL` (some paths landed), `CONTRIBUTES` (none landed), `UNKNOWN` (a path or the file
list could not be decided — a truncated 3000-path list is `UNKNOWN`, never "the paths I saw
are landed").

Read-only by construction: one `urlopen(` call site with no `method=`, so every request is
a `GET`; local `git ls-tree` only. The guard asserts that.

## 5. Measurement — the queue is genuine unmerged work

```
$ python scripts/pr_integration_oracle.py            # base = origin/main @ 8f746f9eab6d
63 open PRs  |  CONTRIBUTES=63
```

**Positive control, because an oracle that reports one verdict for everything is
decoration.** The same `classify()` run against two *merged* PRs on the same base:

```
#705 (merged) -> INTEGRATED   15 changed paths, all landed=True
#675 (merged) -> INTEGRATED    1 changed path,  landed=True
#744 (open)   -> CONTRIBUTES  11 changed paths, all landed=False
```

So the oracle discriminates, and the 63-way result is a finding rather than a constant:
**no open draft's work has been silently landed on `main`.** The accumulation is 63 real,
distinct, unmerged changes — it is not a pile of duplicates waiting to be swept.

That redirects the reduction strategy, which is the useful part: closure-as-obsolete is
**not** available for any of the 63. Reduction has to come from consolidation (composing
related drafts into fewer reviewable units) or from human review throughput. Recording the
absence of a shortcut is worth more than inventing one.

## 6. Verification

```
python -m pytest tests/test_pr_integration_oracle.py -q -rEf      -> 11 passed
python -m py_compile scripts/pr_integration_oracle.py             -> ok
```

Negative controls carried by the guard:

- `test_negative_control_a_differing_path_is_not_integrated` — the pre-oracle shape
  (compare nothing, call it landed) is fed a path whose head blob genuinely differs from
  base; it must read `CONTRIBUTES`.
- `test_a_truncated_file_list_is_undecidable_not_integrated` — a 3000-entry list of
  *landed* paths must still read `UNKNOWN`, so a truncated view cannot be mistaken for a
  complete one.
- `test_the_oracle_issues_no_mutating_request` — no `POST`/`PUT`/`PATCH`/`DELETE`, one
  `urlopen(`, no `method=`. A closure input must not be able to change PR state.

## 7. Not executed (and why)

- **No PR was closed.** Zero closure candidates were produced; the oracle reports, the
  human decides. Closure authority is not implied by a verdict.
- **`api/main.py` untouched.** Not a boot-code change; the 2600-line budget is unaffected.
- **#733 / #736 not extended.** They are other open drafts with their own scopes; the
  oracle answers a different question. No parallel PR was opened for their tasks.
- **The router vocabulary (R499) not repaired.** Authority question; recorded.

## 8. Next legal task

Re-derived, not asserted. `scripts/portfolio_state_refresh.py --write` run at
2026-11-27T12:12:32Z records:

```
sonata                 last_progress_at 2026-11-27T10:25:30Z   2 open PRs
family-safety-network  last_progress_at 2026-11-27T11:12:00Z   7 open PRs
Arkadia                last_progress_at 2026-11-27T12:11:57Z  64 open PRs  <- this pulse
next: sonata -- oldest verified last_progress_at among unblocked repositories
```

So the next pulse selects **`sonata`** (10:25:30Z is older than FSN's 11:12:00Z). An earlier
draft of this section guessed FSN from the *pre-pulse* ordering; the derivation corrects it,
which is the reason the ledger is derived rather than typed.

For Arkadia specifically: the queue needs **consolidation**, not closure. The cheapest next
bounded Arkadia slice is to group the 64 drafts by changed-path overlap and measure which
groups compose cleanly — but `scripts/pr_wave_dry_run.py` (#736) already owns that
measurement, so the next Arkadia pulse should **continue #736** rather than duplicate it.

## 9. Human decisions required

- Review this PR; it is a draft and marking it ready is the owner's action.
- Decide whether the 63-draft queue should be reduced by consolidation (composing drafts)
  or by human review throughput. No agent may close a PR on the strength of an oracle
  verdict alone.
- R499 remains open on the *vocabulary* question (repair A vs B vs C). The decision record
  already classifies it as sovereign.

## 10. Deterministic resumption block

```
current state      : main 8f746f9eab6d; 64 open Arkadia drafts (63 + this PR); all CONTRIBUTES
evidence           : this record; scripts/pr_integration_oracle.py; 11 tests
blockers           : merge execution is human-only; drafts need their owner to mark ready
authorized action  : continue an existing draft; one bounded objective per pulse
forbidden actions  : merge, push to main, force-push, deploy, close a PR on oracle alone,
                     open a parallel PR for a task #733/#736 already owns
completion         : the selected draft's gap is measured, implemented, and guarded, and
                     this record plus the ledger name the next legal task
```

## 11. Cycle 35 continuation — the unreadable file list was a landing claim

Measured 2026-11-28 during a portfolio pulse at `main` `8f746f9e` / this PR's head `3824817a`.

**Defect.** `pr_files()` returned `[]` on *any* failed page — a 403, a rate limit, a
network error — and `classify([])` returned `INTEGRATED`. So a PR whose file list could
not be read was reported as "its work has already landed": the single verdict that
justifies closing live work. `tests/test_pr_integration_oracle.py` pinned that reading
(`test_an_empty_diff_contributes_nothing` asserted `INTEGRATED`), which is the
freeze-the-bug shape — the guard protected the defect instead of the property.

```
before                                    after
classify([], {})  -> INTEGRATED           classify([], {})  -> UNKNOWN
pr_files(<fails>) -> []                   pr_files(<fails>) -> None  (evaluate -> UNKNOWN,
                                                                    reason=file_list_unavailable)
```

**Repair, three sites, one file.**

| site | change |
|---|---|
| `classify` | an empty list is `UNKNOWN`; docstring states an unreadable list is never a landing claim |
| `pr_files` | returns `None` when a page is unreadable, distinct from a successful empty list |
| `evaluate` | a `None` file list yields an `UNKNOWN` row with `reason: file_list_unavailable`, and `render_table` prints `n/a` rather than a fabricated `0` |

**Negative controls, both proved against the pre-repair script** (revert `classify`/`pr_files`
to the head shape, run, restore): `2 failed, 10 passed`. Restored: `12 passed`.
The unreadable case uses a closed port (`http://127.0.0.1:9`) as a real failing `urlopen`
— no mock, the same code path a 403 takes.

**Checks run**

```
python -m py_compile scripts/pr_integration_oracle.py                     -> ok
python -m pytest tests/test_pr_integration_oracle.py -q -rEf              -> 12 passed
python -m pytest tests/test_pr_integration_oracle.py \
      tests/test_open_pr_inventory.py tests/architecture -q -rEf          -> 30 passed
printf '<3 paths>' | python scripts/cp10_mutation_boundary_policy.py --judge -> PASS
```

**Not claimed.** No PR was closed; no merge, deployment or acceptance. The live queue
measurement in §"Measured effect" was not re-run in this continuation (needs network +
token), so its `63 open PRs | CONTRIBUTES=63` figures remain bound to base `8f746f9e`.
`api/main.py` is untouched.
