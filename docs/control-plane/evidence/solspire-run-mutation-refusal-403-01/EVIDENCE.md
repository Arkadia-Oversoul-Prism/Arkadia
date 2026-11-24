# SolSpire `/solspire/run` refused a mutation plan as an opaque 500

**Workstream:** `solspire-run-mutation-refusal-403-01`
**Observed:** 2026-11-24T01:17:56Z
**Base `main`:** `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**Disposition:** implemented on an isolated branch; **no merge, deployment or acceptance claimed.**

---

## 1. The defect

`solspire/execution_runtime.py::ExecutionRuntime.execute` refuses an engineering mutation
plan by **raising** `PermissionError` before a worker thread exists:

```python
blocked = [s.get("tool") for s in plan.steps if s.get("tool") in _ENGINEERING_MUTATION_TOOLS]
if blocked:
    raise PermissionError(
        "Engineering mutation is disabled in SolSpire ExecutionRuntime; "
        "use the governed Weaver K15 → K3 path. "
        f"Blocked tools: {', '.join(blocked)}"
    )
```

`_ENGINEERING_MUTATION_TOOLS = frozenset({"fs_write", "github_commit", "git_commit", "git_push"})`.

`solspire/console_router.py::_execute_run` — the single canonical run pipeline behind both
`POST /solspire/run` and `POST /solspire/projects/{id}/run` — called it **without** handling
that raise, so the refusal surfaced as an unhandled server error:

```python
    execution = get_runtime().execute(plan, owner_uid=user["uid"])   # PermissionError → HTTP 500
```

The boundary itself held (nothing mutated, no worker thread was created). What was wrong is
the **report**: a caller received `500 Internal Server Error`, which is indistinguishable from
a broken backend, instead of an attributable refusal naming the governed path.

### 1.1 The refusal is reachable from ordinary model output

The plan is produced by the planner, and nothing between the model and the runtime filters
mutation tools:

| stage | filter |
|---|---|
| `Planner._llm_plan` (`solspire/planner.py:120-148`) | asks the model not to emit `fs_write`/`git_commit`/… in the **prompt**, then keeps every step where `"tool" in s` |
| `Planner.validate_plan` (`solspire/planner.py:93-103`) | structure only: non-empty list, `<= MAX_STEPS`, each step a dict with a `tool` key — **no tool allowlist** |
| `_execute_run` | no `except PermissionError` |

A prompt instruction is not an enforcement point. Any model output that names a mutation tool
— an instruction-following failure, or a request crafted to induce one — reached the raise.

## 2. Reproduction (pre-repair)

Driven through the **real route** with the planner stubbed to emit one step, and
`TestClient(raise_server_exceptions=False)` so the transport status is observable rather than
re-raised by the test client:

```console
$ PYTHONPATH=$PWD:$PWD/archive/legacy_python python /tmp/repro_mutation_500.py
[AUTH] FIREBASE_SERVICE_ACCOUNT_JSON not set — running in dev-mode ...
STATUS: 500
BODY: Internal Server Error
```

## 3. The repair

One bounded change in `solspire/console_router.py::_execute_run` (6 lines):

```python
    try:
        execution = get_runtime().execute(plan, owner_uid=user["uid"])
    except PermissionError as exc:
        # The runtime refuses an engineering mutation plan before any worker thread
        # exists. Surface that as a governed refusal, not an opaque 500.
        raise HTTPException(status_code=403, detail=f"MUTATION_DISABLED: {exc}") from exc
```

Post-repair, the same request:

```console
STATUS: 403
BODY: {"detail":"MUTATION_DISABLED: Engineering mutation is disabled in SolSpire ExecutionRuntime; use the governed Weaver K15 → K3 path. Blocked tools: fs_write"}
```

### 3.1 Why `403` and why a string `detail`

* `403` matches this file's established authorization-refusal convention
  (`eden_ops_02_routes.py`, `enterprise_router.py`, `console_authority_router.py` all answer
  `403` for a refused capability) and separates it from `422` "Planner produced an invalid
  plan" — the plan here is structurally valid, it is *not permitted at this runtime*.
* The `MUTATION_DISABLED` prefix reuses the stable machine-readable code already emitted by
  `solspire/tools_github.py::commit_file` (`{"status": "BLOCKED", "code": "MUTATION_DISABLED"}`),
  so one vocabulary describes the boundary in both places.
* `detail` is a **string**, not a dict. `web/arkadia_console/src/lib/apiClient.ts:98-102`
  renders the error as `String(payload.detail)`; a dict would surface as `[object Object]` in
  the active console. Every one of the 20 other `HTTPException`s in this file passes a string.

The mutation boundary is **unchanged**: `execute()` still raises before any worker thread is
created, and the route only translates the raise. No tool allowlist was added to the planner
and `validate_plan` was not widened — the runtime remains the single enforcement point.

## 4. Regression guard

Three tests appended to `tests/test_solspire_route_composition.py`, chosen because its gate
(`.github/workflows/solspire-route-composition.yml`) is `pull_request`-triggered with
`paths: solspire/**` and therefore executes on this very change. Adding them to
`tests/test_solspire_r4_run_orchestration.py` would have placed them in a workflow that
triggers **only** on `push` to `recon/solspire-r0` — executed by no gate on a PR to `main`.

| test | asserts |
|---|---|
| `test_a_mutation_plan_is_refused_with_a_governed_403` | status `403`; detail starts `MUTATION_DISABLED:`; names `K15`, `K3` and the blocked tool |
| `test_negative_control_a_read_only_plan_is_not_refused` | an `fs_list` plan is **not** `403` and carries no `MUTATION_DISABLED` — proves the refusal is attributable to the mutation tool, not to the wrapper |
| `test_a_refused_plan_creates_no_execution` | no execution is recorded for the refused plan id — the boundary still holds |

### 4.1 Live negative control

Reverting **only** the source fix (`git checkout -- solspire/console_router.py`), then restoring
byte-identically:

```console
=== PRE-FIX ===
FAILED tests/test_solspire_route_composition.py::test_a_mutation_plan_is_refused_with_a_governed_403
1 failed, 3 passed in 1.05s
=== RESTORED ===
4 passed in 1.00s
=== byte-identical restore? ===
IDENTICAL
```

The guard reddens on the defect it claims to detect. The negative control (`fs_list`) passes in
both states by design — it exists to show the detector is not simply "any run is refused".

## 5. Verification

| command | result |
|---|---|
| `pytest tests/test_solspire_route_composition.py -q` | **4 passed** |
| `pytest tests/test_solspire_r4_run_orchestration.py tests/test_solspire_route_composition_ci_wiring.py tests/test_voice_intent.py tests/test_solspire_ownership.py -q` | **99 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile solspire/console_router.py tests/test_solspire_route_composition.py` | OK |
| `wc -l api/main.py` | **2597** (budget 2600; file untouched) |
| `printf '<changed paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, exit 0 |
| `python scripts/lane_state.py --check` | exit 0 |
| `corepack pnpm build` (`web/arkadia_console`) | clean — `tsc --noEmit` + 170 modules, no type errors |
| `corepack pnpm exec vitest run` (`web/arkadia_console`) | **61 passed** (8 files) |

### 5.1 Failing/error node set is unchanged

Full suite on the base revision, then on the composed change, in the **same environment**:

```console
$ pytest tests/ -q -rEf --continue-on-collection-errors
19 failed, 4250 passed, 22 skipped, 6 warnings, 1 error in 287.89s   # base bb19aabd
```

Failing/error node set at base: **20 nodes**, sha256
`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` — identical to the
recorded `8d70e46e…` baseline. Post-change measurement is recorded in §5.2; the claim is
**node-set identity**, never a totals delta. Passed counts move with the installed dependency
set and with the three added nodes.

### 5.2 Post-change full suite

Measured after the repair:

```console
$ pytest tests/ -q -rEf --continue-on-collection-errors
9 failed, 4263 passed, 22 skipped, 6 warnings, 1 error in 282.23s
```

Node set: **10 nodes**, sha256
`11a348481cf81125894a7094c27e0810c09c7e8f0d96733852e671f57ca597b6`.

The two runs differ by **10 nodes and +13 passed**, and neither delta is caused by this change.
Between the two runs `web/arkadia_console/node_modules` was installed (`corepack pnpm install
--frozen-lockfile`), and `tests/test_mission_lifecycle_adapter_contract.py:37` resolves
`web/arkadia_console/node_modules/typescript/lib/typescript.js` to drive the real adapter. That
file's **10** nodes are therefore environment-gated, not repository debt — exactly the class
cycle 04 recorded as "environment-only". They pass in isolation now (`10 passed in 3.18s`).

Attribution by **node identity**, not by count:

```console
$ comm -23 /tmp/baseline_nodes.txt /tmp/after_nodes.txt    # 10 lines: the mission_lifecycle nodes
$ comm -13 /tmp/baseline_nodes.txt /tmp/after_nodes.txt    # empty
```

**Zero** nodes appear only after the change — no regression is introduced. The `+13 passed`
decomposes exactly as the 10 newly-unblocked environment nodes plus the 3 added nodes
(`--collect-only tests/test_solspire_route_composition.py` 1 → 4).

## 6. Measured but **not** repaired — separate proposed work

Recorded rather than repaired, per the contract's "do not expand scope to repair adjacent
failures". Each is a distinct defect with a distinct review question.

### 6.1 `tests/test_solspire_r3_execution_runtime.py` pins the pre-`144d6015` refusal shape

`test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` expects `execute()` to
**return** an `Execution` whose `results[0]["code"] == "MUTATION_DISABLED"`. Commit `144d6015`
("Converge SolSpire and Weaver mutation boundaries", *"route solspire engineering mutation away
from generic runtime"*) deliberately changed the runtime to **raise** instead, and the test was
never updated — `git log -S "PermissionError" -- tests/test_solspire_r3_execution_runtime.py` is
empty. The test has failed since that commit.

Re-pinning it to `pytest.raises(PermissionError)` would *strengthen* the assertion, so it is not
a weakening — but it changes what a **mutation-boundary** test asserts, which deserves its own
review rather than riding along with an error-handling fix. Note the two are complementary, not
contradictory: `execute()` raises, and the route (§3) translates the raise.

### 6.2 `tests/test_solspire_r1_governance_convergence.py` feeds different inputs to each builder

`test_r1_solspire_builders_delegate_to_weaver` calls the SolSpire adapter **without** `pass_id`,
so it derives `mvp1-50c0ee9b89` from the patch hash, then compares against a Weaver call made
with `pass_id="mvp1-r1-patch"`. The comparison is not like-for-like and fails on the id it did
not supply:

```console
E  AssertionError: assert 'mvp1-50c0ee9b89' == 'mvp1-r1-patch'
```

Supplying the same `pass_id` and `objective` to both builders yields **zero** mismatches across
all 15 canonical keys — the delegation the test exists to prove is exact:

```console
MISMATCHES with identical inputs: {}
```

### 6.3 `test_r1_weaver_governance_is_canonical` pins a location a refactor moved

The test asserts `"execute_patch" in inspect.getsource(weaver/governance.py)`. `execute_patch`
has **never** been defined in `governance.py` (`git log --all -S "def execute_patch" -- weaver/governance.py`
→ empty); it lives in `weaver/execution.py:173`. `b555b074` exposed it through governance, then
`36bdcf01` ("keep governance module narrowly scoped") deliberately removed it from the imports
and `__all__`. The test was not updated. The property it states — Weaver owns execution and
SolSpire delegates — still holds and is stronger than a source-location pin:
`solspire/project_execution.py:14` imports `execute_patch` **from `weaver.execution`**.

### 6.4 Workflow coverage of the four `solspire-r*-validation.yml` gates

`solspire-r1/r3/r4-validation.yml` trigger only on `push` to `recon/solspire-r0`, so they are
inert for `main` and for pull requests. The three findings above therefore cannot fail any PR
gate today; the tests are visible only when a human runs the suite. This is the same
"a guard no workflow executes is decoration" class already recorded for
`test_baseline_fingerprint.py` and `test_boot_syntax_boundary.py`. Fixing it changes gate
selection across four workflows and is a separate bounded workstream.

## 7. Next-action block

**Current state.** `main` = `bb19aabd`; this change is on an isolated branch. `api/main.py`
untouched (2597/2600). Console builds and its 61 vitest tests pass. Full-suite failing/error
node set identical to base.

**Evidence.** Sections 2–5; every command is reproducible as written.

**Blockers.** Merge execution is human-only (GOV-03). This PR is a **draft** and stays one:
OpenHands does not inherit merge authority, and marking a PR ready because an agent finished a
turn is prohibited.

**Authorized next action.** A human reviews this branch for merge. On a later cycle an agent may
take one of §6.1–§6.3 as a separate bounded change, or §6.4 as a gate-selection workstream.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; widening the planner/`validate_plan`
allowlist to make the refusal unreachable (that would remove the boundary rather than report it).

**Completion condition.** Complete when this evidence is reviewable on the branch, with `main`
unmodified and no merge, deployment or acceptance claimed.
