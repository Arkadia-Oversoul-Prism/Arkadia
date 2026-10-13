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

## Lane 2 continuity — evidence coverage (2026-10-13 pulse)

The successor task above (`evidence_status` / `evidence` capture) is **not
actionable**: no verified owner- and board-scoped write handler exists, so adding
a capture control would invent a mutation path. The bounded move taken instead was
**display-only**: render `summarize().withEvidence`, the third radar metric that
was computed but never surfaced (`byStatus` and `offVocabulary` were reconciled by
`prism-opportunity-pipeline-strip-01`). Evidence:
`docs/control-plane/evidence/prism-opportunity-evidence-coverage-01/`.

Next bounded task on this lane: reconcile the next archived Opportunity Radar /
NovaNet capability **whose contract measures cleanly against a verified handler**.
Do not wire `evidence_status` / `evidence` until a real handler is verified.

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

## Lane continuity — 2026-10-13 (fact grid)

`prism-opportunity-fact-grid-01` (same draft PR #492, head `6a94554`): the console
rendered only three of the ~22 declared `BuyerReconEntryInput` facts. The grid is
now **derived** from the contract's own `DESCRIPTIVE_FIELDS` + `COMMERCIAL_FIELDS`
(so it cannot drift), every value through `fact()` (unverified reads `UNKNOWN`,
never a blank). Display-only. Evidence:
`docs/control-plane/evidence/prism-opportunity-fact-grid-01/`.

Next bounded task on this lane: surface `notes` (excluded from the grid, still
unrendered) **only if** it can be tied to a verified read field and needs no new
control; otherwise reconcile the next archived radar capability that measures
cleanly against a verified handler. Do not invent a capture path.

## Lane continuity — 2026-10-13 (operator notes)

`prism-opportunity-notes-render-01` (same draft PR #492, head `6dc3b13c` + this
slice): `notes` was the last declared `BuyerReconEntryInput` read field the console
never rendered. Traced end to end — declared `notes: str = ""`, stored in the
`buyer_recon_entries` table (`DEFAULT ''`), returned by `to_dict()` on **both**
reads, and writable through the same create/edit handlers `ProspectEntryForm`
already drives — so **no new control or mutation path** was added. The surface now
renders the note gated on its presence (`entry.notes &&`), display-only. Evidence:
`docs/control-plane/evidence/prism-opportunity-notes-render-01/`.

Next bounded task on this lane: reconcile the next archived Opportunity Radar /
NovaNet capability **whose contract measures cleanly against a verified handler**.
Do not wire `evidence_status` / `evidence` until a real handler is verified; do not
invent a capture path for a field with no verified write route.

## Lane continuity — 2026-10-13 (author controls)

`prism-novanet-author-controls-01` (same draft PR #492, head `44b854e2` + this
slice): the console public field was read-only while the archived Prism field
offered **author-only Edit / Delete** on a transmission. The backend contract is
verified and served — `PATCH`/`DELETE /api/transmissions/{id}` in
`api/transmissions.py`, owner derived from the verified Firebase uid (401
anonymous / 403 non-owner) — so the capability was reconciled, not invented. New
feature-local `src/components/novaNet/AuthorControls.tsx` renders **nothing** for
a non-owner and composes its path from the one registry
(`endpoints.transmissions` + `encodeURIComponent`); `NovaNetPage.tsx` mounts it
gated on `myUid === t.owner_uid` and reloads the field on success. No shared file
(`endpoints.ts`, `types.ts`, router, surfaces, `App.tsx`) was touched. Evidence:
`docs/control-plane/evidence/prism-novanet-author-controls-01/`.

Next bounded task on this lane: reconcile the next archived NovaNet public-field
capability **whose contract measures cleanly against a verified handler**
(reactions / repost only if a real handler is verified). Do not invent a capture
path for a capability with no verified write route.
