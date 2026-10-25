# Agent 04 — Arkana, Weaver & Engineering Lab

**Current slice:** PR #428 — read-only Arkana thread history and verified Lab session/run/event/evidence/artifact/agent views.
**After merge:** create the next branch from freshly fetched `main`, open a new draft PR, update the active branch map through Workstream 1, and begin immediately.
**Owns:** Arkana/Oracle, Weaver, Engineering Lab feature-local pages/components/tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Immediate continuation task

Build the next bounded read-only slice: **a traceable run-to-evidence review view** that connects the real session/run/work-event/evidence records already returned by the Engineering Lab handlers.

1. Re-fetch `main`; verify exact handler routes, response shapes, identity/owner scope, and any stable foreign-key/reference fields. Do not join records on guessed identifiers.
2. Show source references and current recorded states; distinguish run completion from evidence existence, verification from review, and review from human acceptance. Missing links must remain visibly unresolved, not inferred.
3. Add tests for owner isolation, empty/missing references, duplicate/partial records, and the negative control where an evidence record exists but no verification/acceptance exists.
4. Keep the interface read-only. No authorize, execute, transition, run-agent, provider, repository-write, merge, or deployment controls.
5. Once this trace is proven, continue with one verified Arkana history improvement or Weaver read surface at a time.

## Hard boundaries

- No edits to shared routing/navigation/tokens/tests, NovaNet/Solariun feature files, runtime/authority model, or deployment configuration.
- No fabricated replies/evidence, hidden execution, auth bypass, or treating a declared agent capability as granted authority.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue with a safe non-overlapping task where possible.

## Required PR evidence

Verified route/auth/data contract; source-bound references; owner/read-only/state-boundary tests; negative controls; typecheck/build; exact SHAs; unresolved links and next bounded move.

## Status — 2026-10-25 (lane reference re-measurement, lane 4)

**Active branch:** `integration/eaa-dispatch-readonly-evidence-current-main`
**Active PR:** [#553](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/553) — draft, the live lane 4 thread.

Supersedes the `#428` pointer at the top of this document, which **merged on 2026-10-11**
at `71190dd3`, and `#536`, which is closed without merging. Neither is a live thread.

This block also supplies the `**Active branch:**` pointer this document previously
lacked, which the guard requires. It exists because the lane guard's enforced set is no
longer derived from `doc_guard`: lane 4 is judged on every run, so a stale pointer here
blocks the gate instead of being hidden by a deferral. The lane docs are lane-owned; this
edit is a reference correction only — it changes no task, no ownership, and no scope.
