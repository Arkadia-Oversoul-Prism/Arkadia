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
  --continue-on-collection-errors`): **18 failed / 1304 passed / 18 skipped / 1 error** —
  re-measured 2026-10-03 on `gate-hygiene/stale-gate-fixture-retirement-01` (main
  `162f574`), after retiring the two archived-surface gate nodes. A plain CI checkout
  reports **19 failing/error nodes**: the recorded 18-node set plus the
  clone-depth-dependent sibling
  `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`, which errors when the
  PR-head revision `7d79f38…` is absent.
  Classified baseline debt — see
  `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`.
  The 49 → 20 failure reduction since `a26af408` is fully explained by the merged SH-02
  stale-assertion repair PRs (#124–#137).
- Baseline fingerprint — derivation is **executable and pinned**, not prose:
  `python scripts/baseline_fingerprint.py <pytest log>` prints both values below and is
  covered by `tests/test_baseline_fingerprint.py`.
  - outcomes (canonical): `sha256("\n".join(sorted("FAILED|ERROR <nodeid>")) + "\n")` =
    `6c7bf8218fd1e0ae9bc970653e98c18b3a78b69a5c4920dac9f4747c033e4648`
  - node set: `sha256("\n".join(sorted("<nodeid>")) + "\n")` =
    `2bc35996b21de6529ffffab63446c8bd7295c388e841a2807101d189eaf7da01`
  - The recorded node set is `tests/fixtures/baseline_node_set.txt` (18 nodes); the two
    values above are what the script prints for it.
  > **Correction 2026-10-02** (`gate-hygiene/baseline-fingerprint-reconciliation-01`).
  > `gate-hygiene/baseline-fingerprint-reproducibility-01` (PR #203) set out to make the
  > fingerprint reproducible and merged `scripts/baseline_fingerprint.py`, but the pair it
  > published (`a59453b8…` / `9a35c812…`) is **not reproducible by that script or by any
  > other derivation**. The first reconciliation pass then published `4d84e7eb…` /
  > `da2ec262…`, which *was* reproducible — but only in a clone that contained the PR-head
  > revision `7d79f38…`, because the recorded set held a node that skips when that revision
  > is absent (`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`). The
  > value therefore encoded **clone depth**, not the repository's debt, and a CI checkout —
  > which does not fetch PR-head revisions — derived the older, differently-shaped set.
  > The recorded set now excludes that node (18 nodes) and the values above are stable
  > across clone depths. All three earlier pairs (`a59453b8…`, `9a35c812…`, `4d84e7eb…`,
  > `da2ec262…`) are superseded and must not be republished.
  > **Correction 2026-10-02** (`gate-hygiene/superseded-fingerprint-origin-01`). The claim
  > above that `a59453b8…` / `9a35c812…` are "not reproducible by any convention" is
  > **wrong**. They reproduce exactly as the recorded 20-node set **plus** the
  > depth-dependent *sibling* node
  > `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` — i.e. a bare CI clone's
  > live run. Both values remain **superseded** (the sibling's outcome depends on whether the
  > clone carries `7d79f38…`, so the pair is clone-depth dependent and must not be
  > republished), but their origin is now **explained**, not UNKNOWN. Measured on
  > `162f574b05`: a bare clone's live 21-node run hashes to `a59453b8…` / `9a35c812…`, and the
  > recorded set plus the sibling reproduces both byte-exactly.
  > `tests/test_baseline_fingerprint.py` now proves this
  > (`test_superseded_values_are_the_recorded_set_plus_its_sibling`), so the explanation cannot
  > silently regress. Evidence:
  > `docs/control-plane/evidence/gate-hygiene-superseded-fingerprint-origin-01/`.
  > `tests/test_baseline_fingerprint.py` now runs the recorded node set through the
  > extractor and requires every document that publishes a fingerprint to carry the
  > canonical value, with a negative control proving the superseded values do not
  > reproduce, and a guard that the clone-depth-dependent node never re-enters the set.
  > **Superseded 2026-10-03** (`gate-hygiene/stale-gate-fixture-retirement-01`): the two
  > nodes asserting the root `gate/` + `index.html` surface (archived by `f6718b9`) were
  > retired, so the recorded set is 18 nodes and the canonical pair is
  > `6c7bf821…` / `2bc35996…`.
  > Evidence:
  > `docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/`.
  > **No regression.** The clone-depth-stable failing/error node set is unchanged at
  > `2b167e4` — 18 nodes, `17 failed / 1 error` — with the pinned PR-head revision present
  > and absent alike; the one node that moved between the two clones is the depth-dependent
  > node now excluded from the recorded set. The passed count moves between runs of the
  > *same* tree because
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
