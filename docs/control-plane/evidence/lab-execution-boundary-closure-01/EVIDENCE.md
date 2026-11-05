# Execution-boundary closure — Engineering Lab MVP vertical slice

**Branch:** `fix/lab-execution-boundary-01`
**Base:** `main` @ `4ce6fc174b3101232c992f56feb41f2cef064767`
**Status:** IMPLEMENTED · locally VERIFIED · **not merged, not deployed, not accepted**
**Merge authority:** reserved to the human sovereign.

---

## 0. Baseline correction (important)

The brief's baseline was stale. Live state at the start of this run:

| Ref | Brief said | **Live** |
|---|---|---|
| `main` | `4ff76c15` | **`4ce6fc17`** |
| #623 | open draft | **merged** (`d44b26b3`) |
| #624 | open draft | **merged** (`f6d165ed`) |
| #625 | open draft | **merged** (`e5ba02cd`) |
| #626 | open draft | **merged** (`4ce6fc17`) |

All four PRs landed. The merge-authority contradiction is therefore **moot for
these four** — the human sovereign merged them. This work starts from
`4ce6fc17`, not `4ff76c15`.

---

## 1. The defect (reproduced, not inferred)

`execute_bounded_task` enforced authorization **only** for `test` operations.
`write` and `run` were gated solely by `task.requires_write` — a *client-supplied
boolean*. A session with **no linked authorization at all** could write to disk.

Reproduction on `4ce6fc17` (before the fix):

```
session state after open : PROPOSED
session authorization_ref: None
session state after transition: AUTHORIZED
session authorization_ref     : None
run result_state: IMPLEMENTED
file written on disk: True
BYPASS CONFIRMED: a write executed with no linked authorization.
```

Two further defects in the same boundary:

- `effective_tools()` skipped the authorization intersection entirely when
  `authorization_operations is None` — contradicting its own docstring, which
  says `None` must be treated as the empty set.
- `_authorization_operations()` returned `None` for a missing *or explicitly
  empty* grant, and never checked revocation, expiry or consumption.
- `api/lab_routes.py` built a `SandboxPolicy` from a **client-supplied**
  `sandbox_root` on the no-project branch.

---

## 2. The fix

| File | Change |
|---|---|
| `lab/engineering_lab/runtime.py` | `effective_tools` always intersects (`set(auth or ())`); new `_require_authorization_for()` dispatch gate; `_authorization_is_usable()` (revoked/expired/consumed); `_authorization_operations` now returns `None` for unusable grants; `execute_agent_loop` uses the same resolver |
| `lab/engineering_lab/store.py` | `revoke_authorization()`; `consume_authorization()` — atomic single-use via conditional `UPDATE ... WHERE json_extract(payload,'$.consumed_at') IS NULL` |
| `api/lab_routes.py` | client-supplied `sandbox_root` now **refused** (409); root is server-managed |
| `tests/test_lab_execution_boundary.py` | **new** — 13 tests incl. 2 negative controls |
| `tests/test_engineering_lab_substrate.py` | 2 tests that *encoded the defect* now link the grant and name the operation |
| `tests/test_engineering_lab_test_boundary.py` | fixture now scopes the grant to the real session id |

The gate runs at the **dispatch point**, for every consequential operation
(`write`, `run`, `test`), on **both** execution paths.

---

## 3. Verification (this run, this revision)

| Check | Result |
|---|---|
| `tests/test_lab_execution_boundary.py` | **13 passed** |
| Lab suite (substrate, lab, agent_loop, dispatch_truth, test_boundary, boundary) | **153 passed, 1 skipped, 0 failed** |
| `tests/architecture` | **11 passed** |
| `tests/test_authority_boundary.py` + enterprise boundary | **20 passed** |
| `corepack pnpm build` (`web/arkadia_console`) | **BUILD OK** |
| Acceptance flow (session→authorize→execute→evidence→READY_FOR_REVIEW) | **PASS** |

### Negative controls (the proof the tests detect the old behaviour)

New tests run against the **old** code (`git stash`):

```
11 failed, 1 passed
```

New tests against the **new** code:

```
13 passed
```

The two failures that remain in `tests/test_engineering_lab_api.py`
(`test_lab_router_is_read_only_and_authenticated`,
`test_lab_mutation_endpoints_are_exactly_the_lab_state_set`) are **identical on
baseline** — pre-existing debt, not a regression. Verified by stashing.

### Baseline attribution (by node identity, not count)

24 failures across the PR-state / read-model / governance-readings /
operational-projection suites are **byte-identical before and after** this
change (`diff` of sorted FAILED lists is empty). They are pre-existing `main`
debt.

---

## 4. Acceptance record

```
revision: 4ce6fc174b3101232c992f56feb41f2cef064767
1. session opened      : PROPOSED | auth: None
2. authorized          : AUTHORIZED | auth: AUTH-09c8c520f86b
3. executed            : result_state = IMPLEMENTED
   evidence_refs       : ['EVD-20d9045fea88']
   artifact_refs       : ['ART-609fabb089a8']
   merge/deploy/self   : False False False
4. session state       : READY_FOR_REVIEW
5. file on disk        : True

ACCEPTANCE: PASS
```

The flow is a real vertical slice: a bounded write executes **only** under a
linked, session-scoped, unexpired grant, produces evidence and an artifact, and
stops at `READY_FOR_REVIEW` with `merge=False`, `deploy=False`,
`self_authorized=False`.

---

## 5. Lifecycle guarantees — status

| Guarantee | Status |
|---|---|
| Expiry | **Implemented** — `_authorization_is_usable` + test |
| Revocation | **Implemented** — `revoke_authorization` + test |
| Single-use atomic consumption | **Implemented** — conditional UPDATE + test |
| Session-scoped grant | **Implemented** — `scope_ref` check + test |
| Governance principal | **Already correct** — resolves against `governance/roles.json` (`Flamekeeper`/`Govern`) and `require_sovereign` (`access_level >= 3`); 20 tests pass. No guessed role check. |
| `PENDING_APPROVALS` durability | **Contained, not fixed** — still a process-local dict. Pinned by `test_pending_approvals_is_explicitly_process_local`. The Lab authorization path *is* durable (`el_authorizations`). |

---

## 6. What could NOT be executed here (honest limits)

- **Full suite** — not run. Only targeted suites were executed; the repo's full
  CP10-B run needs the CI container and a Firebase config.
- **Authenticated browser flow** — not run. No Firebase web config in this
  sandbox; the authenticated Engineering Lab lens was deferred, as in prior
  passes.
- **Mobile/desktop visual acceptance** — not run. No browser harness here.
- **`scripts/lane_state_refresh.py --write`** — **not run**: no
  `GH_TOKEN`/`GITHUB_TOKEN` in the sandbox. The snapshot remains stale
  (base `46d85e2d` vs current `4ce6fc17`). This is a real, named gap.
- **Render deployment revision** — not identified. No Render API credential and
  no `render.yaml` in the repo; no deploy was triggered.
- **Lane 3 path gap** — confirmed (`LANE_OWNERSHIP["3"]` enumerates no `tests/`
  path, so `tests/test_knowledge_notes_boundary.py` matches no lane) but **not
  edited**: it is a shared/coordinator-owned artifact and changing another
  lane's ownership needs owner authorization.

---

## 7. Release-blocking items

1. **`PENDING_APPROVALS` is in-memory** — a restart drops queued tool
   approvals. Contained and documented; not a blocker for the Lab slice, which
   uses the durable `el_authorizations` table.
2. **Lane-state snapshot is stale** — needs a token-bearing run of
   `scripts/lane_state_refresh.py --write`.
3. **Lane 3 ownership gap** — one-line fix, owner-gated.
4. **24 pre-existing test failures** on `main` — baseline debt, outside this
   change's paths.

---

## 8. Non-claims

No merge. No deployment. No production configuration mutation. No governance
file edited. No other lane's ownership changed. No claim that any check passed
without the output above.
