# Agent 02 — NovaNet & Project Opportunity Radar

**Active branch:** `feat/prism-next2-02-opportunity-entry-flow`
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Task:** create/edit prospect entries on the selected project board using verified routes.
**Owns:** NovaNet feature modules, `src/components/opportunities/**`, scoped buyer-recon board/entry behavior in `solspire/buyer_recon.py` and `solspire/buyer_recon_router.py`, and related tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Start now — no new prompt required

1. Re-fetch `main`; verify actual POST/PATCH methods, auth/owner checks, request/response shapes, and board-scoping behavior from handlers and tests before wiring UI.
2. Add feature-local create/edit controls for a prospect entry on a selected project board. Reuse the verified API client and actual response shape; do not invent a route or duplicate persistence.
3. Add targeted tests for successful create/edit, validation failure, auth denial, wrong-board writes, and honest loading/empty/error states. Assert persisted state in cross-board negative controls, not response status alone.
4. Preserve unverified facts as `UNKNOWN`; do not turn a prospect into a confirmed buyer, and do not invent contacts, pricing, demand, procurement commitments, or transaction outcomes.
5. Keep reconnaissance separate from budget, approval, transaction, spending, and execution authority. No delete/bulk actions unless an actual authorized handler is independently verified.
6. Keep NovaNet legacy subviews visibly blocked/not-wired until their contracts are verified. Continue with one capability at a time.

## Hard boundaries

- No edits to `App.tsx`, router/surface registry, global nav/lenses/tokens, shared shell tests, or shared endpoint/type registries.
- No auth bypass, hidden writes, duplicate persistence, or claims of success before server confirmation.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue elsewhere when safe.

## Required evidence

Verified route contract; owner and board-scope tests; validation/error states; typecheck/build; negative controls; exact SHAs; explicit unknowns and next task.
