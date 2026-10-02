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
**Workstream K — COMPLETE.** No K6 exists in the design doc.

> Reconciled 2026-10-02 (Weaver pass `gate-k/k4-status-reconciliation`). K4 was recorded
> here as "READY TO BEGIN" while it had in fact already shipped on `main` via PR #153
> (`4a9281b`) — implementation, spine seam, frontend render, and 6 passing tests all
> present. Record backfilled at `docs/checkpoints/K4_response_provenance.md`. This is the
> same staleness class K5 carried; both are now closed, and every K checkpoint has a record.

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
- ✅ K4 — Response Provenance: `build_sources()` in `api/oracle_spine.py`, `sources` on the
  Oracle response, `SourceRef[]` render in `ArkanaCommune.tsx`; 6 tests. Record:
  `docs/checkpoints/K4_response_provenance.md`
- ✅ K3-A/B/C — Canonical Ontology / Operational Graph / Semantic Enrichment: implemented and
  checkpointed; `assemble_context` is consumed by `api/oracle_spine.py` and `api/knowledge_routes.py`
  (K3-C "Context Engine Wiring" is satisfied at the spine)

### Pending (manual — user action)
- 🟡 `web/public_prism/.env.production` — `VITE_API_URL` must be updated to `https://arkadia-kw64.onrender.com` in Vercel dashboard before next frontend deploy

### Next Checkpoint
**None — Workstream K is COMPLETE.** K1, K2, K3, K4 and K5 are all shipped and all now
carry a checkpoint record (`docs/checkpoints/`). The design doc
`docs/recon/KNOWLEDGE_OS_EVOLUTION.md` names no K6.

### Recommended next bounded task (NOT started)
**CS2 — Reusable conversational UI.** Extract the proven Oracle Chat capabilities into a
reusable conversational component boundary so every surface inherits one canonical chat
shell over the shared spine. Deferred (not discarded) in `NEXT_AGENT.md`.

This is a **product scope expansion** relative to Workstream K. Naming it here is a
recommendation, not an authorization; beginning it requires a sovereign decision.

Standing non-K candidates awaiting a sovereign ruling or a separate bounded workstream
(see `PARKING_LOT.md`): `weaver.autonomy` module/package shadowing (authority model);
Spiral Grove registry declaration-order vs topological-order contract; baseline test debt.

## Repository Health
- Architecture fitness tests: **11/11**
- Full suite (`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
  --continue-on-collection-errors`): **20 failed / 1242 passed / 17 skipped / 1 error**
  (21 failing/error nodes) — re-measured 2026-10-02 on `main` @ `702b63ae`.
  Classified baseline debt — see
  `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`.
  The 49 → 20 failure reduction since `a26af408` is fully explained by the merged SH-02
  stale-assertion repair PRs (#124–#137).
- Baseline fingerprint — derivation is **executable and pinned**, not prose:
  `python scripts/baseline_fingerprint.py <pytest log>` prints both values below and is
  covered by `tests/test_baseline_fingerprint.py`.
  - outcomes (canonical): `sha256("\n".join(sorted("FAILED|ERROR <nodeid>")) + "\n")` =
    `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7`
  - node set: `sha256("\n".join(sorted("<nodeid>")) + "\n")` =
    `da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71`
  - The recorded node set is `tests/fixtures/baseline_node_set.txt` (21 nodes); the two
    values above are what the script prints for it.
  > **Correction 2026-10-02** (`gate-hygiene/baseline-fingerprint-reconciliation-01`).
  > `gate-hygiene/baseline-fingerprint-reproducibility-01` (PR #203) set out to make the
  > fingerprint reproducible and merged `scripts/baseline_fingerprint.py`, but the pair it
  > published (`a59453b8…` / `9a35c812…`) is **not reproducible by that script or by any
  > other derivation** — running the merged script on the same 21 nodes at the same
  > revision prints `4d84e7eb…` / `da2ec262…`. The two values above are the reproducible
  > pair; `a59453b8…` and `9a35c812…` are superseded and must not be republished.
  > `tests/test_baseline_fingerprint.py` now runs the recorded node set through the
  > extractor and requires every document that publishes a fingerprint to carry the
  > canonical value, with a negative control proving the superseded values do not
  > reproduce. Evidence:
  > `docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/`.
  > **No regression.** The failing/error node set is byte-identical at `702b63ae` and
  > `2b167e4` (21 nodes; both fingerprints match), so the intervening commits changed no
  > failure node. The passed count moves between runs of the *same* tree because
  > `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  > is order-dependent (documented in `AGENTS.md`); it is not a failure-node change.
- Registered layer violations: 10 (LAYER_MAP.py — do not touch)
- Registered circular imports: 3 (LAYER_MAP.py — do not touch)
- Workflows (local Replit): failing (pre-existing — missing secrets)
- Production: LIVE at https://arkadia-kw64.onrender.com

## Blocked By
Nothing blocking repository work. (The Vercel env var is cosmetic.)

Gate-2 production parity remains **BLOCKED on provider auth** — the deployment-specific URL
is behind Vercel Deployment Protection. That is an external boundary, not a repository task;
see `docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/`.

## Workstream K Final State
- ~~K1 — Corpus Document Ingestion~~ (complete)
- ~~K2 — Oracle Conversation Archival~~ (complete)
- ~~K3 — Canonical Ontology / Operational Graph / Semantic Enrichment~~ (complete)
- ~~K4 — Response Provenance~~ (complete — record backfilled 2026-10-02)
- ~~K5 — Static Ingestion~~ (complete)
