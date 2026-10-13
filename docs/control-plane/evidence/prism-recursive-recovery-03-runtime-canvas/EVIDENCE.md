# EVIDENCE — PRR-03 · Solariun project runtime-context canvas

**Work item:** PRR-03 (prism-recursive-recovery-01 ledger)
**Target behavior:** The Solariun `projects` lens offers a real per-project
control that opens a read-only canvas over the served, owner-scoped projection
`GET /solspire/projects/{project_id}/runtime-context`, rendering its actual
binding states (UNKNOWN stays UNKNOWN), repeating the endpoint's epistemic
boundary, and stating the deliberate 404 ambiguity instead of guessing.
**Base (dependency):** this branch stacks on draft PR #510
(`feat/prism-rec-01-solariun-routed-lenses` @ `31fd1d5`), which owns
`SolariunPage.tsx`; its own base is `main` @ `dfbd230`.
**Implementation commit:** `931c3f0c544c74cfb1be04ad7f48101f0d084107`
(candidate head when every verification below was executed; base SHA + PR head
identify the exact candidate).
**Branch:** `feat/prism-rec-03-runtime-canvas`

## 1. Problem (measured)

At base, `SolariunPage` rendered `NotYetWired` with
`contract="/api/solspire/projects/{id}/runtime-context"` — while the canonical
backend **serves** the contract (handler
`solspire/console_router.py::project_runtime_context`, mounted under the
`/solspire` router with `require_auth` + `require_project_owner`), and the
advertised string carried a wrong `/api` prefix (it is recorded in
`RECORDED_ADVERTISED_DRIFT` by the endpoint-registry guard). A verified
read-only contract with no UI is exactly a "missing user-visible capability
with an existing backend contract".

The archived Prism's Solariun presented a "cognitive canvas" per project; this
is the smallest recovery of that experience against the current contract — not
a second memory/task/event system (the handler is a projection over
`project_store`, Daily Pulse, Workload, and WorkEvents spines).

## 2. Changed paths (stacked on #510)

- `web/arkadia_console/src/lib/endpoints.ts` — `solspireProjectRuntime(id)`,
  a registry-derived, percent-encoded path builder (precedent:
  `labSession`/`labCanvas`; no new registry constant — it derives from the
  existing `solspireProjects` entry). Verified: no open PR touches this file.
- `web/arkadia_console/src/components/solariun/ProjectRuntimeCanvas.tsx`
  (new) — the read-only canvas with loading / ready / auth-required /
  unavailable / failed / ambiguous-404 states; `UNKNOWN` bindings rendered as
  dashed chips distinct from bound ones; `epistemic_boundary` and
  `retrieved_at` shown verbatim; store records shown as bounded counts only.
- `web/arkadia_console/src/pages/SolariunPage.tsx` — per-project "Runtime"
  toggle (`aria-pressed`, per-id testid) and canvas mount; the obsolete
  not-yet-wired placeholder removed.
- `tests/test_prism_solariun_runtime_context_ui.py` (new, 11 tests).

No backend file changed. No write control exists anywhere in the slice.

## 3. Verification (exact commands and results)

| Command | Baseline | After candidate |
|---|---|---|
| `cd web/arkadia_console && pnpm run build` (`tsc --noEmit && vite build`) | PASS | **PASS** (exit 0, `dist/assets/index-DsY7VLP-.js` family, rebuilt after final edits) |
| `python3 -m pytest tests/test_prism_solariun_runtime_context_ui.py -q` | n/a (new) | **PASS — 11 passed** |
| Full relevant set (new suite + solariun-lens, canonical routing, rebuild-01, aeas05 acceptance, endpoint registry, authority chain, shell nav, pass-C ownership, solariun consolidation/knowledge/x01-x12, CP10 gate integrity, `tests/architecture`) | **211 passed** (measured in a detached worktree at #510 head `31fd1d5`, same command minus the new file) | **222 passed** |

Backend half is **executed** against the real `console_router` with isolated
SQLite paths: owner 200 with the documented shape and `UNKNOWN` bindings;
unauthenticated 401; missing-id and foreign-project 404 bodies byte-identical
(existence never leaked); two consecutive reads produce identical state
(the projection mutates nothing). Frontend half: the path builder is executed
in Node (plain and hostile `a/b?c#d` ids — percent-encoded, can't address a
different route), plus source contracts with negative controls (unwired
projects lens flagged; inline `/solspire/...` composition flagged, comments
exempt).

Guards that caught candidate defects (fixed in the candidate, tests untouched):
`test_every_page_read_uses_the_registry_not_an_inline_path` (an
imported-from-a-feature-module builder is not registry-derived at the call
site — resolved by the `lib/endpoints.ts` builder, the sanctioned seam).

## 4. Review findings

- Scope: 2 edited source files, 1 new component, 1 new test (+evidence).
  Diff at this branch head: `endpoints.ts +14`, `SolariunPage.tsx +27/−7`.
- Every control real and permission-aware: the toggle reads state; the canvas
  is read-only; ownership is enforced server-side (404) and the UI never
  claims which refusal occurred.
- Honest states: UNKNOWN bindings never upgraded; `UNAVAILABLE` knowledge
  graph shown with its detail; no store record contents invented (counts only,
  server-bounded).
- No second source of truth: one registry entry, one builder, one handler.

## 5. Limitations / risks (explicitly not claimed)

- **NOT TESTED (browser):** no browser harness in this sandbox; rendering is
  covered by build + contracts, not an observed session.
- **NOT TESTED:** the `UNAVAILABLE` knowledge-graph branch and the
  `SUBJECT_WORKSPACE_BOUND` paths are exercised only through handler
  inspection, not a seeded workspace fixture (workspace-free fixtures cover
  UNKNOWN).
- Backend execution used dependency overrides for `require_auth` (the
  repository's established test convention); the real Firebase token path is
  covered by `require_auth`'s own tests, not this file.
- Dependency: merges only after PR #510 (stacked branch; base set to the
  #510 branch).

## 6. Next dependency / recommended action

Draft PR with base = `feat/prism-rec-01-solariun-routed-lenses`. After #510
merges, GitHub retargets the base to `main`.
