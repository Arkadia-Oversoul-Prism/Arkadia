# Agent 02 — NovaNet & Project Opportunity Radar

**Active branch:** `feat/prism-l2-field-completeness-01`
**Active PR:** [#564](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/564) — draft.
**Base revision:** `36f53be22d753ffe269f05cbf3fb39212f744207` (measured live 2026-10-25; every
earlier base recorded below is superseded).
**Task:** NovaNet public-field completeness — disclose the page bound **and** make the
disclosed remainder retrievable against the verified `offset`/`limit` contract.
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

## Lane continuity — 2026-10-13 (engagement readings)

`prism-novanet-engagement-readings-01` (same draft PR #492, head `e5e6871d` +
this slice): the console public field discarded the engagement a reader could
already fetch. `GET /api/transmissions` returns `reactions` (four backend-seeded
keys), `comments` and `reposts` on every post; the archived Prism field card
rendered all of them. New feature-local `src/components/novaNet/EngagementBar.tsx`
renders them **read-only** — no request, no invented count (a missing reaction
reads `?? 0`), the vocabulary is the backend's own four keys in its order.
`NovaNetPage.tsx` mounts it per transmission, above the author controls.

Scope decision: `reactions`/`comments` have live write handlers but were **not**
wired here (a separate bounded slice); `reposts` has **no** handler, so it is a
reading with no control. No shared file was touched. Evidence:
`docs/control-plane/evidence/prism-novanet-engagement-readings-01/`.

Next bounded task on this lane: wire the **reaction write path**
(`POST /api/transmissions/{id}/react`, verified handler) with a negative control
proving the client offers it only where the backend accepts it.

## Lane continuity — 2026-10-14 (echoes completeness composed into #492)

`prism-l2-echoes-completeness-01` was opened as a **sibling** PR (#528,
`feat/prism-l2-echoes-completeness-01`) from `main` `3ca8582a`, editing the same
`web/arkadia_console/src/pages/NovaNetPage.tsx` base blob (`ef3ccf69`) as PR #492
(from `49809f45`). Siblings editing one file from one ancestor conflict on merge,
so the slice was **composed** into the lane branch rather than left to race:
`git cherry-pick -x e162371d` onto `feat/prism-next7-02-pipeline-strip`, commit
`75fcc947`. The #492 hunks (7/17/54/70/87) and #528's (32/97/113) do not overlap;
the cherry-pick auto-merged and **both** slices are present.

The slice repairs a truthfulness defect: the Crystal-Matrix echoes panel rendered a
bare `EchoesFeed.public.slice(0, 8)` with no stated total and no notice — a subset
presented as the whole stream. It now single-sources `ECHO_DISPLAY_LIMIT`, states
the public total in the header, and renders a truncation notice
(`data-testid="novanet-echoes-truncation"`).

The new guard `tests/test_prism_novanet_echoes_completeness.py` (3 nodes, with a
negative control that reconstructs the pre-change silent cap) is **derived** into
the console-contract domain by `scripts/console_contract_domain.py`, so
`.github/workflows/prism-console-contract.yml` executes it with **no workflow
edit** — the drift class PR #435 removed. Evidence:
`docs/control-plane/evidence/prism-l2-echoes-completeness-01/`.

Measured at `75fcc947`: derived domain **473 passed**, new guard **3 passed**,
lane-2 guards **117 passed**, architecture **11/11**, console build clean with the
marker in the bundle. Full-suite node set 9 nodes, sha256 `c280ddc6…` —
byte-identical to the branch baseline at `d4b9c1fe` (zero regression).

**Disposition:** PR #528 is superseded by this composition; close it once #492 is
reviewed (agents do not close PRs). Draft; no merge, deployment, or acceptance.

Next bounded task on this lane: wire the **reaction write path**
(`POST /api/transmissions/{id}/react`, verified handler) with a negative control
proving the client offers it only where the backend accepts it.

## Status — 2026-10-24 (LANE 2, pointer re-point after snapshot refresh)

**Active branch:** `feat/prism-l2-field-completeness-01`
**Active PR:** [#564](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/564) — draft, head `7c7cdd439c1707741ebc3621b0fa81cbbe2ca850`.
**Base:** `68acf89f3045a01b0ba04038fabac4edfb5f937e` (measured live this pulse; every
earlier base recorded above is superseded).

Every `**Active PR:**` pointer above is stale. The header names PR #430, which is
**MERGED** (`merge_commit_sha` `04e1b83b89e51a994af68b529a1076665f9b3ae5`), and the
dated continuity blocks that follow name #492/#528 — both also no longer open
threads. This block is appended rather than rewritten, per the last-wins convention
`scripts/lane_state.py::declared_branch`/`declared_pr` implement: the last
declaration in the document is the authoritative one, so appending is how a lane
updates its pointer without destroying the provenance above it.

Measured, not asserted. `scripts/lane_state_refresh.py` re-derived the lane-state
snapshot from live PR state and moved this lane from `doc_guard: idle` to
`doc_guard: current` (PR #564, opened 2026-10-24T12:55Z, is the first open PR whose
changed paths fall inside lane 2's exclusive ownership —
`web/arkadia_console/src/pages/NovaNetPage.tsx`). `python scripts/lane_state.py
--check --verify-live` then reported:

```
DRIFT lane 2 (AGENT-02-NOVANET-OPPORTUNITY.md): declares PR #430, which is not an
  open lane PR in the snapshot (open: [..., 562, 563, 564])
DRIFT lane 2 (AGENT-02-NOVANET-OPPORTUNITY.md) declares PR #430, which is MERGED
```

The finding was correct: a successor agent reading this document would have resumed
a merged thread. This block is the repair.

Note on the mechanism, recorded rather than silently fixed: the guard's *blocking*
scope is `current_lanes(state)`, which is derived from the snapshot's `doc_guard`
field — a field the refresher writes. A refresh can therefore widen the gate's teeth
onto a lane whose doc it does not repair, which is exactly how this lane became red.
The tension is real and is left for sovereign review rather than resolved here; see
`docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md` §8.

`AGENT-03` and `AGENT-04` are **not** repaired here: they are `deferred` to open PRs
#548 and #555, which install their own pointers. That is the documented measured
handoff, and editing those docs from this workstream would be a scope violation.

**Next bounded task on this lane:** wire the reaction write path
(`POST /api/transmissions/{id}/react`, verified handler) with a negative control
proving the client offers it only where the backend accepts it.

## Lane continuity — 2026-10-25 (field completeness: the remainder becomes retrievable)

`feat/prism-l2-field-completeness-01` (draft PR #564, head `e2c563ef`): the field
panel disclosed its own truncation but offered no way to act on it. The notice
read "Showing 50 of N public transmissions — the remainder is not rendered on
this surface", which is honest and still leaves the reader holding a page
presented as the field.

The remedy was already served: `GET /api/transmissions` takes **`offset` as well
as `limit`** (`api/transmissions.py`), so the remainder is retrievable without
inventing a contract. The render bound became state (`fieldPage`, initialised
from the one declared `FIELD_PAGE_LIMIT`) and the notice gained a bounded
"Show more" control (`data-testid="novanet-transmissions-more"`) that grows it by
one page per request, capped at the handler's own 100 ceiling and retiring on the
last page. No shared file (`endpoints.ts`, `types.ts`, router, surfaces,
`App.tsx`) was touched.

Two guard nodes were added to `tests/test_prism_novanet_field_completeness.py`:
`test_the_disclosed_remainder_is_retrievable` and a negative control that
reconstructs the bare-notice form and asserts the retrievability detector flags
it **while the silent-cap detector still passes it** — proving the two measure
different properties rather than restating one another.

Measured at `e2c563ef`: guard **9 passed**; console-contract derived domain
**815 passed**; wiring **30 passed**; architecture **11/11**; console build clean
with the marker in the bundle and the pre-change control absent. The live negative
control (control removed from the real `NovaNetPage.tsx`) reddened the guard
(`2 failed`), then the file was restored byte-identically.

**Disposition:** draft; no merge, deployment, or acceptance.

**Next bounded task on this lane:** reconcile the next archived NovaNet
public-field capability whose contract measures cleanly against a verified
handler. `GET /api/transmissions` supports `offset`, so a *deep-linkable* page
position (e.g. surfacing `offset` in the path/query rather than only in component
state) is the nearest unclaimed slice; confirm a real handler before wiring any
new write path.

## Lane continuity — 2026-10-26 (the window moves; the clamp bounds one read, not the field)

Same branch and draft PR #564, head `64060506` at the start of this pulse. The
previous slice's remedy carried its own defect one level up, and it was measured,
not inferred.

**The defect.** `feat/prism-l2-field-completeness-01` made the disclosed
remainder retrievable by *growing* `limit`: `Math.min(page + FIELD_PAGE_LIMIT,
TRANSMISSION_PAGE_CEILING)` with the control retired by `fieldPage <
TRANSMISSION_PAGE_CEILING`. That ladder climbs 50 → 100 and stops, because 100 is
the handler's own **per-request** `limit` clamp (`api/transmissions.py`), not a
bound on the field. Executed against the real handler with 150 posts stored:
`GET /api/transmissions?limit=100` returns 100 posts and `total: 150`. The panel
therefore rendered 100 of 150, printed "the remainder is not rendered on this
surface", and had **already removed the control** — the reader was told 50 posts
existed and given no way to reach them. That is the exact defect class this
slice's own evidence names ("a disclosure with no way to retrieve what it
discloses"), reintroduced by conflating a per-request clamp with a field bound.

**The repair.** The handler serves `offset` beside `limit` (verified:
`?limit=100&offset=100` → 50 returned), so the window *moves* rather than widens.
`fieldOffset` replaces `fieldPage`; the request carries `?limit=${FIELD_PAGE_LIMIT}
&offset=${fieldOffset}`; the notice states the window position ("Showing 1–50 of
150 … this is a window over the field, not the whole of it"); "Show more" advances
one page and "Newer" returns, both guarded on the field's own end
(`fieldOffset + field.data.transmissions.length < field.data.total`), so the
older-page control retires exactly when the last page is rendered and the whole
field is reachable from any position. `TRANSMISSION_PAGE_CEILING` was deleted:
its premise was the defect, and a constant that encodes a wrong invariant is
worse than no constant.

**The guard was corrected, not merely updated.** `find_unretrievable_disclosure`
had *required* `TRANSMISSION_PAGE_CEILING` to be present — it encoded the wrong
invariant and would have passed a field that retires its control with a remainder
still named. It now measures the real property: the window position is state, the
request carries an offset, and the control retires on the field's end. A new
negative control (`test_negative_control_detector_flags_a_window_that_retires_early`)
feeds it the **shipped** form reconstructed verbatim and asserts it is flagged
*while `find_silent_cap` still passes it* — the two detectors measure different
properties rather than restating one another.

Measured at this head: guard **10 passed** (was 9); console-contract derived domain
**816 passed** (52 guard files, was 815); wiring **30 passed**; architecture
**11/11**; console build clean. Bundle markers: `novanet-transmissions-newer` and
`novanet-transmissions-more` present, the slice-specific pre-change notice
("public transmissions — the remainder is not rendered") **absent**. Live negative
control: the real `NovaNetPage.tsx` mutated to the shipped ladder reddened the
guard (`3 failed, 7 passed`), then was restored byte-identically (`10 passed`).

**Bundle-control correction (recorded, not hidden).** The first control chosen for
the bundle check — the bare phrase "not rendered on this surface" — is **shared
prose**, emitted by two *other* panels (`SpiralCodexPanel.tsx` and the public-echoes
panel), so it read 1 and looked like a divergence. It is not one: the control was
wrong, and it was replaced with a slice-specific string. Do not reuse that phrase as
a control.

**Disposition:** draft; no merge, deployment, or acceptance.

**Next bounded task on this lane:** the sibling disclosure measured while fixing
this one — the public-echoes panel renders "Showing N of M public echoes — the
remainder is not rendered on this surface" and `GET /api/echoes`
(`api/main.py::echoes_feed`) **takes no `limit` or `offset` at all**, so that
remainder is genuinely unreachable and cannot be repaired by the client. Confirm
the handler signature before proposing any change; if it is confirmed, the correct
disposition is a backend contract proposal, not a UI slice — a UI control cannot
reach a remainder the endpoint never serves.
