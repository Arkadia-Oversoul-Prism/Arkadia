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
| K4 — Response Provenance | **NEXT** |
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

**Workstream K — Checkpoint K4: Response Provenance**

K2, K1, K5 and K3 are complete. The Knowledge OS now receives:
- Every Oracle conversation (K2)
- Every corpus document on upload, creation, and refresh (K1)
- Static repository knowledge — vault notes, ADRs, open loops, structured docs (K5)
- Context assembly over the populated graph, via the shared spine (K3)

K4 makes what the Oracle already retrieves *visible*. `knowledge/context_engine.assemble_context()` returns note UUIDs alongside the text chunks it selects, but the Oracle response discards them — the user sees a confident answer with no way to tell which archived knowledge produced it. K4 surfaces those identities as a `sources` array so answers become citable.

> **Status reconciliation (2026-09-30):** this file previously instructed the next agent to implement K5. K5 had already shipped on `main` across `606510f`, `4ca0442`, `0852068`, `31818e3`. The record is backfilled at `docs/checkpoints/K5_static_ingestion.md` and the status table above now reflects verified state.

---

## Startup Protocol (Maximum 5 minutes)

Read only:

1. `MISSION.md` (this file)
2. `.bootstrap/01_STATE.md`
3. `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → section "K5" only

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
- `knowledge/pipeline.py` — `ingest()` is the entry point; duplicate-detection makes it idempotent.
- `knowledge/context_engine.py` — `assemble_context()` is the retrieval entry point.
- Semantic search, knowledge graph, timeline, and embeddings all exist.
- All production references point to `https://arkadia-kw64.onrender.com`.

Do not rebuild any of these.

---

## Objective: K4 — Response Provenance

**The gap:** The Oracle answers from retrieved knowledge but never says which knowledge.
`assemble_context()` already returns the note identities it used; the Oracle response
shape drops them, so every answer is uncitable and unverifiable by the reader.

**The fix:** Propagate the retrieved note identities out of the spine and into the Oracle
response as a `sources` array, then render them in the UI.

**Files to read before writing any code:**

```
knowledge/context_engine.py   — assemble_context() return shape; where note UUIDs live
api/oracle_spine.py           — retrieve_arkana_context() / build_memory_block() — the
                                seam where the context package is already in hand
api/main.py                   — /api/commune/resonance response shape (additive only)
web/public_prism/src/components/ArkanaCommune.tsx  — render "Based on: ..." citations
```

**Implementation approach** (verify against actual code before writing):

`api/oracle_spine.py` already receives the full context package from
`assemble_context()`. Extract the note identities there into the existing diagnostics
dict (`meta`) rather than re-querying — one seam, no second retrieval path. Then thread
that through the Oracle response and render conditionally in the UI.

**Standing question — ask before every code change:**
> What is the smallest connection that unlocks the existing Knowledge Layer without increasing maintenance?

**Verified starting state:** no Oracle response path currently returns a `sources`
array. `api/oracle_spine.py` reports only `notes_retrieved` (a count) and `source` (a
provenance label) — identities are available but not propagated.

**Explicitly out of scope for K4 (recorded, not fixed):**

1. `static:spiral_codex` points at `static/**/*.md`, which matches zero files — `static/`
   holds only HTML/JS/CSS assets.
2. `static:docs` uses a non-recursive `*.md` glob, so ~274 of 290 markdown files under
   `docs/` (incl. `docs/control-plane/` ×126, `docs/recon/` ×22) are not ingested. Not
   test-pinned — no test references `static:docs`. It is a **corpus-curation** decision
   reserved to the sovereign, per
   `docs/control-plane/evidence/k5-open-loop-corpus-coverage/EVIDENCE.md` §6.
3. K5 uses `note_type="task"` for open loops where the design sketch said `"event"`.

Each is a candidate for its own bounded workstream; none is in K4's scope.

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

## Deliverables

Exactly one checkpoint. Exactly one commit. Exactly one push.

Update only:

```
MISSION.md                                      (rewrite for next checkpoint)
.bootstrap/01_STATE.md                          (mark K4 complete, set next)
NEXT_AGENT.md                                   (rewrite for next checkpoint)
docs/checkpoints/K4_response_provenance.md     (checkpoint record)
docs/phase1/CONTINUATION_LEDGER.md             (session record — at session end)
```

Nothing else outside checkpoint scope.

---

## Verification

After implementation, run once:

```bash
pytest tests/architecture -q           # must be 11/11
pytest tests/ -q                       # must pass (pre-existing failures acceptable)
```

---

## Success Condition

At the end of this session:

- ✅ Vault, ADRs, and structured docs are ingested into the Knowledge OS on startup
- ✅ Architecture tests remain green (11/11)
- ✅ Startup time not materially increased (ingestion is background/daemon)
- ✅ Pre-push checklist clean
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next checkpoint (K3)

Then stop immediately.
