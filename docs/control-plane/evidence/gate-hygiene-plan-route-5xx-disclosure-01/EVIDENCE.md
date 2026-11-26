# Plan-route 5xx disclosure — the last unowned instance of a class three open PRs are closing

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`, cycle 25
**Base:** `main` @ `cb2841956bcc0397007b9efffbaa8cc6d0801836` (2026-11-26T00:16:37Z)
**Measured:** 2026-11-26, 05:06-06:00 UTC, this workspace
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no draft conversion, no acceptance. This PR is a **draft**.

---

## 1. State re-derived, not inherited — zero drift

| fact | measured value | how |
|---|---|---|
| canonical `main` | `cb2841956bcc0397007b9efffbaa8cc6d0801836` | `git rev-parse origin/main` after `git fetch` |
| local `main` vs `origin/main` | `0 0` (ahead/behind) | `git rev-list --left-right --count` |
| clone | full (`is-shallow-repository` -> `false`) | `git rev-parse` |
| working tree at start | clean | `git status --porcelain` |
| open PRs | **63** — 62 drafts, **1 ready** (`#679`) | `search/issues is:pr is:open` |
| `api/main.py` | 2 597 lines (budget 2 600) | `wc -l` |

Cycle 24 recorded the same SHA and the same queue shape. Nothing was inherited: the figures
above were re-read this cycle.

### 1.1 Production boundary — revision identity VERIFIED, acceptance NOT CLAIMED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision       cb2841956bcc0397007b9efffbaa8cc6d0801836
  revision_source       RENDER_GIT_COMMIT
  revision_conflict     false
  canonical_deployment  one_reconciled_deployment
GET /health -> 200 {"status":"radiant","path":"/health"}
```

Deployed revision equals `main`. Necessary evidence of source-to-runtime consistency; it is
not proof of correct behaviour and it is not acceptance.

---

## 2. Failing/error node set — 23 nodes, identical to cycle 24

`python -m pytest tests/ -q -rEf --continue-on-collection-errors` at `cb284195`:

```
22 failed, 4251 passed, 22 skipped, 1 error in 295.01s (0:04:55)
```

**23** failing/error nodes; sorted node-id sha256
`17b3b70467b8d5c3730770b25518f00fa8c257ab0e3fdd48299bc8e8d6713a1d`, byte-identical to
cycle 24's value under the same convention. The per-file distribution is unchanged and every
node is owned by an open PR or sovereign-reserved (CE-01 / FINDING F-01).

### 2.1 One classification was verified instead of repeated

Cycle 24 classified the **10** `test_mission_lifecycle_adapter_contract.py` nodes as
"environment-only — needs `web/arkadia_console/node_modules/typescript`". That was an
inference. It is now measured:

| tree | result |
|---|---|
| `node_modules/typescript` absent | `10 failed` |
| after `corepack pnpm install --frozen-lockfile` in `web/arkadia_console` | **`10 passed`** |

And the prerequisite *is* installed by a gate that *does* execute the file: the module is a
member of the derived console-contract domain
(`python scripts/console_contract_domain.py | grep mission_lifecycle` -> 1 match), and
`.github/workflows/prism-console-contract.yml` runs `pnpm install --frozen-lockfile` in
`web/arkadia_console` before `pytest -q $(python scripts/console_contract_domain.py)`. So the
ten nodes execute in CI with their toolchain, and their absence from CI's failure list is not
a hidden skip.

Recorded so a later cycle does not "repair" these nodes: there is nothing to repair, and a
source edit would redden a passing gate.

---

## 3. The defect — one unowned instance of the 5xx disclosure class

The repository is closing "a 5xx response that carries the exception bound by its own
`except` clause" file by file:

| surface | repair | detector scope |
|---|---|---|
| `api/main.py` | #729 | that file |
| `api/knowledge_routes.py` | #718 | that file |
| `api/source_routes.py` | #735 | that file |

Each detector is scoped to its own file, so an instance in any other module survives all
three. Measured over the corpus (`grep -rn 'status_code=5[0-9][0-9]'`, filtered to an
expression referencing the caught exception) and cross-referenced against
`GET /pulls/<n>/files` over all 63 open PRs:

| file with a 5xx echo | owning open PR |
|---|---|
| `api/main.py` | #729 |
| `api/knowledge_routes.py` | #718 |
| `api/source_routes.py` | #735 |
| `api/lab_routes.py` | #712 |
| `solspire/console_router.py` | #710, #713 |
| `api/arkana_signal_routes.py`, `api/ceo_chat_routes.py`, `api/ims_products.py` | #717 |
| **`api/plan_routes.py`** | **none — 0 open PRs touch it** |

The unowned instance, as measured on `main`:

```python
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   # and no log
```

The caller receives kernel internals (tool output, filesystem paths, upstream host and
credential state) and the operator receives nothing, because the handler logs nothing — so
the cause is destroyed at the moment the caller is told it.

---

## 4. Change

`api/plan_routes.py` — log the cause, return a bounded message:

```diff
     except HTTPException:
         raise
-    except Exception as e:
-        raise HTTPException(status_code=500, detail=str(e))
+    except Exception:
+        logger.exception("plan execution failed")
+        raise HTTPException(
+            status_code=500,
+            detail="Plan execution failed; inspect server logs for internal details.",
+        )
```

Deliberately unchanged: the `400` paths. A 4xx echoes a caller-caused message
(`"input is required"`, `"Invalid plan: <reason>"`), which is the contract of a 4xx, not
server-side evidence.

`tests/test_plan_route_5xx_error_contract.py` (4 nodes) pins it:

| node | property |
|---|---|
| `test_the_live_plan_route_discloses_no_cause` | AST scan of the live file finds no 5xx echo |
| `test_detector_flags_the_measured_pre_repair_shape` | **negative control** — the pre-repair shape *and* its f-string variant are reported |
| `test_detector_stays_silent_on_a_repaired_handler_and_a_4xx_echo` | **positive control** — silence is only meaningful if the detector can be silent |
| `test_a_failing_step_returns_500_without_the_internal_cause` | behavioural: `500`, marker absent from the body, marker **present in the log** |

The detector is an AST scan over `ast.ExceptHandler` -> `raise HTTPException(status_code>=500,
detail=<expression referencing the caught name>)`, excluding nested function bodies. A text
match would have been satisfied by the module docstring.

---

## 5. Verification

| scope | result |
|---|---|
| `tests/test_plan_route_5xx_error_contract.py` | **4 passed** |
| touched-route suites (`test_kernel_plan_perimeter.py`, `test_tool_execution_perimeter.py`) + `tests/architecture` + new file | **63 passed** |
| gate-integrity (`test_m02a_ci_gate_integrity.py`, `test_ci_gate_trigger_coverage.py`, `test_ci_suite_collection_continuation.py`, `test_workflow_injection_boundary.py`) | **326 passed** |
| CP10 mutation boundary judge over the staged diff | `Mutation boundary PASS`, exit 0 |

### 5.1 Live negative control on the real file — the only control that proves the guard bites

| step | result |
|---|---|
| revert `run_plan` to `detail=str(e)` | `2 failed, 2 passed` — exactly the live pin and the behavioural node |
| the disclosure, observed | `{"detail":"INTERNAL-MARKER-4c1f7d"}` |
| restore byte-identically (`sha256sum -c` -> `api/plan_routes.py: OK`) | `4 passed` |

The two detector controls stayed green in both directions, which is the intended shape: they
test the detector, not the file.

### 5.2 Full-suite node set — measured on both trees

| tree | result | nodes |
|---|---|---|
| `main` `cb284195` (console toolchain **absent**) | `22 failed, 4251 passed, 22 skipped, 1 error in 295.01s` | 23, `17b3b704...` |
| branch (console toolchain **installed**, §2.1) | `12 failed, 4265 passed, 22 skipped, 1 error in 291.73s` | 13, `e7d8341c...` |

`comm -3` on the two sorted node-id lists yields **zero** branch-only nodes. The 10-node
reduction is exactly `test_mission_lifecycle_adapter_contract.py`, which passes once the
console toolchain exists (§2.1) — not a repair, an environment delta between the two runs.
The arithmetic closes: `4251 + 10 + 4 = 4265` passed, where 4 is this PR's new file.

The comparison that binds is the node *set*, not the totals: no node is added, and no
existing assertion is touched.

---

## 6. Composition

`api/plan_routes.py` is touched by **0** of the 63 open PRs (`grep plan_routes` over the
per-PR file inventory -> 0 matches), and no open PR adds
`tests/test_plan_route_5xx_error_contract.py`. #729 introduces `api/http_failure.py` with an
equivalent helper; this change deliberately does **not** import it, because that module does
not exist on `main` and a cross-PR import would make this branch unbuildable on its own. If
#729 merges first, folding this handler onto the shared helper is a two-line follow-on and
not a conflict.

---

## 7. Not claimed / limitations

- No merge, no deployment, no production-parity claim beyond §1.1 revision identity, no
  acceptance.
- The class is closed **for this file only**. A corpus-wide detector is a separate,
  sovereign-scoped workstream: it cannot be green until the four owned repairs land, and a
  guard that is red on `main` is not a guard.
- `api/plan_routes.py` was not line-count constrained; `api/main.py` is untouched
  (2 597 / 2 600).
- The change alters an error **message**, not control flow: the route still returns `500`
  for an internal failure, and still `400` for a caller-caused one.

---

## 8. Next-action block

**Current state.** `main` = `cb284195`, unchanged. Production revision = `cb284195`
(VERIFIED, revision identity only). 63 open PRs: 62 drafts, 1 ready (`#679`,
`ELIGIBLE_TO_MERGE` advisory, head unchanged since cycle 23). This PR is a draft on
`gate-hygiene/plan-route-5xx-disclosure-01`.

**Evidence.** §1 state re-derivation; §1.1 production revision; §2 node set `17b3b704...`
identical to cycle 24; §2.1 the mission-lifecycle classification verified by measurement and
by naming its execution site; §3 the ownership matrix that identifies the one unowned
instance; §5 verification and the live negative control.

**Blocker.** Human, unchanged: nothing merges until a human reviews a candidate. Not an
engineering gap, and no agent may cross it.

**Authorized action for the next cycle.** Re-derive `main`, the production revision and the
queue (one read each); re-run the full suite and classify the node set by identity; re-run the
duplicate-path scan over the open-PR inventory before trusting the queue; re-assess any
newly-ready candidate. If the four owned 5xx repairs have merged, the corpus-wide detector
becomes green and is then the correct next change — measure it, do not assume it.

**Forbidden.** Merge execution, draft conversion, push to `main`, force-push,
protection/check bypass, deployment, provider configuration, acceptance, and any claim of
production parity beyond revision identity.

**Completion condition.** State re-derived with zero drift; the node set re-classified by
identity; one unowned defect closed with a guard proven to fail on the pre-repair shape; the
human blocker named.
