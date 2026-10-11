# Agent 02 — NovaNet & Project Opportunity Radar

**Current slice:** PR #426 — buyer-recon schema/ownership repairs and Projects-surface Opportunity Radar mount.
**After merge:** create the next branch from freshly fetched `main`, open a new draft PR, update the active branch map in `SHARED-CONTRACTS.md` through Workstream 1, and begin immediately.
**Owns:** NovaNet feature modules, `src/components/opportunities/**`, scoped buyer-recon board/entry behavior in `solspire/buyer_recon.py` and `solspire/buyer_recon_router.py`, and related tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Immediate continuation task

Build the next bounded Opportunity Radar slice: **create and edit a prospect entry on a selected project board**, using only verified existing POST/PATCH handlers and the canonical project-board scope.

1. Re-fetch `main`; verify actual route methods, auth/owner checks, request/response shapes, and board-scoping behavior from handlers and tests before wiring UI.
2. Add feature-local create/edit controls and targeted tests for success, validation errors, auth denial, wrong-board writes, and honest loading/empty/error states.
3. Preserve unverified fields as `UNKNOWN`; do not turn an unverified prospect into a confirmed buyer, and do not invent contact facts, pricing, demand, or procurement commitments.
4. Keep reconnaissance separate from budget, approval, transaction, spending, and execution authority. No delete/bulk actions unless an actual authorized handler is independently verified.
5. Keep NovaNet legacy subviews visibly blocked/not-wired until their own contracts are verified. Record one capability at a time.

## Hard boundaries

- No edits to `App.tsx`, router/surface registry, global nav/lenses/tokens, shared shell tests, or shared endpoint/type registries.
- No duplicate persistence, invented endpoints, auth bypass, hidden writes, or claims that a UI action succeeded before the server confirms it.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, human authority decision, destructive/data-loss risk, or genuine contract conflict; record exact evidence and continue elsewhere when safe.

## Required PR evidence

Fresh/existing database migration results; owner and board-scope tests; verified endpoint/request/response contract; typecheck/build; negative controls; exact SHAs; explicit unknowns and next task.
