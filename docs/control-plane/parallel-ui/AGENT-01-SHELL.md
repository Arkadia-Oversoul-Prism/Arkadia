# Agent 01 — Shell, Navigation, Design System & Integration

**Active branch:** `feat/prism-l1-legacy-route-coverage-01`
**Active PR:** [#507](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/507) — draft, implementation in progress.
**Base revision:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
**Task:** advance the Lane-1 shared shell/navigation seam; the next bounded task is repairing lane instruction-doc drift against a machine-readable lane-state snapshot (`docs/control-plane/parallel-ui/lane-state.json`), guarded by `tests/test_lane_instruction_doc_currency.py`.

> Superseded pointers (2026-10-15): the earlier `feat/prism-next2-01-shell-contract-map` branch and wave PRs (#423/#425/#426/#427/#429) are **merged and closed** history; the live Lane-1 threads are PR #507 and PR #529. Do not reopen or continue a merged thread.

**Owns:** shared app shell, `App.tsx`, router/surface registry, global navigation/lenses/tokens, shared shell/endpoint contract tests, `lib/endpoints.ts`, `lib/types.ts`, and integration seams.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Start now — no new prompt required

1. Verify current `main` is descended from the stated base, then refresh the four active branch/PR/head entries in `SHARED-CONTRACTS.md` after the four next-wave PRs exist. Keep the merged #425–#428 wave as history, not active work.
2. Re-verify the actual served handler and URL encoding for Workstream 4's recorded requests. Add `labAutomations: "/api/lab/engineering/automations"` to the canonical registry and add a typed, encoded `labCanvas(id)` path builder derived from `endpoints.labArtifacts`. `labSession(id)` already exists; verify it remains correct. Do not add paths that are not served.
3. Add focused positive/negative contract tests for those builders and their served routes. Run endpoint-registry guards, TypeScript/build, and route-table checks.
4. Review the merged Opportunity Radar Projects mount against the actual board handler; make a shared integration change only if evidence proves one is needed. Do not take over the feature-local implementation.
5. Continue with the highest-value remaining shell/navigation gap in the live inventory. Work in bounded commits and keep the PR updated.

## Measured contract facts (do not re-derive from memory)

- **`useRouter` normalises the address bar on load** (`lib/router.ts`, this branch). It resolves the inbound pathname and `replaceState`s the canonical path when they differ, so `/nexus`, a trailing slash, or an unrouted path does not leave the address bar holding a path no surface declares. Reconciled from the archived Prism (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:102 history.replaceState`). `tests/test_console_shell_nav_contract.py` evaluates the real router in Node rather than pinning its text.
- **`PATH_ALIASES` reconciles legacy inbound links to one canonical surface, never a second route.** Currently `/nexus` → `novanet` and `/oracle` + `/commune` → `arkana`. The archived Prism's route table declares `commune: '/oracle'` and accepts both `/oracle` and `/commune`, and its home surface sends the Oracle portal to `commune`; the console names that surface `arkana`. Without the aliases those paths fell through `resolvePath` to `home`, and the address-bar normalisation then wrote `/`, making the loss permanent for a shared link. **Verify a candidate alias against `app.openapi()["paths"]` and `_RESERVED_PREFIXES` before adding it** — a legacy path that collides with a real backend route must not become a UI alias. Not yet reconciled: `/home` (same case as `/`) and `/gate` + `/living-gate` (the archived `gate` view — the console has no such surface, so reconciling it is a product decision, not a routing one).
- The alias-soundness suite (`_path_aliases` / `_alias_defects`) already asserts every alias targets a declared surface and never collides with a canonical path. **Extend it rather than adding a second detector** — a duplicate guard is not a guard, and the first draft of this pass's alias tests failed on helper scope because `strip_types` is nested inside `_js_route_resolver`.
- The canvas route is a **sibling** of artifacts, not a sub-resource. Served: `/api/lab/engineering/artifacts` (GET), `/api/lab/engineering/canvas/{artifact_id}` (GET). **Not** served: `/api/lab/engineering/artifacts/{artifact_id}`, and `/api/lab/engineering/canvas` alone is not a route. This is why `labCanvas` derives its base by substitution and why a `labCanvasRoot` registry entry would fail the served-path guard.
- `/api/commune/resonance` and `/api/knowledge/search` are **POST-only**; a GET probe returning 405/404 is not a defect.
- Workstream 2's merged evidence explicitly requests **no** shared endpoint constant for `/solspire/buyer-recon`; that path is handler-derived in its own contract module. Do not add it to the registry. Its served shapes are `/solspire/buyer-recon/projects/{project_id}` and `/…/entries` (verified against `app.openapi()`), and the Projects mount is `SolSpirePage.tsx:33` → `OpportunityRadarSection` → `ProjectOpportunityRadar` (reviewed this pass; no shared change needed).
- `knowledgeSearch` was already added by `67696372`; do not re-add it.
- **A concurrent commit on this branch may land the same work.** Two landed while this pass's copies were uncommitted or in flight: `9b1b3ef1` ("reconcile shared endpoint contract against merged feature slices") added `labAutomations` + `labCanvas`, and `e8b0b77a` ("widen the one-registry guard to apiRequest literals") took the detector-widening that this pass had recorded as its own next move. `git fetch` + compare against `origin/<branch>` **before** committing and again before pushing; drop a duplicate rather than re-landing it, rebase the non-overlapping work onto the remote head, and keep **both** sides of a documentation conflict rather than picking one.

## Hard boundaries

- Do not implement NovaNet/Opportunity, Knowledge OS, Arkana/Weaver/Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or genuine cross-workstream contract conflict. Record exact evidence in the PR thread and continue with a safe non-overlapping task where possible.

## Required evidence

Exact base/head SHAs; route/OpenAPI verification; ownership/overlap check; targeted tests and negative controls; typecheck/build; baseline failure-node comparison; current branch map; one next bounded task.

## Status — 2026-10-24 (LANE 1, lane-currency truth repair)

**Active branch:** `feat/prism-l1-legacy-lens-route-recovery-01`
**Active PR:** [#562](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/562) — draft, head `0a6d4db698ccc715a5e790b02d240838ea78eeaa`.
**Base:** `68acf89f3045a01b0ba04038fabac4edfb5f937e` (measured live this pulse; every
earlier base recorded above is superseded).

The pointers above are stale and were repaired by *appending* this block, per the
last-wins convention already used by lanes 2–4. Measured live this pulse: **all four**
lane docs named a dead thread — `AGENT-01` named PR #507 (closed without merging),
`AGENT-02` #430 (merged), `AGENT-03` #526 (closed without merging), `AGENT-04` #428
(merged). A successor agent reading any of them would have resumed a closed thread,
which is the continuity failure the lane model exists to prevent.

Two of those four were *hidden by the deferral mechanism*, which is the more important
finding: `AGENT-03`'s `#526` was installed by open PR #548 and `AGENT-04`'s `#536` by
open PR #555, each while its own lane was `deferred`, so the currency guard judged
neither pointer. `scripts/lane_state.py --verify-live` now judges liveness on the
*document*, for every lane, independently of disposition.

Repaired in this pass:

- Freshness no longer compares SHAs. `snapshot.base_main == current main` reddened on
  any unrelated merge (31 commits had landed since the recorded base; two touched a
  guarded path). Staleness is now "a lane doc changed after the snapshot was recorded".
- `--verify-live` adds an authoritative PR-state oracle (GitHub reads API, read-only):
  OPEN / MERGED / CLOSED_UNMERGED / UNKNOWN, with UNKNOWN failing closed.
- The snapshot is now *derived* (`scripts/lane_state_refresh.py --write`) instead of
  hand-transcribed — the transcription step is what let ten closed PRs stay recorded
  as open.

Ownership note: this pass repaired only Lane 1's own instruction doc. `AGENT-03` and
`AGENT-04` are owned by PRs #548 and #555; their dead pointers are recorded here as a
measured handoff, not edited from a lane that does not own them.

Evidence: `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md`.

**Next bounded task:** once #548 and #555 land or are superseded, re-point `AGENT-03`
and `AGENT-04` at their live lane threads, then re-run
`python scripts/lane_state.py --check --verify-live` and expect it to be clean.
