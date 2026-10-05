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

### Active bounded PR (Phase 1 — Runtime Stabilization)
> **Reconciled 2026-10-05** (Weaver pass `gate-hygiene/ci-gate-trigger-coverage-01`, main
> `4550531`). The PR recorded below was **merged 2026-10-03T17:45:33Z**, at head
> `981870e256` — not the `3a28b79` recorded here. The "READY FOR SOVEREIGN MERGE" status was
> stale. The section is retained as the record of that workstream. The current active bounded
> PR is `gate-hygiene/ci-gate-trigger-coverage-01` (CI gate trigger coverage boundary), which
> adds no new workstream: it repairs the trigger filter of an existing gate.

**PR #240** — `gate10/cp10-allowlist-arkadia-console-android` → `main`. **MERGED 2026-10-03.**
Head `981870e` (the `3a28b79` recorded below was superseded before the merge).

- **Defect (real, repository-owned):** the CP10 mutation boundary (`SG-02-FE.2-V`) rejected
  **18 of 1726** tracked paths at `d798811`, all under the single top-level prefix
  `arkadia-console-android/`. That reddened three `test_m02a_ci_gate_integrity.py` nodes on
  `main`. This is the recurring allowlist-omission class `AGENTS.md` records: a plainly
  legitimate tracked surface means the allowlist is wrong, not the commit.
- **Fix:** one `LEGIT` alternation admitting `arkadia-console-android/`. Denylist and
  unknown-root rejection untouched — the gate is not weakened.
- **Evidence:** `docs/control-plane/evidence/gate10-cp10-allowlist-arkadia-console-android/EVIDENCE.md`
  and `docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`.
- **Measured:** `tests/test_m02a_ci_gate_integrity.py` 55 passed; `tests/architecture`
  11 passed; CP10 workflow `success` at both branch heads; node set 31 → 28 (exactly the
  three gate-integrity nodes, zero new failing nodes). `py_compile api/main.py` OK (2582).
- **Provider note:** `Vercel – console` / `Vercel – arkadia-prism` are failing on **every**
  open PR (#237/#238/#239/#240) with "Deployment rate limited — retry in 24 hours". That is
  a provider-side build rate limit, not a code regression.

### Phase 1 baseline classification (recorded 2026-10-03)
All **28** failing/erroring nodes at `3a28b79` are classified in
`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`:
3 repaired by PR #240, 10 test-side literal/regex defects, 3 `AGENTS.md`
encoding-adjudication nodes, 12 recorded pre-existing debt, 3 stale fixture entries now
passing. **Attribute deltas by node set, never by counts** — the passed count is
order-dependent via `test_agent_loop_does_not_mutate_repository`.

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

**Proposed bounded work recorded 2026-10-05** (discovered, not authorized, not started):
1. *Reconcile `tests/fixtures/baseline_node_set.txt`* — 10 recorded nodes vs 20 live, a strict
   subset. Needs the same measurement-backed retirement the 18→10 pass used, so a future pass
   does not read unrecorded debt as a regression.
2. *Widen `provider-routing.yml` to `api/**`* — the architecture suite asserts the
   `api/main.py` line budget, so `api/**` belongs in the filter of any workflow that runs it.
   Held back deliberately: that workflow also runs the full suite, which carries baseline debt,
   so widening the trigger first would turn every API pull request red with debt it did not
   introduce. Prerequisite: the baseline is not red.
3. *Resolve PR #294's review-record boundary regression* — independently reproduced this pass
   at head `2b8d4f51` (`tests/test_verification_review_boundary.py`: 4 failed / 6 passed;
   `main` passes 10/10). Must be reconciled before #294 merges.

## Repository Health
> **Reconciled 2026-10-05** (Weaver pass `gate-hygiene/ci-gate-trigger-coverage-01`, main
> `4550531`). Measured live this pass, with the full suite run under `-rEf` (errors visible):
> `python -m pytest tests/ -q -rEf --continue-on-collection-errors` →
> **19 failed / 1444 passed / 22 skipped / 1 error**, i.e. **20 failing/error nodes**, outcomes
> fingerprint `d7fe13dd60c33af8628d37fa6daad045f7bcf47831bd06f2787316e89e7a3807`.
> Architecture fitness is **1 failed / 10 passed**, not 11/11: the single failure is
> `test_api_main_line_count_within_budget` (`api/main.py` = 2805 lines, budget 2600), carried
> by PR #296.
> The recorded fixture `tests/fixtures/baseline_node_set.txt` holds **10** nodes that are a
> **strict subset** of the live 20 (verified by set difference; zero fixture nodes are absent
> from the live run). Ten live nodes are therefore unrecorded baseline debt — the
> `test_m02a_ci_gate_integrity.py` trio (`research/**` allowlist omission, from #290),
> four `test_agents_md_encoding_adjudication.py` nodes, the `api/main.py` line-budget node,
> `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points`,
> and `test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`.
> This is **fixture drift**, not a regression: this pass's own delta against the recorded
> baseline is zero new failing nodes. Reconciling the fixture is recorded as a bounded
> proposal, not performed here.

- Architecture fitness tests: **11/11**
- Full suite (`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
  --continue-on-collection-errors`): **9 failed / 1414 passed / 20 skipped / 1 error** —
  re-measured 2026-10-04 on `main` `1b7c089` (live reconciliation), **10 failing/error
  nodes**. The recorded set is those 10 nodes; 8 of the prior 18 entries had been repaired
  by later merges while the fixture kept carrying them as debt. A plain CI checkout
  additionally reports the clone-depth-dependent sibling
  `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`, which errors when the
  PR-head revision `7d79f38…` is absent.
  Classified baseline debt — see
  `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/`.
  The 49 → 20 failure reduction since `a26af408` is fully explained by the merged SH-02
  stale-assertion repair PRs (#124–#137).
  > **Superseded 2026-10-03 measurement** (`gate-hygiene/stale-gate-fixture-retirement-01`,
  > main `162f574`): **18 failed / 1304 passed / 18 skipped / 1 error**, recorded set 18
  > nodes, after retiring the two archived-surface gate nodes. Retained as history; do not
  > republish as current health. Evidence:
  > `docs/control-plane/evidence/gate-hygiene-baseline-node-set-live-reconciliation-01/`.
- Baseline fingerprint — derivation is **executable and pinned**, not prose:
  `python scripts/baseline_fingerprint.py <pytest log>` prints both values below and is
  covered by `tests/test_baseline_fingerprint.py`.
  - outcomes (canonical): `sha256("\n".join(sorted("FAILED|ERROR <nodeid>")) + "\n")` =
    `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38`
  - node set: `sha256("\n".join(sorted("<nodeid>")) + "\n")` =
    `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`
  - The recorded node set is `tests/fixtures/baseline_node_set.txt` (10 nodes); the two
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
  > **Superseded 2026-10-04** (`gate-hygiene/baseline-node-set-live-reconciliation-01`): a
  > live full-suite run on main `1b7c089` reported **9 failed / 1414 passed / 20 skipped /
  > 1 error** (10 failing/error nodes), and **8 of the 18 recorded entries now pass** — they
  > had been repaired by later merges while the fixture kept carrying them as debt. The
  > recorded set is now the **10** nodes a live run actually reports; the superseded pair is
  > retained in `tests/fixtures/superseded_baseline_node_set_18.txt`. Evidence:
  > `docs/control-plane/evidence/gate-hygiene-baseline-node-set-live-reconciliation-01/`.
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

---

## Phase 1 PERSIST — re-measured on `main` @ `357fbd8` (2026-10-03, Weaver pass `gate10/persist-phase1-runtime-state-01`)

Recorded so the next heartbeat reconstructs from evidence rather than memory.

**BASE_MAIN** = `357fbd83001924e909979fbaebdedbd991a2aadb`
(`Merge pull request #244`, 2026-10-03T17:54:44Z). Worktree clean, on a dedicated
branch off `origin/main`. PR #240 is **MERGED** by the sovereign as `444d5cd`
(2026-10-03T17:45:33Z, head `981870e`); `main` then advanced #241 `f206e77`,
#242 `7f2d265`, #244 `357fbd8`.

### Integration verified

- **CP10 allowlist repair is integrated on `main`.** `git ls-files | python
  scripts/cp10_mutation_boundary_policy.py --judge` → **RC 0**, PASS, admitting all
  **1732** tracked paths at `357fbd8`.
- `tests/architecture` + `tests/test_m02a_ci_gate_integrity.py` → **66 passed**
  (architecture alone 11/11).
- `python -m py_compile api/main.py` → OK. `api/main.py` is **2582** lines against the
  hard **2600** budget — 18 lines of headroom; treat as a protected surface.
- CI on `357fbd8`: `build`, `browser`, `Full-history secret scan` all `success`.
  CP10 (`sg-02-fe-2-v.yml`) `success` at `444d5cd` and at every PR #240 head.

### Baseline re-measured (this supersedes the `162f574` line in Repository Health)

`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
--continue-on-collection-errors` on `main` @ `357fbd8`:

| | value |
|---|---|
| result | **24 failed / 1367 passed / 19 skipped / 1 error** |
| failing+error node set | **25** |

**Delta from the PR #240 branch measurement: 28 → 25, exactly the three
`test_m02a_ci_gate_integrity.py` nodes the repair fixed; zero new failing nodes.**
The repair's own completion condition is met on `main`.

The 25-node set splits against `tests/fixtures/baseline_node_set.txt` (18 entries,
written at `d798811`) as: 14 still failing, 4 now passing (stale fixture entries),
11 absent from the fixture but all present at `cc95487` — pre-existing, not from this
repair. Classifications are in
`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md` §8.

### Fact corrections recorded this pass

Two claims were measured and **withdrawn** (detail in the EVIDENCE §8.2):

1. CP10 is **not** path-filtered for console work — `sg-02-fe-2-v.yml` does not list
   `arkadia-console-android/**`, so a console-only merge such as `444d5cd` is
   **skipped** by it, not passed. The console has its own gate,
   `.github/workflows/arkadia-console-android.yml` (`gradle assembleDebug`).
2. `arkadia-console-android/` was **not** first tracked by #237 (`cc95487`): the tree
   first appears at `8806f38`, an ancestor. Path counts `d798811` = **1726**,
   `cc95487` = **1727**, `main` @ `357fbd8` = **1732**. `main`'s "1726 at the console
   merge" is correct for the revision the fixture records; the policy comment no longer
   pins a count (a point-in-time reading is not part of the invariant).

### Open PRs (live)

- **#243** — `feature/mie-mvp-01`, head `813eaed`, base `main`, state OPEN,
  mergeability **UNSTABLE**. MIE Gate 05 change loop. **Not this workstream** — no
  action taken here; it does not touch Phase 1 runtime stabilization.

### Next bounded task

**Unchanged:** CS2 — Reusable conversational UI (recommended, **not authorized**;
requires a sovereign decision). The four candidate workstreams in
`phase1-runtime-stabilization-01/EVIDENCE.md` §6 also stand as separate bounded
branches: frontend literal pins (10 nodes), boundary regex false positives, baseline
node-set reconciliation (stale entries + 11 unrecorded nodes), and the sovereign-reserved
`weaver.autonomy` collection ERROR.

### Authority boundary

Read-only measurement plus in-repo state persistence on a dedicated branch. No test
repaired, no merge, no push to `main`. Human authority is required to merge.
