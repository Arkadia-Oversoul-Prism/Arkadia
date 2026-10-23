# Recon: Prism reconciliation, slice 2 — NovaNet ownership + the next gap

Bound to base `main` `68403b9ea8e2ba16ade0d1b08418453a79b9dcb7`, branch head `0b0e0cd3`
(PR #559). Read-only recon; no source changed by this document.

## 1. Ownership recon — the finding that redirects the next slice

The mandate named NovaNet as the next slice. **That premise is stale.** Measured live:

- **PR #492 is merged, not open.** `pulls/492` → `state: closed, merged: true`, merge
  commit `7030ccb2` ("LANE2: Opportunity Radar pipeline and evidence coverage").
- The console already has a working NovaNet surface: `pages/NovaNetPage.tsx` (field +
  echoes lenses) with `components/novaNet/{TransmissionComposer,EngagementBar,AuthorControls}.tsx`,
  all reading the live contract (`/api/transmissions`, `/api/echoes`) through the registry.
- **No open PR touches NovaNet.** `grep -iE 'novanet|transmission|social'` over all 19 open
  PRs' file lists → 0 matches.

So NovaNet is **CONNECTED**, not a gap. Proceeding on the mandate's wording would have
produced a competing surface over an existing one — exactly the hazard the ownership rule
forbids. Re-derived rather than trusted.

### Open-PR file contention (19 open PRs, 195 path entries)

Files touched by more than one open PR — do not edit from a third branch:

| File | Owners |
|---|---|
| `docs/control-plane/parallel-ui/lane-state.json` | #553, #555 (+ #539) |
| `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` | #539, #546, #553 |
| `web/arkadia_console/src/lib/endpoints.ts` | #556, **#559 (prior slice)**, **this slice** |
| `web/arkadia_console/src/pages/ArkanaPage.tsx` | #550, **#559 (prior slice)** |
| `weaver/engineering_acceptance.py`, `weaver/openhands_dispatch.py`, … | #500, #502, #508, #553 |

`lib/endpoints.ts` therefore has **three** open branches touching it. Measured composition
with #556 is recorded in `EVIDENCE.md` §4.2 — the composed tree (with `main` merged in, since
#556's head is behind) runs **89 passed** and builds clean.

Unowned and therefore available: `pages/NovaNetPage.tsx`, `pages/SolariunPage.tsx`,
`lib/surfaces.ts`, `lib/router.ts`. `pages/KnowledgePage.tsx` is owned by #554.

**Superseded:** an earlier revision of this table named only #556 and #559 for
`endpoints.ts`. That was measured before this slice existed; the third owner is this branch.
Re-measured at `68403b9e` against 19 open PRs.

## 2. A stale-contract defect in the console's own copy (owned elsewhere)

`pages/SolSpirePage.tsx:43-46` declares four `NotYetWired` contracts:

| Declared | Served? | Real path | Live production |
|---|---|---|---|
| `/api/solspire/workloads` | **ABSENT** | `/solspire/workloads` | not probed (timeout) |
| `/api/solspire/proposals` | **ABSENT** | `/solspire/proposals` | **401 Authentication required** |
| `/api/solspire/pulses` | **ABSENT** | `/solspire/pulses` | **401 Authentication required** |
| `/api/solspire/voice` | **ABSENT** | (none) | 404 |

Three of the four name an `/api/solspire/*` prefix that does not exist, while the real
`/solspire/{workloads,proposals,pulses}` are served and auth-gated. **Not repaired here**:
PR #556 already owns this file and its diff replaces exactly those four lines with the
correct `/solspire/*` paths. Repairing it from this branch would conflict with reviewed work.

## 3. The next gap — the Spiral Codex / Encyclopedia Galactica corpus

### The defect, measured

`GET /api/codex` on production: **200**, an open read, no identity required, serving
**661 documents / 4,413,059 characters** (5,128,422 bytes on the wire). Per document:
`id, source, category, priority, label, description, chars, preview, content, fetched_at,
error, github_url`.

The archive built two whole routes on it — `/encyclopedia` (`NexusSpiralCodex`,
`initialMode="scrolls"`) and `/spiral-codex` (`SpiralCodexFeed`), plus `SpiralVault`,
`ShereSanctuary`, `PersonalCodex`, and `dashboardApi.codex()`. `SpiralCodexFeed` carries a
full IA: category chips with counts, a search across label/description/preview, an expandable
document body, and an upload flow.

The console references it **zero** times. The registry's `codex` entry is `/api/me/codex` —
the **personal** corpus, a different contract. The public corpus has no registry entry at all.

### Why this is the right next slice

1. **Backend capability exists and is verified** (§3), so it is UNSURFACED, not ABSENT.
2. **Three of the 71 mission-relevant gap paths in one coherent surface**: `/api/codex`,
   `/api/codex/upload`, `/api/scrolls`.
3. **It is unowned.** No open PR touches codex/scrolls/encyclopedia (0 matches).
4. **The console's own UI currently mis-states it.** `NovaNetPage.tsx:200-203` tells the
   reader the hub sub-views' contracts are "either unverified or sovereign-key gated, which
   the authenticated client cannot satisfy". That is true of `/api/ims/inquiries` (403
   "Sovereign key required") and false of `/api/codex`, which is an unauthenticated 200. The
   surface states a false reason for an absent capability.
5. **It unlocks further surfaces**: the same corpus feeds `/api/scrolls` and the Knowledge OS.

### The archive port is not a copy — a live 404 proves it

`SpiralCodexFeed.tsx:90-91` fetches `/api/codex/categories` in parallel with `/api/codex`.
Measured: **`/api/codex/categories` is ABSENT from the route table and returns 404 on
production** (`{"detail":"Route not found"}`). A naive port would fire a request that always
fails. Categories must be derived client-side from the documents' own `category` field,
which the payload already carries.

## 4. Capability-to-surface graph (this slice)

| Field | Value |
|---|---|
| Capability ID | `SPIRAL-CODEX-CORPUS` |
| Purpose | Read the shared public document corpus — the Encyclopedia Galactica |
| Legacy routes | `/encyclopedia`, `/spiral-codex` (`App.tsx:134-135`) |
| Legacy components | `NexusSpiralCodex.tsx`, `SpiralCodexFeed.tsx`, `SpiralVault.tsx` |
| Current canonical surface | `novanet`, section `codex` (the hub's own namespace) |
| Contract | `GET /api/codex` — public read, verified 200 on production |
| Identity / authority | **None required.** Read-only; no mutation wired |
| Service | `api/main.py::get_codex` → `_get_scrolls()` |
| State change | None (read) |
| Classification | **UNSURFACED** |
| Confidence | High — route table, live production probe, payload shape all measured |

### Envelope

- **User-visible outcome:** a reader opens NovaNet → Codex and sees the corpus — total
  documents, total characters, category facets with counts, a bounded document list, and
  per-document expand showing the real `content`.
- **Allowed changes:** `lib/endpoints.ts` (append one entry), `lib/types.ts` (append
  interfaces), a new `components/novaNet/spiralCodexContract.ts`, a new
  `components/novaNet/SpiralCodexPanel.tsx`, `pages/NovaNetPage.tsx` (add the lens, correct
  the hub note), a new contract test, an evidence doc.
- **Exclusions:** no upload (a write; separate slice), no `/api/scrolls`, no Knowledge OS
  coupling, no backend change, no new router or API client.
- **Acceptance:** the panel renders real counts from the live contract; loading/empty/error
  states are honest; the 661-document corpus is not fully rendered (bounded, with the
  truncation stated); categories derive from documents because the route is 404; the false
  hub note is corrected; contract tests pass with negative controls.
- **Rollback:** revert the branch; additive only.

## 5. Unknowns (recorded, not resolved)

- The `/api/ims/*` and `/api/distribution/*` clusters were **not** fully classified — only
  `/api/ims/inquiries` (403 sovereign) was probed. Their disposition is UNKNOWN here.
- Whether `/api/codex` should be its own top-level surface rather than a NovaNet lens is a
  product decision; this slice uses the existing `novanet` namespace because `surfaces.ts`
  is a shared seam and adding a surface is a larger change than the slice needs.
- The archive's `/api/codex/categories` may have existed historically; only its present
  absence is measured.
