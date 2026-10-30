# AEAS-01 · P0.3 — Repository & change inspection in the Engineering Lab

**Directive:** issue #590 — *Engineering Lab becomes the execution substrate for Arkadia One*
**Slice:** P0.3 — "Complete inspectable engineering output: show actual file or diff information
when available … identify the source revision against which the task was executed."
**Date:** 2026-10-29
**Branch:** `freebuff/f6a4fd1dd162a73f0b053afb` (base: `d9a16f12`)

---

## 1. Why this slice

Measured before the change: the Lab page (`web/arkadia_console/src/pages/EngineeringLabPage.tsx`)
had **no repository surface at all**. `/api/lab/engineering/overview` returns sessions, agents,
loop, gateway and authority readings — no branch, no source revision, no working-tree state, no
diff. The mission workspace could read a file *named by the operator* through a bounded run, but
"see the actual repository / branch / source revision / working-tree state" and "view a diff,
identify changed files and their change status" (directive §2.1, §2.5) had no native surface.

The capability underneath already existed and was reused rather than replaced:
`lab/observatory/git.py::repository_state` and the bounded `Sandbox` read-only git boundary
(`enforce_git_read_only`, closed L1 terminal grammar) that every Lab run already executes through.

Coordination: open PR **#591** (`feat/dea-01-mission-state-guard-01`, draft) is the other active
implementation stream on this directive. It owns `MissionWorkspace.tsx`, `missionContract.ts`,
`pages/EngineeringLabPage.tsx` (its own edits), `tests/test_lab_mission_workspace_contract.py`.
**This slice touches none of those** except a two-line mount in the Lab page (one import, one
`<LabRepositoryContext />` element). No file was edited by two streams.

---

## 2. What was implemented

### Backend (serves the reading)

| File | Change |
|---|---|
| `lab/engineering_lab/repository.py` | **new** — `observe_repository(root)`: porcelain parsing, change labels, bounded staged/unstaged diffs, truthful degradation |
| `lab/engineering_lab/runtime.py` | `workspace_root()` — one public accessor over the runtime's default root, so inspection and execution cannot drift onto two roots |
| `api/lab_routes.py` | `GET /api/lab/engineering/repository` (`engineering_repository`), authenticated, read-only |

Response shape (`arkadia.lab.repository/1`):

```jsonc
{
  "schema": "arkadia.lab.repository/1",
  "observed_at": "…",
  "repository": { "branch", "head", "short_head", "remote", "remote_redacted",
                  "status": "observed|unavailable", "reason", "clean": true|false|null },
  "changes":     { "status": "observed|unavailable", "reason", "count": int|null,
                   "truncated", "files": [{ "code", "label", "path",
                                            "original_path", "staged", "unstaged" }] },
  "diff":        { "unstaged": {status,text,chars,truncated,reason},
                   "staged":   {status,text,chars,truncated,reason} },
  "boundary": "read-only git observation through the bounded sandbox: no stage, checkout, fetch, write, or push is performed"
}
```

Truthfulness rules enforced in code:

* a failed git read → `status="unavailable"` **with the reason**; `clean` stays `null` (UNKNOWN) and
  `count` stays `null` — never `clean: true`, never `0 files`;
* `diff.status` distinguishes `observed` / `empty` ("the read succeeded and printed nothing") /
  `unavailable` (+reason); output is bounded and reports `truncated`;
* `count` is what git printed; the `files` list is capped (`truncated: true`) — the cap bounds
  rendering, never the reading;
* the only commands issued are read-only git subcommands inside a `write_allowed=False` sandbox.

### Frontend (the operator surface)

| File | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | `labRepository` registry entry (one registry, no page-local path) |
| `web/arkadia_console/src/components/lab/labRepository.ts` | **new** — pure projection, dependency-free, executed by the contract test under Node |
| `web/arkadia_console/src/components/lab/LabRepositoryContext.tsx` | **new** — panel: facts, change list, staged/unstaged diff disclosures, loading/empty/unavailable/error states, `Re-observe` |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | mount only (2 lines) |

The panel performs **reads only** — no POST/PUT/PATCH/DELETE appears in its source, and it exposes
no stage/checkout/reset control, because the contract it reads has no such operation.

### Tests

| File | Nodes | Covers |
|---|---|---|
| `tests/test_lab_repository_observation.py` | 13 | real temp git repo: clean/modified/staged/unstaged/untracked/rename, diff bounds, list cap, **negative controls** (non-git dir → unavailable, not clean; absent root), no-mutation (status/HEAD/`diff --cached` byte-identical before vs after), route GET+auth, handler observes `workspace_root()`, anonymous → 401 |
| `tests/test_lab_repository_surface_contract.py` | 12 | registry entry is served by `api.main:app`, no page-local literal, **reads only**, page mount, handler field binding, and the projection **executed under Node** (absent `clean` → `UNKNOWN`; absent `count` → `UNKNOWN`; unavailable diff carries its reason; empty diff ≠ unread diff) |

---

## 3. Verification (commands actually run)

```
.venv/bin/python -m pytest tests/test_lab_repository_observation.py -q
  → 13 passed in 1.49s                                   (exit 0)

.venv/bin/python -m pytest tests/test_lab_repository_surface_contract.py -q
  → 12 passed                                            (exit 0)

.venv/bin/python -m pytest <18 lab/console/guard files> -q
  → 354 passed, 2 skipped in 8.04s                       (exit 0)
    (skips are pre-existing opt-ins: N-ATLaS live validation, node-absent guard)

corepack pnpm build            # tsc --noEmit && vite build
  → ✓ 113 modules transformed, built in 2.76s            (exit 0)

git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge
  → "Mutation boundary PASS", exit 0   (all 9 changed paths admitted)

# Real served route, not TestClient — uvicorn api.main:app :8000
GET /api/lab/engineering/repository           → 401 (gated, unauthenticated)
GET /openapi.json → path present, methods = ["get"]

# The dev origin proxies to the backend (vite :3000 → :8000)
GET /api/lab/engineering/repository via proxy → 401
GET /api/version via proxy                    → 200 (json)

# The observation run against THIS working tree (live, real git):
branch=freebuff/f6a4fd1dd162a73f0b053afb  short_head=d9a16f1269b2  clean=False
changes: observed, count=9 — exactly the 9 changed paths of this slice,
  each with its porcelain code (' M' modified ×5, ' A' added ×4)
diff.staged=empty(0 chars)  diff.unstaged=observed(49094 chars)
```

**Browser workflow:** no browser automation exists in this Cloud environment (no Playwright/Chromium
driven from here), so no screenshot or click-through is claimed. The console dev server runs bound to
`0.0.0.0:3000` with the preview hostname answering `200`, backend proxied, and is open in the
preview panel. What is proven for the UI is the build, the registry/served-route contract, and the
**executed** projection; what is *not* proven is an authenticated human session rendering the panel
against Firebase identity.

---

## 4. Capability status

| Capability | Status | Evidence |
|---|---|---|
| Repository branch / source revision reading | **LIVE** | executed `observe_repository` above; handler test |
| Working-tree change inventory with change status | **LIVE** | 9-file real inventory with porcelain codes |
| Real staged/unstaged diff through the Lab boundary | **LIVE** | `diff.unstaged` 49 094 chars observed |
| Served, authenticated, GET-only route | **LIVE** | real HTTP 401 + openapi `["get"]` |
| Registry-bound console read + panel mount | **LIVE** | registry guard (served-path) + build |
| Failure states (unavailable/empty/loading/error) | **LIVE** | negative controls executed (Python + Node) |
| Authenticated operator rendering the panel | **PARTIAL** | build + contract proven; no browser session here |
| **Running tests through the Lab** (`pytest` in sandbox) | **UNAVAILABLE** | L1 terminal grammar is a closed set `{git, echo, pwd, true, false}`; widening it executes repository code inside the boundary — a **human authority decision**, not taken here |
| Model-backed worker dispatch (`run-agent`) | **UNAVAILABLE** | gateway binds only the `n_atlas` adapter; no inference adapter is bound for `ollama`/`gemini` in this environment, so a dispatch would return `BLOCKED` truthfully |
| Merge / deploy / repository mutation | **NOT IMPLEMENTED — refused by design** | forbidden marker guard + sandbox read-only grammar |

---

## 5. Governance

* **Authorization used:** the Lab's own `require_auth` (router-level `require_lab_auth`); no
  authority, approval, or identity change. No `require_sovereign` weakening, no new public path.
* **Scope:** 9 paths, all inside `lab/`, `api/lab_routes.py`, `tests/`, `web/arkadia_console/`.
  CP10 mutation-boundary judge passes on the exact diff.
* **No merge, no push to main, no deployment, no production config or credential touched.**
  The change is committed on `freebuff/f6a4fd1dd162a73f0b053afb` and opened as a PR for human review.
* **No fabricated state:** every status the surface shows is produced by an executed git read or
  rendered as `UNKNOWN`/`unavailable` with its reason; there is no LIVE/SUCCESS decoration.
* **No parallel-writer overlap** with open PR #591 (see §1).

### Pre-existing failures observed on the base revision (NOT introduced here)

1. `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` — asserts
   router dependency name `require_auth`; the router now declares `require_lab_auth`. Verified by
   stashing this change and re-running: **2 failed on the base tree as well**.
2. `tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` —
   `/api/lab/engineering/n-atlas/{run,test-session}` are not in `ALLOWED_MUTATION_ENDPOINTS`.
   Same stash-run: pre-existing.
3. `tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main`
   — fails **closed** because this clone has no resolvable `main` ref
   (`git rev-parse main` → *Needed a single revision*; only `freebuff-base` and this branch exist).
   The guard reads lane docs and git history only, neither touched by this change.

Recorded, not repaired: repairing adjacent failures is out of this slice's authorized scope.

---

## 6. Remaining gap → next bounded task

**Most important unresolved acceptance criterion:** DoD 7 — *"the operator can … run tests"* —
through the Lab. The bounded sandbox refuses any binary outside `L1_TERMINAL_BINARIES`, so no test
command can execute; this is the substrate's deliberate execution boundary (ADR/GATE L1), and
widening it means repository code executes inside the Lab's hands.

**Smallest next implementation step:** a `test` operation kind in `execute_bounded_task` that runs a
**declared, pinned test command** inside the container boundary (`SandboxPolicy.containerized`,
already implemented and used by the project canvas), records the real exit code, stdout/stderr
tail, and duration as an observation + evidence, and is refused with a clear reason when the
container runtime is not configured.

**Dependency/authorization needed:** explicit human decision that (a) test execution is permitted
inside the containerized boundary for an authorized session, and (b) the pinned command list. Until
that decision, the capability stays `UNAVAILABLE` and is reported as such — not mocked.
