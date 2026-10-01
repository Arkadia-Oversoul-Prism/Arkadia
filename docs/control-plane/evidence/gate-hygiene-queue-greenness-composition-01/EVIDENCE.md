# gate-hygiene — composed-queue greenness, one merge-order defect, and a verified repair

Pass: `gate-hygiene/queue-greenness-composition-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of PR #141)
Authority: no merge, no push to `main`, no force-push. Human-only merge.
**Type:** bounded evidence pass + one apply-verified doc patch (not applied here). No source,
test, or governance change; `api/main.py` untouched.

---

## 1. Why this pass exists

PR #158 (`gate-hygiene/open-pr-queue-merge-order-map-01`) mapped the open-PR queue and
verified that the recommended merge sequence is **conflict-free**. It stated its own limit
explicitly (§10):

> The composability probes are **git-object** merges, not a build or a deployment. They make
> **no** production-parity claim and do not assert the merged tree is *green* — only
> *conflict-free*.

A sovereign draining the queue under the #158 map would therefore learn, at the end, whether
the result passes — not before. This pass closes exactly that gap: it **materialises the
recommended sequence and measures the resulting tree**, then attributes every delta against a
freshly re-measured baseline.

This is the smallest valid next task on the `gate-hygiene` workstream: it requires no new
authority, no product decision, and no architecture change. It is a *measurement*.

## 2. Preconditions and method

- **M0 — clone is full, not shallow.** `git rev-parse --is-shallow-repository` → `false`;
  `git rev-list --count origin/main` → `1414`. (#158's warning that a shallow clone silently
  corrupts `merge-base` / three-dot diffs does not apply to this clone.)
- **M1 — baseline re-measured live**, not inherited. A detached worktree at `origin/main`:
  - `python -m pytest tests/architecture -q` → **11 passed**
  - `PYTHONPATH=archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors`
    → **20 failed / 1039 passed / 13 skipped / 2 errors**
- **M2 — materialise the #158 sequence** in a scratch worktree, real `--no-ff` merges:
  `157, 156, 155, 151, 152, 153, 154, 142, 144, 145, 146, 148, 149, 150`.
- **M3 — measure the composed tree**, then diff the failing-test *set* (not the count)
  against the baseline set.

`--continue-on-collection-errors` is required: without it pytest aborts at the two known
collection errors and reports nothing (this is itself pre-existing debt, see §5).

## 3. Result 1 — the recommended sequence is conflict-free (reproduced)

All **14 merges were clean**, reproducing #158 §4. No conflict at any step, including the
`api/main.py` overlap between #153 and #154.

Composed-tree `api/main.py` is **2531 / 2600** lines and `python -m py_compile api/main.py`
is **OK** (the P1-A boot-code check).

## 4. Result 2 — the composed tree is **not** green: one genuine merge-order defect

Composed tree (before any repair):

```
19 failed, 1090 passed, 15 skipped, 1 error
```

Set-level delta against the re-measured baseline:

| direction | n | tests |
|---|---|---|
| **fixed by the queue** | 2 | `test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move`, `::test_dry_run_evidence` |
| **still failing** | 18 | the `SH-07` / `SH-09` / steward-filter / spiral-grove / solspire cluster (unchanged from baseline) |
| **NEWLY BROKEN** | 1 | `test_documented_route_contract.py::test_health_route_documentation_matches_the_served_app` |
| **collection errors** | 2 → 1 | `test_render_codex.py` cleared; `test_autonomy.py` remains |

### The defect is a *semantic* conflict — invisible to a git-object merge

Two PRs, each correct alone, contradict each other when combined:

- **PR #156** (`gate-hygiene/documented-route-contract-repair-01`) adds
  `tests/test_documented_route_contract.py`, which parses `api.main:app` for served routes
  and asserts each appears in the `DEPLOYMENT_GUIDE.md` table.
- **PR #154** (`gate-hygiene/production-health-route-provenance-01`) adds `GET /health` to
  `api/main.py` as a projection of `/api/heartbeat`.

Both PRs *anticipate* each other — #156's prose says *"PR #154 restores it … Until that
merges, probe `/api/heartbeat`"*, and #154's docstring cites `DEPLOYMENT_GUIDE.md`. Neither
merged the other's effect, so the guard reddens on the union.

Measured isolation (scratch worktree, `origin/main` base):

| composition | `test_documented_route_contract.py` |
|---|---|
| `main` + #156 alone | **9 passed** |
| `main` + #154 alone | **9 passed** |
| `main` + #156 + #154 | **1 failed, 8 passed** |

Fingerprint:

```
tests/test_documented_route_contract.py::test_health_route_documentation_matches_the_served_app
E  AssertionError: /health is served but the guide's table does not list it
E  assert ('GET', '/health') in {('GET','/'), ('GET','/api/codex'), ...}
```

`api/main.py` overlaps between #153/#154 were hunk-disjoint (#158 §4) and merged cleanly.
This failure is **not** an `api/main.py` conflict: it is a documentation row missing from the
tree the guard parses. **File-level overlap and hunk-level overlap were both clean; the
contradiction is at the semantic level.**

## 5. Result 3 — the two baseline improvements are attributed

| PR | effect, measured in isolation | evidence |
|---|---|---|
| **#148** `scheduler-bootstrap-testspec-repair-01` | `tests/test_engineering_scheduler_bootstrap.py` → **13 passed** (was 2 failed) | fixes both baseline scheduler failures |
| **#149** `render-codex-collection-error-provenance-01` | `tests/test_render_codex.py` collects cleanly (`no tests ran`, no error) | clears one of the two baseline collection errors |

Both are genuine baseline-debt reductions, attributable to specific PRs.

## 6. The repair — apply-verified, minimal, **not applied to `main`**

`patches/health-row-doc-repair.patch` (in this directory) — **2 hunks, docs only, 1 file**:

1. adds one table row to `DEPLOYMENT_GUIDE.md`:
   `| GET | /health | Liveness projection of /api/heartbeat (deployment contract path) |`
2. rewrites the now-false prose *"`GET /health` is **not** served by this app on the current
   revision — it returns `404` … Until that merges"* into the post-merge truth: `/health` **is**
   served as a projection, never a second liveness authority.

Verified on the composed tree with the patch applied:

| check | result |
|---|---|
| `test_documented_route_contract.py` + `test_production_health_route.py` | **14 passed** |
| full suite | **18 failed / 1091 passed / 15 skipped / 1 error** |
| new failures vs baseline | **0** (the 1 new failure is gone) |
| `tests/architecture` | **11 passed** |
| `python -m py_compile api/main.py` | **OK**; `api/main.py` 2531 / 2600 |
| CP10 boundary judge on `DEPLOYMENT_GUIDE.md` | **PASS** (exit 0) |

The patch is relative to `DEPLOYMENT_GUIDE.md` **as PR #156 leaves it** (`index dd17939`), so
it applies cleanly **once #156 has merged**. It is published as a verified artifact, not
applied here, so that this pass stays docs/evidence-only.

### Why this is a repair and not a weakening

The guard's rule is *"the guide must list what the app serves."* #154 makes `/health`
genuinely served; the correct response is to list it, not to exempt it. The patch makes the
guide match the app — it does not relax the assertion, and it removes a sentence that becomes
false the moment #154 merges.

## 7. Merge-order consequence for the sovereign

#158's advisory map is still correct on ordering, but it must be read with one addition:

- **#156 and #154 must not both merge without the row.** Either
  (a) apply `patches/health-row-doc-repair.patch` after #156 merges and before/with #154, or
  (b) treat the pair as a single unit.
- **Preferred, and now measured:** merge Wave 1 in the #158 order **with the patch applied at
  the #154 step** → the 14-step sequence is green, not merely conflict-free.
- If the queue is drained without the row, `main` goes red on
  `test_documented_route_contract.py` — a guard #156 itself added. That is a *new* failure
  attributable to the merge, not baseline debt.

## 8. Scope and regression boundary

Evidence-only **plus one published, unapplied patch**. This pass changes no tracked source,
test, `AGENTS.md` byte, or governance file; it touches neither `api/main.py` nor `LAYER_MAP.py`.
It therefore cannot alter any suite's outcome on `main`.

Baseline failures are **recorded, not fixed** (§4 table), per the contract's rule that baseline
debt is not repaired while executing an unrelated bounded task.

## 9. Remaining uncertainty

- The composition is a **git + pytest** measurement, not a build or a deployment. It makes
  **no** production-parity claim. `vite build` was not run (no `node_modules` in the scratch
  worktree); the frontend is not exercised by this pass.
- The patch is verified **against the composed tree only**. Its behaviour against a partially
  drained queue (e.g. #156 merged, #154 not yet) is *prose* truth but was not separately
  measured.
- The 18 remaining failures are reproduced, not diagnosed. Their classifications (`SH-07`,
  `SH-09`, steward-filter, spiral-grove, solspire) are carried from the existing ledgers and
  were not re-adjudicated here.
- `test_autonomy.py` collection error is unchanged pre-existing debt.
