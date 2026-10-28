# EVIDENCE — residual recovery from closed PRs #482 / #572 / #499

Directive: `RESIDUAL-RECOVERY-2026-10-27-01`
Branch: `gate-hygiene/residual-recovery-2026-10-27-01`
Base: `main` @ `36f53be2` (verified live == local HEAD == `origin/main`; 0 open PRs)
Mode: bounded recovery and reconciliation — recover only what is missing
Authority: human sovereign (directive A1-A5)

## 1. Reconstruction (live, this pass)

| item | measured value |
|---|---|
| `origin/main` | `36f53be22d753ffe269f05cbf3fb39212f744207` |
| open PRs | **0** |
| `#482` | closed, unmerged (head `0cc7c9e7`, merge base `ee684fff`) |
| `#572` | closed, unmerged |
| `#499` | closed, unmerged (merge base `49809f45`) |
| `#553` | closed variant that also carried a history-depth guard |
| clone depth | `--is-shallow-repository` -> `false` (full clone) |

All three directives' reported findings were revalidated against live source rather than
taken from PR prose. Two residuals are **genuinely missing**; one is **already present**.

## 2. R482 — history-depth test coverage: MISSING (recovered)

### What is already on `main` (do not reapply)

`fetch-depth: 0` is present on both history-dependent workflows:

- `provider-routing.yml` — added by `b287659e` ("attribute regressions against a merge-base baseline")
- `sg-02-fe-2-v.yml`

`tests/test_history_depth_ci_wiring.py` is **absent** from `main`
(`git ls-files` -> 0 paths), and no equivalent guard exists (the other `*_ci_wiring.py`
guards assert different properties).

### The defect the missing guard would have caught — and did catch

The guard variant was run against live `main` **before** any patch. It failed **2** nodes:

```
FAILED tests/test_history_depth_ci_wiring.py::test_a_workflow_selects_itself_and_the_guard[provider-routing.yml]
FAILED tests/test_history_depth_ci_wiring.py::test_a_workflow_selects_every_input_its_guard_reads[provider-routing.yml]
2 failed, 15 passed
```

The failing assertion names the real omission:

> `provider-routing.yml` judges `tests/test_agents_md_encoding_adjudication.py`, which reads
> `AGENTS.md`, but does not select `AGENTS.md` in its `pull_request` paths filter.

Measured domain membership at `36f53be2`:

| workflow | `fetch-depth: 0` | executes a history-dependent guard |
|---|---|---|
| `provider-routing.yml` | **True** | yes |
| `sg-02-fe-2-v.yml` | **True** | yes |
| `economic-seam-engine.yml` | False | none |
| `lane-doc-currency.yml` | True | none |
| `baseline-fingerprint.yml` | True | none |

So the residual is **not** the `fetch-depth` fix (already landed). It is the **two
`paths:` filter omissions** in `provider-routing.yml`, plus the guard that pins them.

The #553 variant failed the same 2 nodes on the same tree — with the same root cause reached
by a differently-named assertion. The two variants are not competing repairs; they detect the
same live defect. This recovery carries the #482 variant.

### The fix (4 inserted lines, 1 file)

`.github/workflows/provider-routing.yml` `pull_request.paths`:

```yaml
      - "tests/test_history_depth_ci_wiring.py"
      - "AGENTS.md"
```

Why each is load-bearing:

- `tests/test_history_depth_ci_wiring.py` — the guard selects **itself**, so a rewrite of the
  guard is judged by the guard.
- `AGENTS.md` — it is an **input**, not prose. `tests/test_agents_md_encoding_adjudication.py`
  reads it, and `provider-routing.yml` executes that guard. `grep -rn "AGENTS.md"
  .github/workflows/` matched only comments, so before this line an `AGENTS.md`-only commit
  ran **no** whole-suite gate anywhere in the repository.

### Verification

| check | result |
|---|---|
| `tests/test_history_depth_ci_wiring.py` before patch | **2 failed, 15 passed** |
| `tests/test_history_depth_ci_wiring.py` after patch | **17 passed** |
| negative control A — `fetch-depth: 0` -> `1` | `1 failed` (`..._fetches_full_history[provider-routing.yml]`) |
| negative control B — drop the guard from `paths` | `1 failed` (`..._selects_itself_and_the_guard[provider-routing.yml]`) |

Both controls were applied to the **real** workflow file and restored byte-identically.

## 3. R572 — shallow-clone detection: MISSING (recovered)

`clone_is_shallow()` is absent from `scripts/lane_state.py` on `main`
(`grep -rn clone_is_shallow scripts/ tests/` matches only `scripts/baseline_preflight.py`,
a different module with its own copy).

`scripts/lane_state.py` on `main` cannot distinguish a **truncated checkout** from a
**rewritten `main`**. Both reach the same non-ancestor branch and emit the same finding:

```
snapshot base_main <sha> is not an ancestor of HEAD <sha>; the recorded provenance is void
(was main rewritten?)
```

The two conditions require **opposite responses** — a truncated clone is repaired by fetching
history, a rewritten `main` by re-measuring the lane PRs. Diagnosing the first as the second
sends an operator to investigate a rewrite that never happened.

The repair adds `clone_is_shallow(repo)` (`git rev-parse --is-shallow-repository`, read-only,
fails to **not** shallow) and splits two call sites:

- `_freshness_findings` — non-ancestor `base_main`: names the shallow checkout, "UNKNOWN, not
  a pass", and the repair (`fetch-depth: 0` / `git fetch --unshallow`).
- `_liveness_findings` — a merge commit that is **present but unwalkable**. This is the
  fail-open shape: `commit_is_present` is True so the absent-object guard does not fire,
  `--is-ancestor` exits non-zero because the graft stops the walk, and a naive reader
  concludes "not merged" and reports **nothing** for a stale open-claim on a genuinely merged
  PR.

### Verification

`tests/test_lane_instruction_doc_currency.py` — **41 passed** (base 37; `--collect-only`
attribution: +4 = the 4 new nodes).

| negative control | result |
|---|---|
| `clone_is_shallow` -> `return False` (split disabled at the definition) | **2 failed, 39 passed** — exactly `test_freshness_names_a_truncated_clone_instead_of_a_rewritten_main` and `test_liveness_reports_undecidable_for_a_present_but_unwalkable_merge_commit` |

Both **positive controls** keep passing under the disabled split, which is what proves the
guard does not swallow the defects it exists to catch:

- `test_freshness_still_reports_a_rewritten_main_on_a_full_clone` — a real rewrite still says
  "rewritten" and must **not** say "shallow".
- `test_liveness_still_reports_the_stale_claim_on_a_full_clone` — a full clone still names the
  stale snapshot as "already an ancestor of HEAD".

Fixture provenance: the shallow fixtures build a real `--depth 1` clone over a `file://`
origin with a `--depth 1` fetch of a side ref, so the commit is genuinely present and
genuinely unwalkable. The `is_ancestor_of_head(merge_commit, repo=origin) is True` assertion
is the control's premise — the truncated verdict is a clone artifact, not a rewrite.

## 4. R499 — `merged_acceptance_pending` gate: ALREADY PRESENT (not recovered)

**This residual is not missing. The behaviour is on `main` under different vocabulary.**

`grep -rn "merged_acceptance_pending"` at `36f53be2` matches **12 test modules** and the live
trajectory. The router's current behaviour already satisfies the directive's stated objective:

| directive requirement | live behaviour at `36f53be2` |
|---|---|
| never silently selected | `select_next_move` -> `None` |
| never a clean stop | blocked stop, not `CLEAN_STOP_BLOCKER` |
| named, not a data defect | the #322 truthfulness repair names the frontier |
| merge != acceptance | enforced at a different seam (see below) |

Measured: `tests/test_router_schema_vocabulary_closure.py`,
`test_engineering_router_status_truthfulness.py`, `test_router_clean_stop_contract.py`,
`test_trajectory_schema_conformance.py`, `test_worker_attention_composition.py` ->
**54 passed** on unmodified `main`.

### Why the #499 diff is NOT recoverable within this directive

The #499 diff is **not** merely a `merged_acceptance_pending` gate. Its load-bearing change is:

```python
-TERMINAL_DONE = frozenset({"completed", "accepted", "merged"})
+TERMINAL_DONE = frozenset({"completed", "accepted"})
```

That **removes `merged` from the terminal set** — i.e. it changes *when a merge becomes
authoritative*. The directive's section 4 MANDATORY HUMAN-REVIEW GATE reads:

> If the repair requires interpreting or changing **who can authorize acceptance, when a merge
> becomes authoritative**, K15/K3 governance, protected authority code, approval enforcement,
> or the identity boundary, **STOP before implementing that interpretation.**

This is that case, and the repository already says so in a decision record that is **on
`main`**: `docs/control-plane/evidence/gate07-trajectory-status-vocabulary-decision-01/EVIDENCE.md`
section 5 ("Authority classification (the reason this is not executed)") concludes that the
candidate repairs "are not behaviour-equivalent" and that the choice "decides an authority
question", which the contract "classifies correctly as a human-authority decision".

Additional contradiction recorded, not reconciled: the #499 branch's own evidence document
(`weaver-schema-status-semantics-2026-10-12/EVIDENCE.md`) states the implementation "remains
unverified until current-head CI passes" while its Verification section claims **VERIFIED**
at head `91398207...` with "all other 11 current-head check-runs are `completed/success`". The
`weaver/` tree has since moved on `main`; the two claims cannot both describe the current
tree, so the diff's verification does not transfer.

### Disposition

**HUMAN REVIEW REQUIRED.** The specific decision is a single, precisely-bounded question:

> May `merged` be removed from `TERMINAL_DONE` so that a merged PR no longer satisfies
> acceptance or a dependent move's dependency?

This directive explicitly does not authorize that interpretation ("This directive does not
authorize constitutional reinterpretation or a new authorization path"). The findings are
preserved here; no router change was made.

## 5. Cross-residual reconciliation

Effective-diff comparison found **no shared file, no shared invariant, and no test
dependency** between the two recovered residuals:

| residual | files | layer |
|---|---|---|
| R482 | `.github/workflows/provider-routing.yml`, `tests/test_history_depth_ci_wiring.py` | CI wiring / test-only |
| R572 | `scripts/lane_state.py`, `tests/test_lane_instruction_doc_currency.py` | lane guard / test-only |
| R499 | — | not recovered (human gate) |

One integration unit is safe: the two residuals are disjoint, neither touches
`api/main.py`, `api/lab_routes.py`, `weaver/engineering_router.py`, or any protected authority
surface. Minimum-artifact rule satisfied — **one** PR, not three.

CP10 boundary: all touched paths are admitted by
`scripts/cp10_mutation_boundary_policy.py --judge` (checked per path before staging).

## 6. Scope statement

Changed: exactly 5 paths (4 recovered + this record). No `api/main.py`, no `api/lab_routes.py`,
no `weaver/engineering_router.py`, no lane-owned frontend, no governance record.

Not claimed: merge, production deployment, acceptance, or autonomous dispatch. Verification
here is local test evidence against an exact revision.

## 7. Remaining work

1. **R499 human decision** — the `merged` / `TERMINAL_DONE` question above. Sovereign-only.
2. **#499's router evidence document** is unverified against the current `weaver/` tree; if the
   sovereign approves the semantics, the diff needs re-derivation, not a patch transfer.
3. **Incidental finding, PROPOSED and out of scope:** `provider-routing.yml` now names
   `AGENTS.md` as an input, so an `AGENTS.md`-only commit runs the whole suite. `sg-02-fe-2-v.yml`
   also executes the adjudication guard but does not name `AGENTS.md`; the recovered guard only
   asserts this for **judging** surfaces, and `sg-02-fe-2-v.yml` is exempted by its
   `continue-on-error` step. Whether that exemption should persist is a separate bounded
   question — recorded, not repaired.

## 8. Second-pass verification of this record (2026-10-28, independent re-measurement)

A later pulse under the same directive re-derived every load-bearing claim above from live
evidence rather than trusting this document. Result: the recovery stands; three claims needed
correction or completion, and are recorded here rather than rewritten in place.

### 8.1 Base revision re-verified, open-PR count corrected

| item | section 1 says | re-measured 2026-10-28 |
|---|---|---|
| `origin/main` | `36f53be2` | `36f53be22d753ffe269f05cbf3fb39212f744207` — **unchanged** |
| open PRs | **0** | **5** (`#577`, `#578`, `#579`, `#580`, `#581`) |

Section 1's "0 open PRs" was accurate *when written* (before this branch's PR existed) and is
superseded by the live count above. The base SHA is unchanged, so the recovery is still bound
to the revision it was measured against.

### 8.2 `lane-doc-currency` is red on `main` itself — it does not gate this PR

The `lane-doc-currency` check is **FAILURE** on this PR's head `fa30ab31`. It is not caused by
this change and does not block integration:

- The failing step is the last one, `python scripts/lane_state.py --check --verify-live`, and
  this PR does not touch that workflow
  (`git diff 36f53be2 fa30ab31 -- .github/workflows/lane-doc-currency.yml` -> empty).
- Re-measured directly: `--check --verify-live` exits **1** with **16** DRIFT findings on
  `main` @ `36f53be2` *and* on this branch's head — byte-identical. The plain `--check` (the
  snapshot-only step) exits **0** on both.
- The drift is a stale snapshot, not a code defect: `docs/control-plane/parallel-ui/lane-state.json`
  records 12 PRs as open (last base `68acf89f`) while only 5 are open. This PR does not touch
  the snapshot.
- The red is **pre-existing and repository-wide**, not attributable to any one branch: 14
  consecutive `lane-doc-currency` runs are `failure`, including a `workflow_dispatch` run on
  `main` @ `36f53be2` itself and runs on four unrelated branches.
- It does not gate merges: the repository declares **no rulesets** (`GET /rulesets` -> `[]`),
  and `#566` merged into `main` (`36f53be2`, 2026-10-25) with this check red.

The mechanical repair exists but is **out of scope** for this directive: the snapshot is
derived by `scripts/lane_state_refresh.py --write` (dry run here reports the full
open/merged/closed reclassification). The refresh is a separate bounded workstream; it was
measured, not executed.

### 8.3 R572's `clone_is_shallow` guard: present, and its controls re-proved

Section 3's negative control is reproduced exactly and independently. Disabling the behavior at
its **definition** (`clone_is_shallow` -> `return False`, so both call sites are covered) reddens
precisely the two intended nodes and nothing else:

```
FAILED tests/test_lane_instruction_doc_currency.py::test_freshness_names_a_truncated_clone_instead_of_a_rewritten_main
FAILED tests/test_lane_instruction_doc_currency.py::test_liveness_reports_undecidable_for_a_present_but_unwalkable_merge_commit
2 failed, 39 passed
```

Restored: `41 passed`. The positive direction also holds — under the disabled split the
rewritten-`main` case still reports "rewritten", so the split did not swallow the original
verdict. The two recovered files are **byte-identical** to the preserved #572 head `1a89ebf0`
(`scripts/lane_state.py` sha256 prefix `014bf5b0`, `tests/test_lane_instruction_doc_currency.py`
`689fc002`), so this is a provenance-preserving recovery, not a re-implementation.

### 8.4 R482's filter guard: present, and the #553 signature reproduced

Section 2's negative control is reproduced exactly. Removing the two recovered `paths:` entries
(`tests/test_history_depth_ci_wiring.py`, `AGENTS.md`) restores `main`'s state and reddens the
same two nodes the #553 variant failed:

```
FAILED tests/test_history_depth_ci_wiring.py::test_a_workflow_selects_itself_and_the_guard[provider-routing.yml]
FAILED tests/test_history_depth_ci_wiring.py::test_a_workflow_selects_every_input_its_guard_reads[provider-routing.yml]
2 failed, 15 passed
```

Restored: `17 passed`. The recovered guard is byte-identical to the preserved #482 head
`0cc7c9e7` (sha256 `7566aa7acc8314d098de2be3bf9dd28a90df2be8e07b9079abcfbb329e33c510`).

### 8.5 The "three workflows" discrepancy is resolved: the guard domain is derived

The directive reports #553 failing `test_a_workflow_selects_every_input_its_guard_reads` for
**three** workflows (`economic-seam-engine.yml`, `provider-routing.yml`, `sg-02-fe-2-v.yml`).
Re-measured at `36f53be2`, the guard parametrizes **one**:

| workflow | history-dependent | a *judging* script executes the guard |
|---|---|---|
| `provider-routing.yml` | True | **True** |
| `sg-02-fe-2-v.yml` | True | False (its guard step is `continue-on-error`-exempt) |
| `economic-seam-engine.yml` | False | False |

So the domain is a live measurement, not a stale list: the other two workflows are excluded
because they do not judge the guard, not because the guard forgot them. No defect; the
directive's figure describes an earlier revision.

### 8.6 Regression boundary — failing/error node set, not counts

Full suite, `-rEf --continue-on-collection-errors`, same environment:

| tree | result |
|---|---|
| `main` @ `36f53be2` | `112 failed, 2276 passed, 21 skipped, 111 errors` |
| this branch @ `1711771e` | `112 failed, 2297 passed, 21 skipped, 111 errors` |

**The failing/error node set is identical on both trees** — 223 nodes each, sorted-node-list
sha256 `9accc10a2ae4a59e64dd11ff0f792262784e50099c4921c78ca8a10587bb74e6` on both, and
`comm -3` empty in both directions. Zero regression, demonstrated by node **identity**, not by
counts. The counts move only in `passed`: `2276 -> 2297` (`+21`).

That `+21` is attributed by `--collect-only` and is exactly the recovered tests: `+4` in
`tests/test_lane_instruction_doc_currency.py` (37 -> 41) plus `17` in the new
`tests/test_history_depth_ci_wiring.py` (absent on `main`, `git ls-files` -> 0). No pre-existing
node was repaired, and none was broken.

### 8.7 CP10 boundary and provenance re-checked

All six touched paths are admitted by `scripts/cp10_mutation_boundary_policy.py --judge`
(per-path check). Full diff vs `main`: 6 files, `+1109 / -1` —
`.github/workflows/provider-routing.yml`, `AGENTS.md`, this record,
`scripts/lane_state.py`, `tests/test_history_depth_ci_wiring.py`,
`tests/test_lane_instruction_doc_currency.py`. No `api/main.py`, no `api/lab_routes.py`, no
`weaver/engineering_router.py`, no lane-owned frontend, no governance record.

The `AGENTS.md` addition is an append (insertion-only): the encoding audit on this tree reports
`Cyrillic 0 -> 0`, `oracle 6c43218a48a4 insertions-only inserted=1433 alterations=0
reproduced=True`, and the `AGENTS.md`-facing suites are unchanged at `58 passed, 5 skipped` on
both trees. No oracle-carried line was rewritten.

### 8.8 Unchanged disposition

R499 remains **not recovered — human review required** (section 4). The re-measurement confirms
its load-bearing change is `TERMINAL_DONE` losing `merged` in `weaver/engineering_router.py`,
which decides *when a merge becomes authoritative* — the directive's mandatory human-review
gate. No router change was made, and none is proposed here.

### 8.9 Why `provider-routing.yml` is *not* byte-identical to the preserved #482 head

Three of the four recovered artifacts are byte-identical to their preserved sources:

| artifact | preserved source | sha256 (16) | status |
|---|---|---|---|
| `tests/test_history_depth_ci_wiring.py` | #482 `0cc7c9e7` | `7566aa7acc8314d0` | IDENTICAL |
| `scripts/lane_state.py` | #572 `1a89ebf0` | `014bf5b066a7776b` | IDENTICAL |
| `tests/test_lane_instruction_doc_currency.py` | #572 `1a89ebf0` | `689fc00241343fe3` | IDENTICAL |
| `.github/workflows/provider-routing.yml` | #482 `0cc7c9e7` | `341860b3...` vs `758eba82...` | **DIFFERS, by design** |

`provider-routing.yml` differs because the directive prohibits reapplying workflow fixes already
present on `main`: `fetch-depth: 0` is **already** in `main`'s `provider-routing.yml` (line 37).
Copying the preserved file wholesale would have re-applied an already-integrated fix and reverted
every unrelated `main` advance in the file. Instead the branch takes **`main`'s** version and adds
only the missing filter entries — the whole diff is `+9 / -0`:

```
+      - "tests/test_history_depth_ci_wiring.py"
+      # `AGENTS.md` is an *input* to a guard this job judges, not incidental prose: ...
+      - "AGENTS.md"
```

That is the minimal correct delta, and it is why the "one of four differs" result is expected
rather than a provenance failure. The guard that consumes this filter is byte-identical; only the
filter was extended.
