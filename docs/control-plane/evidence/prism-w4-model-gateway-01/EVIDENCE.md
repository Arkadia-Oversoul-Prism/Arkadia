# Workstream 4 — Engineering Lab model gateway read surface

**Slice:** 07 — `GET /api/lab/engineering/gateway`
**Branch:** `feat/prism-next2-04-run-evidence-trace`
**PR:** #432 (draft)
**Authority:** implement, test, commit, report. **No merge, no deployment, no acceptance.**

---

## 1. Why this surface, and why now

`endpoints.labGateway` is already declared in the shared registry
(`web/arkadia_console/src/lib/endpoints.ts:34`) and was **unwired** — no component
read it. It is therefore the next verified read surface that needs **no** registry
change, which is the constraint the automations surface is blocked on.

The gateway is also where the Lab states its own honesty rule, verbatim from
`lab/engineering_lab/gateway.py`:

> Selection never fabricates availability. If nothing is configured the result
> status is `UNAVAILABLE` and the caller must treat model work as blocked — not
> silently substitute a stub.

A surface that renders this badly would undo the rule at the last step, so the
non-collapses are the point of the slice, not decoration.

---

## 2. Verified route / auth / data contract

| | |
|---|---|
| Method + path | `GET /api/lab/engineering/gateway` |
| Router | `APIRouter(prefix="/api/lab", dependencies=[Depends(require_lab_auth)])` (`api/lab_routes.py:64`) |
| Handler | `async def model_gateway() -> dict: return describe_gateway()` (`api/lab_routes.py:362`) |
| Auth | Lab router default `require_lab_auth` → `require_auth`; the path is **not** in `_PUBLIC_NATLAS_PATHS`, so it is owner-scoped like the rest of the Lab |
| Response | `ModelGateway.to_dict()` → `{local_providers, remote_providers, agent_providers, catalog}` |

Catalog entry = `ModelDescriptor.to_dict()`
(`gateway.py:85`): `{provider, model, config_class, configured, status, detail, cost_note}`.

Measured by invoking the handler directly in this environment:

```
top-level keys: ['local_providers', 'remote_providers', 'agent_providers', 'catalog']
catalog entries: 10
statuses: ['UNCONFIGURED']          # nothing configured here
config_classes: ['AGENT_RUNTIME', 'LOCAL', 'REMOTE']
LOCAL  = (ollama, llama_cpp, openai_compatible_local, n_atlas)
REMOTE = (gemini, openai_compatible, anthropic_compatible)
AGENT  = (native_arkadia_agent, openhands_compatible, acp_compatible)
union(LOCAL, REMOTE, AGENT) == set(CONFIG_CLASSES)  -> True
```

The groups **partition** the catalog exactly, so a naive group-by is lossless
today. The projection reports the cases where that would stop being true.

---

## 3. The non-collapses this surface preserves

| Non-collapse | Where it comes from | How the projection keeps it |
|---|---|---|
| `configured` != `AVAILABLE` | `configured` records an env var; `status` records a probe | separate fields; `configured_but_not_available` names the gap |
| `AVAILABLE` != authorized to run | the gateway is a description, not an authority | `authority_granted` is a literal `false`; the verdict note says "not an authorization" |
| `LOCAL` != free | `cost_note` = "cost not asserted; provider tiers are not assumed free" | `cost_asserted` reads the note; no class is rendered as free |
| `AGENT_RUNTIME` != probed | `describe()` returns `UNCONFIGURED` for every agent runtime, never probing | `agent_runtime_reported_available` is surfaced; a test asserts the handler never marks one `AVAILABLE` |

---

## 4. Missing / partial readings

Each is a first-class ledger field, not a silent omission:

* `ungrouped_providers` — a catalog provider in **no** declared group (a naive
  group-by would drop it and under-report the catalog).
* `missing_from_catalog` (per group) — a group naming a provider the catalog does
  not describe.
* `duplicate_providers` — a provider described more than once.
* `unknown_config_class` — an entry whose class is not in `CONFIG_CLASSES`.
* `group_class_mismatch` (per group) — declared under one group, classified as
  another.

`gatewayVerdict` returns one of three states — `NO_CATALOG`,
`MODEL_WORK_BLOCKED`, `PROVIDER_AVAILABLE` — derived only from the ledger, so an
empty or unconfigured gateway can never read as ready.

---

## 5. Read-only by construction

* One `useHydration` / one `apiRequest`, to the **declared** `endpoints.labGateway`
  entry. The path is not inlined.
* `labGateway.ts` imports **nothing** — no React, no client, no store — so it
  cannot reach anything mutating even by accident.
* No `<button>`, `onClick`, or `onSubmit` in the surface: it renders readings, not
  actions. Selecting or invoking a model is a mutating act the console holds no
  authority for.
* `describe_gateway` is asserted (via `ast`) to have exactly one `return` of
  `to_dict()` and to call none of `register_adapter` / `generate(` / `select(` — if
  the handler ever gained a side effect, this surface's claim would be wrong even
  though its own code is unchanged.
* **No shared file edited.** `lib/endpoints.ts`, `lib/types.ts`, `App.tsx`,
  `lib/router.ts` and `lib/surfaces.ts` are untouched.

---

## 6. Changed paths

| Path | Role |
|---|---|
| `web/arkadia_console/src/components/lab/labGateway.ts` | pure projection (no imports) |
| `web/arkadia_console/src/components/lab/LabModelGateway.tsx` | read-only renderer |
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | mounts the surface |
| `tests/test_prism_w4_model_gateway.py` | handler oracle + projection execution (16 tests) |
| `tests/test_lab_model_gateway_contract.py` | read-only ceiling + wiring + vocabulary (16 tests) |

---

## 7. Measured result

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Summary | Failing/error node set sha256 | Nodes |
|---|---|---|---|
| `main` `f390526a` (detached worktree) | 27F / 2342P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |
| branch (slice 06 + 07) | 27F / 2411P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |

`diff` on the sorted node sets is **empty** — no node fixed or broken. The
`+69 passed` is the four new test files: `--collect-only` reports 18 + 19 + 16 +
16 = **69**, matching the delta exactly.

* `tsc --noEmit && vite build` → clean; `dist/assets/index-BinH0HjF.js` 76.54 kB.
* `python -m py_compile api/main.py` → OK (2499 lines, within the 2600 budget).
* `python scripts/cp10_mutation_boundary_policy.py --judge` on all new paths → PASS.

The projection is **executed**, not grepped: `labGateway.ts` is run under Node
against the real `describe_gateway()` output, so `MODEL_WORK_BLOCKED` in this
environment is an observed result. If Node is unavailable those tests skip with a
stated reason.

---

## 8. Limitations / next

* Nothing here authorizes running a model. `MODEL_WORK_BLOCKED` is the correct
  reading in this environment and is **not** a defect to repair.
* The automations read surface remains **blocked** on Workstream 1's
  `labAutomations` registry entry.
* Not claimed: merge, deployment, production parity, acceptance.

**Next bounded move:** the next verified Lab/Arkana/Weaver read surface whose
registry entry already exists — `endpoints.labOverview` (`GET /api/lab/overview`)
is declared and unwired.

_This document was written by an AI agent (OpenHands) on behalf of the repository owner._
