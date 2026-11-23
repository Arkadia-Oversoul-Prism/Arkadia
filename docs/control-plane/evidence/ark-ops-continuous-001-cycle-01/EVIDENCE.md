# ARK-OPS-CONTINUOUS-001 — cycle 01 evidence

**Observed:** 2026-11-23, cycle window ~12:05–12:40 UTC.
**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`.
**Nature of this change:** documentation only. No product code, test, workflow, governance
text, `api/main.py` line or deployment configuration is modified. Nothing here is a merge,
a deployment, or an acceptance.

## 1. Current state

| item | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `git ls-remote`/`git/ref/heads/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` → `false`, 2705 commits) | `git rev-parse` |
| branch protection | none (`/branches/main/protection` → HTTP 404 "Branch not protected") | REST |
| rulesets | `0` | `GET /rulesets` |
| open PRs | **27**, every one a **draft**, every one `base: main` | `GET /pulls?state=open` |
| obsolete open PRs | **0** — no open head is an ancestor of `main`; every PR carries a non-empty diff | `git merge-base --is-ancestor` per head |

Merge authority is unaffected by any of the above: with 0 approvals and no protection, a
green `main` still confers no merge authority (GOV-03). This cycle executed no merge and
pushed to no `main`.

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version   → 200
  source_revision     bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source     RENDER_GIT_COMMIT
  revision_conflict   false
GET https://arkadia-qzu4.onrender.com/health        → 200 {"status":"radiant","path":"/health"}
```

`source_revision` equals live `main` exactly, so **source ↔ running revision is VERIFIED**
for this revision. That is necessary evidence of consistency and is **not** proof of correct
application behaviour and **not** deployment acceptance — the response itself says so.

`GET /` returns the 40-byte liveness JSON rather than the SPA when the request carries no
`Accept: text/html`; that is the documented SPA-mode behaviour, not a fault.

## 3. Checks executed on `main`

| surface | result |
|---|---|
| check-runs at `bb19aabd` | `boot-syntax`, `console-contract`, `engineering-scheduler`, `posture-currency`, `test`, `Full-history secret scan` → all `success`; `weaver_evolution` → `skipped` (×3) |
| `tests/architecture` | **11 passed** |
| gate-integrity bundle (`test_m02a_ci_gate_integrity`, `test_ci_gate_trigger_coverage`, `test_boot_syntax_boundary`, `test_workflow_injection_boundary`) | **230 passed** |
| lane currency, offline | `pytest tests/test_lane_instruction_doc_currency.py` → **66 passed**; `scripts/lane_state.py --check` → exit **0** |
| lane currency, live | `scripts/lane_state.py --check --verify-live` → exit **0**, `4 PR(s) read`, `doc-guard lanes ['1','2','3','4']`, `deferred []` |

`lane-doc-currency` did **not** run at `bb19aabd`: the workflow is path-filtered to
`docs/control-plane/parallel-ui/**`, `scripts/lane_state*`, its two test files and itself,
and this revision touches none of them. Absence of a run is **not** a pass, so the guard was
executed locally, both offline and against live GitHub. The committed snapshot records
`base_main b842892b`, four commits behind `main`; the guard accepts it because no guarded
lane doc changed in that window.

## 4. Full suite, and classification of every failing node

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 19 failed, 4250 passed, 22 skipped, 1 error in 287.05s
```

Sorted `FAILED`/`ERROR` node set: **20 nodes**, sha256
`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` — identical to the
recorded `main` baseline (`8d70e46e…`), so this cycle found **no new suite drift**.

Every node is accounted for, and **none is an unclaimed, non-reserved defect**:

| node(s) | count | classification | evidence |
|---|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | **sovereign-reserved** — CE-01 `weaver.autonomy` module-vs-package collision | pre-existing; reserved to the sovereign by prior record |
| `tests/test_mission_lifecycle_adapter_contract.py::*` | 9 | **environment-only** — needs `web/arkadia_console/node_modules/typescript`, absent in this sandbox (`ls … → No such file or directory`) | reproduced: `AssertionError: the repository TypeScript compiler is missing at …/typescript/lib/typescript.js`. CI provisions it: `sg-02-fe-2-v.yml` runs `pnpm install --frozen-lockfile` (step 134) **before** the full suite (step 236) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | **sovereign-reserved** — documented FINDING F-01; the test itself states it is a proxy-invalidation awaiting a sovereign persistence-boundary decision and is deliberately left failing | the node's own docstring; not repaired here |
| `tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup…`, `tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | 2 | repaired by open **#700** | `GET /pulls/700/files` names both files |
| `tests/test_solspire_r1_governance_convergence.py::*` | 2 | repaired by open **#693** | `GET /pulls/693/files` names the file |
| `tests/test_m01_persistence.py::…`, `tests/test_m05_files.py::…` | 2 | repaired by open **#690** | `GET /pulls/690/files` names both files |
| `tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | 1 | repaired by open **#691** | title + file list |
| `tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | 1 | repaired by open **#698** | title + file list |

The F-01 node was **not** repaired. Re-pinning it would loosen a persistence boundary,
which is a governance decision reserved to the sovereign, not test hygiene.

## 5. Open-PR queue

27 drafts, all `MERGEABLE`/`CLEAN` or `UNSTABLE`, all `reviewDecision: none`. **No PR has a
CI failure attributable to its own tree.** Seven PRs report `UNSTABLE`; every non-passing
check belongs to one of two external families:

- `native-arkadia-golden-workflow` and `beta-beta-0{1,2}-*` / `bundle-beta-evidence` —
  downstream of the external N-ATLAS runtime. Measured failure text:
  `"reason":"external runtime did not return usable inference"`, `"status":"FAILED"`, and
  `bundle-beta-evidence` then asserts `{'beta-01-english.json': 'PASS',
  'beta-02-hausa.json': 'FAILED'}`.

The intermittency is proven, not assumed: `n-atlas-external-beta.yml` returned **success** on
#704, #702, #701, #698, #697, #695, #694 and **failure** on #693, #703, #700, #699, #696 on
the same day, and branch `gate-hygiene/lane-aggregate-guard-execution-01` shows
`failure(45110213166) → success(45110507386) → failure(45110715250)` within one day on one
branch. A check that flips on one branch without a push is not a function of the tree.
#700's changed paths (one archived `.tsx`, two test files, one evidence doc) cannot influence
an external provider, so its reds are classified **not attributable**.

Consequence: the queue's blocker is **human merge throughput**, not outstanding repair work.
Opening a 28th code PR would add review load without closing a verified gap.

## 6. Gap closed by this cycle

`grep -rIl "ARK-OPS-CONTINUOUS-001" .` returned **no match** before this change: the
governing contract for the recurring reconciliation automation existed only in the directive
conversation, so each new session had to reconstruct its own authority and bounds from
memory. The contract requires the opposite — "an agent must be able to resume without
relying on conversational memory." This cycle records the contract at the same location the
open directive record (#675, `docs/control-plane/openhands/hourly-weaver/`) uses, with an
explicit precedence clause so it cannot be read as amending `AGENTS.md` GOV-03.

Both added paths pass the mutation boundary:
`printf '<path>\n' | python scripts/cp10_mutation_boundary_policy.py --judge` →
`Mutation boundary PASS`, exit `0`.

## 7. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`/api/version` reports the same revision (`revision_conflict: false`). `main`'s executed
checks are green. Full-suite failing set is the recorded baseline (`8d70e46e…`, 20 nodes),
fully classified. 27 open drafts; 0 obsolete; 0 attributable CI failures.

**Evidence.** Sections 1–6 above; commands and outputs are reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03) and 27 drafts await human review.
(b) `beta-*` / `native-arkadia-golden-workflow` results are governed by an external provider
and cannot be made deterministic from this repository. (c) CE-01 and FINDING F-01 are
reserved to the sovereign.

**Authorized next action.** A human reviews the queue for merge; an agent may, on a later
cycle, verify a specific PR against the then-current `main`, or implement a newly measured,
non-reserved defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 or F-01 without a
sovereign decision; opening a PR whose only product is activity.

**Completion condition.** This cycle is complete when the contract record and this evidence
are reviewable on an isolated branch, with `main` unmodified and no merge, deployment or
acceptance claimed.
