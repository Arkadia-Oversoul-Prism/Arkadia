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
