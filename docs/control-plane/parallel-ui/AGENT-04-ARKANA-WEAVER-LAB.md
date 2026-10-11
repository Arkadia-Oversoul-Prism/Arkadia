# Agent 04 — Arkana, Weaver & Engineering Lab

**Active branch:** `feat/prism-next2-04-run-evidence-trace`
**Active PR:** [#432](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/432) — draft, implementation in progress.
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Task:** create a read-only trace from run records to work events and evidence using stable, handler-verified references.
**Owns:** Arkana/Oracle, Weaver, Engineering Lab feature-local pages/components/tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Slice status

| Slice | Surface | State |
|---|---|---|
| 02–05 | Lab read model, agent registry, artifact canvas, Arkana thread history | landed on this branch |
| **06** | **run → work-event → evidence trace** | **implemented, tested, evidenced** — `docs/control-plane/evidence/prism-w4-run-evidence-trace-01/EVIDENCE.md` |
| next | automations read surface | **blocked** on Workstream 1's `labAutomations` registry entry |
| next | next verified Arkana/Weaver read surface | not started |

Slice 06 measured: 37 new test nodes; full-suite failing/error node set
`521c63e1…` **identical** to `main` `f390526a` (28 nodes, `diff` empty); architecture
11 passed; `tsc --noEmit` + `vite build` clean. Read-only by construction — the trace
issues no request of its own and joins only handler-recorded reference fields
(`event.run_id`, `evidence.run_ref`, `run.evidence_refs`).

## Start now — no new prompt required

1. Re-fetch `main`; verify exact handler routes, response shapes, identity/owner scope, and stable foreign-key/reference fields. Never join records on guessed identifiers.
2. Build a feature-local run-to-evidence review view connecting the real session/run/work-event/evidence records. Show source references and recorded states; missing links remain unresolved, not inferred.
3. Preserve the state boundaries: a run is not evidence; evidence is not verification; verification is not review; review is not human acceptance. Include a negative control where an evidence record exists but no verification/acceptance exists.
4. Add tests for owner isolation, empty/missing references, duplicate/partial records, and the read-only ceiling. Keep all requests GET-only unless a separately authorized contract explicitly says otherwise.
5. Workstream 1 is adding the verified `labAutomations` registry entry and `labCanvas(id)` builder on its own branch. Do not edit `lib/endpoints.ts`; after that entry lands, add the read-only automations surface using the actual grammar/response contract and preserve `final_transition: HUMAN_GATE`. Do not wire automation mutation routes.
6. Continue with one verified Arkana or Weaver read surface at a time.

## Hard boundaries

- No edits to shared routing/navigation/tokens/tests, NovaNet/Solariun feature files, runtime/authority model, or deployment configuration.
- No fabricated replies/evidence, hidden execution, auth bypass, or treating declared agent capability as granted authority.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue with a safe non-overlapping task where possible.

## Required evidence

Verified route/auth/data contract; source-bound references; owner/read-only/state-boundary tests; negative controls; typecheck/build; exact SHAs; unresolved links and next bounded move.
