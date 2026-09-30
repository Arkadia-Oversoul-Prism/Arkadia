# K5 — Static Ingestion

**Status:** COMPLETE — backfilled record
**Date of implementation:** ARK Y1 · D142 (2026-08-03) → final fix D… (2026-09-29)
**Date of this record:** 2026-09-30
**Role:** Implementation Steward (record) / Weaver pass (reconciliation)
**Commits:** `606510f` (routes + tracking) · `4ca0442` · `0852068` · `31818e3`

> **This document was written after the fact.** K5 shipped on `main` across the commits
> above, but the checkpoint record required by `MISSION.md` §Deliverables was never
> created, and `.bootstrap/01_STATE.md` still reported K5 as "READY TO BEGIN". This file
> closes that bookkeeping gap. No implementation code was changed by this pass.

---

## Objective

Seed the Knowledge OS with static knowledge that already existed in the repository but
had never been ingested — vault notes, ADRs, open loops, and structured markdown in
`docs/` — so SolSpire Console and the Oracle have a meaningful corpus from day one.

## Change Made

**File:** `knowledge/static_ingestion.py` (new module)

`_SOURCES` declares seven sources, six filesystem-backed and one record-backed:

| source_provider | root | glob | note_type | matches on `main` |
|---|---|---|---|---|
| `static:spiral_codex` | `static/` | `**/*.md` | `scroll` | 0 |
| `static:docs` | `docs/` | `*.md` | `document` | 16 |
| `static:collective` | `docs/collective/` | `*.md` | `document` | 5 |
| `static:creative` | `docs/creative/` | `*.md` | `document` | 7 |
| `static:adr` | `docs/adr/` | `*.md` | `document` | 6 |
| `static:vault` | `vault/` | `**/*.md` | `note` | 4 |
| `static:oracle_open_loops` | — (`kind="oracle_open_loops"`) | — | `task` | 2 rows |

**Wiring:** `api/main.py` lifespan (lines 206–207) schedules the pass in a daemon thread,
wrapped in try/except so a failure cannot block boot.

## Verification

- `pytest tests/test_static_ingestion_sources.py tests/test_static_ingestion_idempotency.py -q`
  → **12 passed**
- Direct run, sandboxed DB, twice in one process:
  - run 1 → `{"ingested": 36, "skipped": 31, "errors": 0}` in 0.9 s
  - run 2 → `{"ingested": 0, "skipped": 72, "errors": 0}` in 0.0 s
  - idempotency confirmed: second pass ingests nothing
- `pytest tests/architecture -q` → 11 passed (unchanged)
- Vault writes land under `vault/**`, which is gitignored (`.gitignore:68`); the pass
  leaves `git status` clean.

## Known gaps (recorded, not fixed — outside this checkpoint's scope)

1. **`static:spiral_codex` matches zero files.** It points at `static/**/*.md`, but
   `static/` holds only HTML/JS/CSS assets — no markdown. The declared "Spiral Codex
   scroll" corpus is empty. Either the root is wrong or the source is vestigial.
2. **`docs/` is scanned non-recursively.** `glob="*.md"` covers the 16 top-level
   documents; `docs/` holds 290 markdown files in total. The remaining ~274 — including
   `docs/control-plane/` (126), `docs/recon/` (22), `docs/phase1/` (10) and
   `docs/checkpoints/` (14) — are not ingested by this source. This is **not** pinned by
   any test: no test references `static:docs` at all (the only pinned set is the six
   ADR filenames). It is a deliberate **corpus-curation** decision — which documents
   belong in the Oracle's retrieval corpus is a sovereign call — recorded as such in
   `docs/control-plane/evidence/k5-open-loop-corpus-coverage/EVIDENCE.md` §6, which
   explicitly declined to bundle it.
3. **`note_type` diverges from the K5 design.** `docs/recon/KNOWLEDGE_OS_EVOLUTION.md`
   §K5 specifies `note_type="event"` for open loops; the implementation uses `"task"`.
   Both are valid members of `NODE_TYPES`; the divergence is recorded, not changed
   (the ontology is frozen — `NEXT_AGENT.md`).
4. **K5 shipped as a lifespan startup pass**, not as the standalone
   `scripts/ingest_static.py` the design sketch proposed. The runtime outcome is
   equivalent and is what the merged tests pin.

## Architectural Boundaries

- No new dependency, no duplicate retrieval engine, no graph implementation.
- `knowledge/static_ingestion.py` is layer-consistent (kernel→knowledge only).
- `api/main.py` untouched by this reconciliation; remains under the 2600-line budget.
- No governance, ADR, or ROADMAP edit.

## Next Checkpoint

**K4 — Response Provenance** — see `.bootstrap/01_STATE.md`.

## Standing reconciliation note

`.bootstrap/01_STATE.md` and `MISSION.md` carried a stale "K5 — READY TO BEGIN" marker
until this pass. Both are corrected here. K3 and K4 statuses were re-verified from live
evidence at the same time so the correction did not simply move the staleness one
checkpoint forward.
