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
    `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f`
  - node set: `sha256("\n".join(sorted("<nodeid>")) + "\n")` =
    `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22`
  > **Correction 2026-10-02** (`gate-hygiene/baseline-fingerprint-reproducibility-01`).
  > `a59453b8…` was published with the derivation `sha256("\n".join(sorted(FAILED/ERROR
  > node ids)) + "\n")`, which reads as the node-set derivation and does **not** reproduce
  > it (that derivation gives `9a35c812…`). The value is `"<OUTCOME> <nodeid>"` lines, and
  > the ids had been taken from `pytest -q` output **including** the assertion reason,
  > which pytest truncates to the terminal width — so the same node set hashed differently
  > at 120 vs 80 columns. `a7687fad…` and `d7ff35b2…687036` were non-reproducible for the
  > same reason. All three are superseded by the two values above.
  > **No regression.** The failing/error node set is byte-identical at `64cbe74`,
  > `481afa1` and `702b63ae` (21 nodes; both fingerprints match at all three revisions),
  > so the `64cbe74` → `702b63ae` movement is a docs/count change only. The passed count
  > moves 1240 → 1242 between two measurements of the *same* tree because
  > `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  > is order-dependent (documented in `AGENTS.md`); it is not a failure-node change.
  > The 1039 → 1240 passed movement versus the earlier `002b189` measurement is explained
  > by the 42 intervening commits (20 new test files, +4049 test lines) and `00271b2`
  > repairing the `test_render_codex` collection error.
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
