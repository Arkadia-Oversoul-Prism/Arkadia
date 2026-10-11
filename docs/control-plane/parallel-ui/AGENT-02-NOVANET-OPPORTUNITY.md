# Agent 02 — NovaNet & Project Opportunity Radar

**Active branch:** `feat/prism-next2-02-opportunity-entry-flow`
**Active PR:** [#430](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/430) — draft, implementation in progress.
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Task:** create/edit prospect entries on the selected project board using verified routes.
**Owns:** NovaNet feature modules, `src/components/opportunities/**`, scoped buyer-recon board/entry behavior in `solspire/buyer_recon.py` and `solspire/buyer_recon_router.py`, and related tests/evidence. Shared routing, global navigation, endpoint/type registries remain Workstream 1's seam.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Slice 1 status — create/edit entry flow LANDED on this branch

Implemented and tested (evidence: `docs/control-plane/evidence/prism-opportunity-entry-flow-01/EVIDENCE.md`):

- `opportunityRadarContract.ts` now carries the write contract (`createEntryBody`,
  `editEntryBody`, `parseEntryResponse`, `upsertEntry`, board-derived paths).
- `ProspectEntryForm.tsx` (new, feature-local) drives only the two verified
  handlers: `POST .../entries` and `PATCH .../entries/{id}`.
- `ProjectOpportunityRadar.tsx` mounts the controls; its read contract, distinct
  states and pinned copy are unchanged.
- `tests/test_prism_opportunity_entry_flow.py` — 48 tests. The frontend half is
  **executed** through Node 24's native TypeScript support, not string-matched.
- Full-suite failing/error **node set identical** to `main` `f390526a` (28 nodes);
  `+48 passed` is exactly this file. Architecture 11/11. Build passes.

Measured backend facts worth keeping (do not re-derive):

- `require_project_owner` returns **404** for a non-owner *and* for a missing
  project, indistinguishably — the UI must not claim which occurred.
- **The status field is a transaction-outcome surface, not a reconnaissance one.**
  `BuyerReconEntryPatch` validates against the full `STATUSES` tuple, which
  includes `EXECUTED` and `SETTLED`. An earlier revision of this slice offered the
  whole vocabulary in the form's `<select>`, which made the outcome one click away
  while the copy beneath it read "authorizes no … execution" — corrected at
  `fb78c700` via `SETTABLE_STATUSES` (through `READY_TO_EXECUTE`), enforced in the
  body builders and not only in the option list. Do not re-widen it; see
  `EVIDENCE.md` §3a.
- **MEASURED DEFECT 3 in `solspire/buyer_recon.py` (open, not repaired):**
  `BuyerReconManager.update_entry` validates `status.upper()` then persists the
  original value, so `PATCH {"status": "conversation"}` answers `200` and stores a
  status outside the declared vocabulary. `create_entry` normalizes; `update_entry`
  does not. Pinned by `test_update_does_not_normalize_a_lowercase_status`. Repair
  needs its own authorization (`SHARED-CONTRACTS` §1/§7.1).
- A blank `prospect` is refused on **create** (`400 prospect is required`) but
  **accepted on edit** (`200`, and it blanks the stored value). The edit body
  therefore omits `prospect` unless supplied.
- `evidence_status` / `evidence` have **no verified UI write path**. They are never
  sent, so the backend's `NONE` / `[]` stand. Do not add a control without an
  independently verified, owner- and board-scoped handler.
- `python-multipart` is required to import `solspire/console_router.py`; it is
  missing in the sandbox by default and affects `main` identically.

Next bounded task on the successor branch: the `evidence_status` / `evidence`
capture path, only if such a handler is verified; otherwise the next archived
Opportunity Radar / NovaNet capability whose contract measures cleanly.

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
