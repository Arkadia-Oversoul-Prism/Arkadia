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

**Workstream K — Checkpoint K5: Static Ingestion**

K2 and K1 are complete. The Knowledge OS now receives:
- Every Oracle conversation (K2)
- Every corpus document on upload, creation, and refresh (K1)

K5 connects the remaining static knowledge that already exists in the repository but has never been ingested: the vault notes, ADRs, open loops, and any other structured markdown in `docs/`. This completes the initial Knowledge OS population and ensures SolSpire Console has a meaningful corpus from day one.

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

## Objective: K5 — Static Ingestion

**The gap:** The vault, ADRs, open-loop documents, and other structured markdown files in `docs/` contain critical Arkadia knowledge that has never been ingested into the Knowledge OS. SolSpire Console's graph and search will be sparse until this static corpus is seeded.

**The fix:** A one-time startup ingestion pass that reads static markdown files from known paths and calls `knowledge/pipeline.ingest()` for each. Idempotent — duplicate-detection prevents re-ingestion on restart.

**Files to read before writing any code:**

```
knowledge/pipeline.py     — ingest() signature (already known)
api/main.py               — lifespan() or startup hook — best place to add one-time pass
docs/                     — survey which subdirectories contain ingestable knowledge
knowledge/vault/          — if it exists, this is the primary vault source
```

**Implementation approach** (verify against actual code before writing):

In the FastAPI `lifespan()` startup block (already exists in `api/main.py`), add a daemon thread that walks known static paths and calls `_ingest_to_knowledge_os()` for each file. Runs once at startup. Duplicate-detection inside `pipeline.ingest()` makes restarts safe.

**Standing question — ask before every code change:**
> What is the smallest connection that unlocks the existing Knowledge Layer without increasing maintenance?

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
.bootstrap/01_STATE.md                          (mark K5 complete, set K3 as next)
NEXT_AGENT.md                                   (rewrite for K3)
docs/checkpoints/K5_static_ingestion.md        (checkpoint record)
docs/phase1/CONTINUATION_LEDGER.md             (session record — at session end)
```

Nothing else outside checkpoint scope.

---

## Verification

After implementation, run once:

```bash
pytest tests/architecture -q           # must be 10/10
pytest tests/ -q                       # must pass (pre-existing failures acceptable)
```

---

## Success Condition

At the end of this session:

- ✅ Vault, ADRs, and structured docs are ingested into the Knowledge OS on startup
- ✅ Architecture tests remain green (10/10)
- ✅ Startup time not materially increased (ingestion is background/daemon)
- ✅ Pre-push checklist clean
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next checkpoint (K3)

Then stop immediately.
