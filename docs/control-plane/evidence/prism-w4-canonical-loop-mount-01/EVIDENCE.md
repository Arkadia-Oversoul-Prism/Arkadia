# Workstream 4 — canonical work-loop surface (mount) · evidence

**Branch:** `feat/prism-next9-04-canonical-loop-mount`
**PR:** opened as draft (Lane 4)
**Base:** `49809f45274f2f81b24e01fefdfb3009e8717495` (`main`)
**Instruction:** `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Defect (measured, not inferred)

`web/arkadia_console/src/components/lab/ExecutionLoop.tsx` was committed by an
earlier pass but is **orphaned** — defined and never imported or rendered. Measured
on `main` @ `49809f45`:

```
grep -rn "ExecutionLoop" web/arkadia_console/src/   ->  1 hit (the definition only)
```

So the Lab surface had no projection of the runtime's canonical work loop even
though the authenticated read that carries it already existed.

## 2. What is read (already declared; no registry edit)

The mount consumes the **already-declared** registry entry the page hydrates,
`endpoints.labEngineeringOverview` → `GET /api/lab/engineering/overview`
(`web/arkadia_console/src/lib/endpoints.ts`). The handler sets
`overview["loop"] = list(CANONICAL_LOOP)` (`lab/engineering_lab/runtime.py::overview`,
surfaced by `api/lab_routes.py`). No new endpoint, no Lane-1-owned file touched.

## 3. The slice

* `web/arkadia_console/src/pages/EngineeringLabPage.tsx` — import and render
  `<ExecutionLoop stages={readLoopStages(...)} />`, sourcing stages from the
  overview read; a malformed/absent payload yields **no** stages (the surface
  reports an unfilled definition rather than inferring one).

## 4. Verification (executed)

| Command | Result |
|---|---|
| `python -m pytest tests/test_prism_w4_canonical_loop_mount.py -q -rEf` | **12 passed** |
| `python -m pytest -q $(python scripts/console_contract_domain.py)` | **401 passed** (new guard is inside the derived domain) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `corepack pnpm build` (tsc --noEmit && vite build) | **built** (`dist/assets/index-C0nBQDvN.js`) |

### Handler oracle (executed, not asserted)

The guard drives the **real** `EngineeringLabRuntime` over an isolated SQLite DB +
event log and asserts `overview["loop"] == CANONICAL_LOOP`
(`DISCOVER, PLAN, EXECUTE, OBSERVE, EVIDENCE, PROPOSE, REVIEW, AUTHORIZE, VERIFY, RECORD`)
and that the overview's authority block keeps `autonomous_merge` / `autonomous_deploy`
false with `human_authorization_required` true.

### Negative control (live, on the real file)

Removing the `<ExecutionLoop ... />` mount from the real `EngineeringLabPage.tsx`
reddens `test_lab_page_renders_the_canonical_loop_surface` (**1 failed, 11 passed**);
restoring it byte-identically returns **12 passed**. The detector cannot be disarmed
by a rewrite that leaves the surface unrendered.

## 5. Read-only ceiling (structural)

The guard asserts the component and the page issue no mutating request
(`method: "POST"|"PUT"|"PATCH"|"DELETE"` -> none), reference none of the mutating Lab
paths (`/authorize`, `/execute`, `/transition`, `/run-agent`), and that the component
performs no fetch of its own (`apiRequest`/`useHydration` absent) — the page fetches,
the component renders. The distinction the surface preserves
(proposal != approval != execution != evidence != verification != review) is asserted
against the component's own copy.

## 6. Scope / non-goals

* Changed: `EngineeringLabPage.tsx`, one new guard test, this record.
* Not changed: any Lane-1 shared file (registry, router, surfaces, types), any
  backend route or authority surface. `api/main.py` untouched.

## 7. Status

**IMPLEMENTED** — code exists, targeted + contract + architecture proof present,
frontend build green. Production parity **NOT CLAIMED**; a post-merge deployment
would be required for that, and no deployment or acceptance is authorized here.
