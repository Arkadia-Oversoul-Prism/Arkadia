# Arkadia Implementation Steward
> Copy this file as the opening message to the next agent session.

---

## Status

| Item | State |
|---|---|
| Backend | **LIVE** — https://arkadia-kw64.onrender.com |
| Phase 0 — Endpoint migration | **COMPLETE** |
| Workstream B | **COMPLETE** — SQLite durability in production |
| Gate B | **CLOSED** |
| K2 — Oracle Conversation Archival | **COMPLETE** |
| K1 — Corpus Document Ingestion | **COMPLETE** |
| K5 — Static Ingestion | **COMPLETE** — `knowledge/static_ingestion.py`, lifespan-wired, 12 tests |
| K3 — Context Engine Wiring | **COMPLETE** — K3-A/B/C checkpointed; `assemble_context` consumed by `api/oracle_spine.py` |
| K4 — Response Provenance | **COMPLETE** — PR #153 (`4a9281b`); 6 tests; record backfilled |
| Workstream K | **COMPLETE** — no K6 exists in the design doc |
| Deployment | STABLE — do not revisit unless a checkpoint requires it |

---

## ⚠ One Manual Action Required Before Deploying Frontend

`web/public_prism/.env.production` could not be updated by the agent (env file protection).

**Before the next Vercel frontend deploy, set:**
```
VITE_API_URL=https://arkadia-kw64.onrender.com
```
Either in the Vercel dashboard under Environment Variables, or by updating `.env.production` manually.

---

## Mission

**Workstream K is COMPLETE. Select the next workstream — that is a sovereign decision.**

K2, K1, K5, K3 and K4 are all shipped. The Knowledge OS now receives:
- Every Oracle conversation (K2)
- Every corpus document on upload, creation, and refresh (K1)
- Static repository knowledge — vault notes, ADRs, open loops, structured docs (K5)
- Context assembly over the populated graph, via the shared spine (K3)
- The retrieved note identities, surfaced as citable `sources` on the Oracle response (K4)

Every K checkpoint now carries a record under `docs/checkpoints/`.

> **Status reconciliation (2026-10-02, pass `gate-k/k4-status-reconciliation`):** this file
> previously reported **K4 as NEXT** while K4 had already shipped on `main` via PR #153
> (`4a9281b`). The record is backfilled at `docs/checkpoints/K4_response_provenance.md` and
> the status table above now reflects verified state. This is the same staleness class that
> K5 carried until 2026-09-30; both are now closed.
>
> **Superseded note (2026-09-30):** this file previously instructed the next agent to
> implement K5. K5 had already shipped across `606510f`, `4ca0442`, `0852068`, `31818e3`.

---

## Startup Protocol (Maximum 5 minutes)

Read only:

1. `MISSION.md` (this file)
2. `.bootstrap/01_STATE.md`
3. `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → section "K4" only

Then run:

```bash
pytest tests/architecture -q
```

If architecture tests fail: repair only those failures, then continue.
If they pass: continue immediately.

**Do not read:** ADRs, ROADMAP, ENGINEERING_PRINCIPLES, CONTINUATION_LEDGER (update it at session end only).

---

## Repository Truth

Assume these are facts. Do not re-verify them.

- Runtime durability is complete. SQLite is production ready.
- Architecture governance is frozen.
- K2 complete: Oracle turns archived to `knowledge/arkadia.db` via `_archive_oracle_turn()` in `api/main.py`.
- K1 complete: All three corpus ingestion entry points (`/api/scrolls`, `/api/codex/upload`, `/api/corpus/refresh`) now fire `_ingest_to_knowledge_os()` in background threads after saving.
- K4 complete: `build_sources()` in `api/oracle_spine.py` derives citations from the context package that was actually injected; `sources` is on the Oracle response; `ArkanaCommune.tsx` renders them conditionally. Provenance is a view of the retrieval that already happened — never a second query.
- `knowledge/pipeline.py` — `ingest()` is the entry point; duplicate-detection makes it idempotent.
- `knowledge/context_engine.py` — `assemble_context()` is the retrieval entry point.
- Semantic search, knowledge graph, timeline, and embeddings all exist.
- All production references point to `https://arkadia-kw64.onrender.com`.

Do not rebuild any of these.

---

## Recommended Next Workstream — CS2: Reusable conversational UI

**This is a recommendation, not an authorization. Beginning it requires a sovereign
decision**, because it is a product scope expansion beyond the (now complete) Workstream K.

The Oracle Chat UI is the reference interaction experience and must be preserved, not
rebuilt. CS2 extracts and generalises its proven capabilities (TTX, canvas/full-display,
rich response presentation, response controls) into a reusable conversational component
boundary so all surfaces inherit ONE canonical chat shell over the same spine.

Do NOT flatten to a generic chat box; do NOT rebuild the Oracle UI from scratch.

Out of scope for CS2 (later checkpoints): NovaNet localStorage→server message persistence,
ReasoMate standalone routing, Encyclopedia/Codex duplicate-surface reconciliation,
NovaNet sample-data removal.

### Standing candidates that require a sovereign ruling first

These are recorded in `PARKING_LOT.md` and **must not** be silently folded into another
workstream:

1. `weaver.autonomy` module/package shadowing — which object is canonical is an
   **authority-model** question, and therefore sovereign.
2. Spiral Grove registry declaration-order vs topological-order contract — which contract
   the registry means is a design ruling.
3. Baseline test debt — separately classified; see Repository Health below.

---

## Open items recorded, not fixed (from the K5 pass)

1. `static:spiral_codex` points at `static/**/*.md`, which matches zero files — `static/`
   holds only HTML/JS/CSS assets.
2. `static:docs` uses a non-recursive `*.md` glob, so ~274 of 290 markdown files under
   `docs/` (incl. `docs/control-plane/` ×126, `docs/recon/` ×22) are not ingested. Not
   test-pinned — no test references `static:docs`. It is a **corpus-curation** decision
   reserved to the sovereign, per
   `docs/control-plane/evidence/k5-open-loop-corpus-coverage/EVIDENCE.md` §6.
3. K5 uses `note_type="task"` for open loops where the design sketch said `"event"`.

Each is a candidate for its own bounded workstream.

---

## Implementation Rule

**Before writing any new code, search the repository for an existing implementation.**
If the required capability exists anywhere in the codebase, reuse it.
Duplicate implementations are defects unless explicitly authorised by the checkpoint.

---

## Constraints

- No governance edits
- No ADR edits
- No ROADMAP edits
- No architecture refactors
- No speculative optimisation
- No new framework or dependency
- No duplicate retrieval engine
- No new graph implementation
- No replacement of the Context Engine

---

## Pre-Push Checklist

Before every commit, run a repository-wide search for:

```bash
grep -rn "TODO\|FIXME\|XXX\|HACK\|arkadia-n26k" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.mjs" . 2>/dev/null | grep -v "docs/adr/" | grep -v "docs/recon/" | grep -v ".env.production"
```

If any were introduced by this checkpoint: resolve them or record them explicitly in the checkpoint document before pushing.

---

## Repository Health (re-measured 2026-10-02, `main` @ `64cbe74`)

- Architecture fitness tests: **11/11**
- Full suite: **20 failed / 1240 passed / 17 skipped / 1 error** (21 failing/error nodes).
  Classified baseline debt — not attributable to new work unless the node *set* changes.
- Baseline fingerprint:
  `sha256("\n".join(sorted(FAILED/ERROR node ids)) + "\n")` =
  `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7`
  (node-set fingerprint `da2ec262…`). The previously published `a59453b8…` is **not
  reproducible** — see
  `docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/`.
- Gate-2 production parity: **BLOCKED on provider auth** (Vercel Deployment Protection).
  External boundary, not a repository task. Do not re-run the pass expecting a different
  classification.

---

## Deliverables

Exactly one checkpoint. Exactly one commit. Exactly one push.

Update only:

```
MISSION.md                                      (rewrite for next workstream)
.bootstrap/01_STATE.md                          (reflect current position)
NEXT_AGENT.md                                   (rewrite for next workstream)
docs/checkpoints/<checkpoint>.md               (checkpoint record)
docs/phase1/CONTINUATION_LEDGER.md             (session record — at session end)
```

Nothing else outside checkpoint scope.

---

## Verification

After implementation, run once:

```bash
pytest tests/architecture -q           # must be 11/11
pytest tests/ -q                       # pre-existing failures acceptable; node set must not grow
```

---

## Success Condition

At the end of this session:

- ✅ Workstream K status reflects verified state — every K checkpoint recorded
- ✅ Architecture tests remain green (11/11)
- ✅ Baseline failure node *set* unchanged (counts alone are not the oracle)
- ✅ Pre-push checklist clean
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next workstream, with the sovereign decision named

Then stop immediately.
