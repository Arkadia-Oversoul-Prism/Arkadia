# 01 — Current State
> Updated at the end of every session. Source of truth for what's next.

---

## Mode
BUILD

## Phase
Phase 1 — Runtime Stabilization

## Workstream
K — Knowledge OS Integration (active)

## Checkpoint
**K4 — Response Provenance** (READY TO BEGIN)

> Reconciled 2026-09-30 (Weaver pass `gate-k/k5-status-reconciliation`). K5 was recorded
> here as "READY TO BEGIN" while it had in fact already shipped on `main` across
> `606510f`, `4ca0442`, `0852068`, `31818e3` — implementation, lifespan wiring, and
> tests all present. Record backfilled at `docs/checkpoints/K5_static_ingestion.md`.
> K3 and K4 statuses below were re-derived from live evidence in the same pass.

---

## True Current Position

### Completed
- ✅ B0.5 — Baseline Integrity (fitness tests fixed, debt registered)
- ✅ Workstream B — SQLite durability complete; Gate B CLOSED
- ✅ Workstream C — Started
- ✅ Phase 0 — Endpoint migration complete (arkadia-n26k → arkadia-kw64 across 12 files)
- ✅ Infrastructure: `railway.json`, `docs/deployment/RAILWAY.md`, `DEPLOYMENT_OPTIONS.md`
- ✅ Knowledge Recon: all 21 `docs/recon/` documents + `KNOWLEDGE_OS_EVOLUTION.md`
- ✅ Backend LIVE: https://arkadia-kw64.onrender.com
- ✅ Session infrastructure: `.bootstrap/`, `PARKING_LOT.md`, `REPOSITORY_SNAPSHOT.md`
- ✅ K2 — Oracle Conversation Archival: daemon thread archives every Oracle turn into the Knowledge Layer
- ✅ K1 — Corpus Document Ingestion: all three corpus entry points wired to _ingest_to_knowledge_os()
- ✅ K5 — Static Ingestion: `knowledge/static_ingestion.py` + lifespan wiring (`api/main.py` 206-207)
  + 12 tests; idempotent (run 2 ingests 0). Record: `docs/checkpoints/K5_static_ingestion.md`
- ✅ K3-A/B/C — Canonical Ontology / Operational Graph / Semantic Enrichment: implemented and
  checkpointed; `assemble_context` is consumed by `api/oracle_spine.py` and `api/knowledge_routes.py`
  (K3-C "Context Engine Wiring" is satisfied at the spine)

### Pending (manual — user action)
- 🟡 `web/public_prism/.env.production` — `VITE_API_URL` must be updated to `https://arkadia-kw64.onrender.com` in Vercel dashboard before next frontend deploy

### Next Checkpoint
**K4 — Response Provenance**

Make Oracle responses citable. `knowledge/context_engine.assemble_context()` already
returns note UUIDs alongside text chunks; surface them as a `sources` array on the Oracle
response and render "Based on: ..." in the UI.

Verified absent on `main`: no Oracle response path returns a `sources` array. The spine
(`api/oracle_spine.py`) builds a context block and a diagnostics dict (`notes_retrieved`,
`source`) but does not propagate note identities to the client.

Files touched: `api/main.py` (response shape) · `web/public_prism/src/components/ArkanaCommune.tsx` (render sources)
Exit: Oracle response includes a `sources` list; frontend shows citations
Risk: Low — additive to response shape; frontend renders conditionally

See `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → section "K4" for the full sketch.

## Repository Health
- Architecture fitness tests: **11/11**
- Full suite (`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
  --continue-on-collection-errors`): **20 failed / 1039 passed / 13 skipped / 2 collection
  errors** (22 failing/error nodes). Classified baseline debt — see
  `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`.
  The 49 → 20 failure reduction since `a26af408` is fully explained by the merged SH-02
  stale-assertion repair PRs (#124–#137).
- Baseline fingerprint (derivation published so it is reproducible):
  `sha256("\n".join(sorted(FAILED/ERROR node ids)) + "\n")` =
  `a7687fadaa25ad5f8aa283747bbffa85d304d516ae2b6c53b3849dc54479434c`
  > An earlier revision of this file carried `d7ff35b2…687036` with no documented
  > derivation; that value could not be reproduced from the node list. The node *set* and
  > counts were consistent, so only the hash was unverifiable. Corrected 2026-09-30.
- Registered layer violations: 10 (LAYER_MAP.py — do not touch)
- Registered circular imports: 3 (LAYER_MAP.py — do not touch)
- Workflows (local Replit): failing (pre-existing — missing secrets)
- Production: LIVE at https://arkadia-kw64.onrender.com

## Blocked By
Nothing. (The Vercel env var is cosmetic — does not block K4.)

## Next Checkpoints After K4
- ~~K1 — Corpus Document Ingestion~~ (complete)
- ~~K5 — Static Ingestion~~ (complete)
- ~~K3 — Context Engine Wiring~~ (complete)
- K4 — Response Provenance (next)
