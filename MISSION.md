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

**Begin Workstream K — Checkpoint K1: Corpus Document Ingestion**

K2 is complete. Oracle conversations now enter the Knowledge Layer automatically.

K1 connects the corpus ingestion pipeline so that uploaded/synced documents (scrolls, PDFs, markdown files) are processed through `knowledge/pipeline.ingest()` rather than only through the corpus RAG layer. This makes the Knowledge Graph aware of the full document corpus — not just Oracle conversations.

---

## Startup Protocol (Maximum 5 minutes)

Read only:

1. `MISSION.md` (this file)
2. `.bootstrap/01_STATE.md`
3. `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → section "K1" only

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
- K2 complete: Oracle turns are now archived to `knowledge/arkadia.db` via `_archive_oracle_turn()` daemon thread in `api/main.py`.
- `knowledge/pipeline.py` exists — `ingest()` is the entry point.
- `knowledge/context_engine.py` exists — `assemble_context()` is the retrieval entry point.
- Semantic search, knowledge graph, timeline, and embeddings all exist.
- Corpus pipeline (`corpus/manager.py`) is connected to the Oracle today.
- All production references point to `https://arkadia-kw64.onrender.com`.

Do not rebuild any of these.

---

## Objective: K1 — Corpus Document Ingestion

**The gap:** Uploaded corpus documents (scrolls, PDFs, markdown) are served through the RAG corpus layer but are NOT ingested into the Knowledge Layer (`knowledge/arkadia.db`). The Knowledge Graph has no awareness of document content — only of Oracle conversations (added in K2).

**The fix:** After a document is successfully stored/synced in the corpus, call `knowledge/pipeline.ingest()` with the document content. This should be a one-time ingestion per document (idempotent via the duplicate-detection already in `pipeline.ingest()`).

**Files to read before writing any code:**

```
corpus/manager.py        — find where documents are stored/synced after upload
knowledge/pipeline.py    — lines 182–210: ingest() signature (already verified in K2)
api/main.py              — find corpus upload/sync endpoint(s)
```

**Implementation approach** (verify against actual code before writing):

After a document is stored to the corpus, call in a daemon thread:

```python
threading.Thread(
    target=_ingest_corpus_document,
    args=(title, content, source_path),
    daemon=True,
).start()
```

Where `_ingest_corpus_document` calls `pipeline.ingest()` with `note_type="document"` and appropriate tags.

**Standing question — ask before every code change:**
> What is the smallest connection that unlocks the existing Knowledge Layer without increasing maintenance?

---

## Implementation Rule

**Before writing any new code, search the repository for an existing implementation.**
If the required capability exists anywhere in the codebase, reuse it.
Duplicate implementations are defects unless explicitly authorised by the checkpoint.

Do not redesign. Do not create new abstractions. Do not create a second pipeline.
Do not replace the Context Engine. Do not create a new graph implementation.

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

If any were introduced by this checkpoint: resolve them or record them explicitly
in the checkpoint document before pushing.

---

## Deliverables

Exactly one checkpoint. Exactly one commit. Exactly one push.

Update only:

```
MISSION.md                                      (rewrite for next checkpoint)
.bootstrap/01_STATE.md                          (mark K1 complete, set K5 as next)
NEXT_AGENT.md                                   (rewrite for K5)
docs/checkpoints/K1_corpus_ingestion.md        (checkpoint record)
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

The repository must remain deployable.
Workflow failures due to missing secrets are pre-existing — ignore them.

---

## Steward Roles (from this point forward)

Arkadia now uses parallel stewards per session:

| Role | Responsibility |
|---|---|
| **Implementation Steward** | Ships the active checkpoint — writes code, runs tests, commits |
| **Verification Steward** | Reviews the diff, runs full test suite, checks architectural boundaries, confirms the commit |
| **Recon Steward** | Investigates unfamiliar code without changing it — produces a report, never commits |

One engineer builds. Another validates. This preserves architectural discipline at speed.

---

## Success Condition

At the end of this session:

- ✅ Corpus documents begin entering the Knowledge Layer on ingest
- ✅ Architecture tests remain green (10/10)
- ✅ Existing corpus RAG behaviour is preserved (response shape and latency unchanged)
- ✅ Pre-push checklist clean
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next checkpoint (K5)

Then stop immediately.
