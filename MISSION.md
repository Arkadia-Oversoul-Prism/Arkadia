# Arkadia Implementation Steward
> Copy this file as the opening message to the next agent session.

---

## Status

| Item | State |
|---|---|
| Backend | **LIVE** — https://arkadia-kw64.onrender.com |
| Phase 0 — Endpoint migration | **COMPLETE** — all active references updated |
| Workstream B | **COMPLETE** — SQLite durability in production |
| Gate B | **CLOSED** |
| Workstream C | Started |
| Knowledge Layer Recon | COMPLETE — `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` |
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

**Begin Workstream K — Knowledge OS Integration**

This workstream does not build a Knowledge Layer.
It connects the one that already exists.

---

## Startup Protocol (Maximum 5 minutes)

Read only:

1. `MISSION.md` (this file)
2. `.bootstrap/01_STATE.md`
3. `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` → sections "The Checkpoint: K2" and "Summary for Implementation Agent"

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
- `knowledge/pipeline.py` exists — `ingest()` is the entry point.
- `knowledge/context_engine.py` exists — `assemble_context()` is the retrieval entry point.
- Semantic search, knowledge graph, timeline, and embeddings all exist.
- Corpus pipeline (`corpus/manager.py`) is connected to the Oracle today.
- All production references point to `https://arkadia-kw64.onrender.com`.

Do not rebuild any of these.

---

## Objective: K2 — Oracle Conversation Archival

**The gap:** Every Oracle turn currently ends and is discarded.
Zero embeddings. Zero graph links. Zero future retrieval.

**The fix:** ~8 lines. A fire-and-forget background thread after the Oracle response
is assembled in `/api/commune/resonance` that calls `knowledge/pipeline.ingest()`.

**Files to read before writing any code:**

```
api/main.py              — find /api/commune/resonance handler; locate where
                           the response string is assembled before return
knowledge/pipeline.py    — lines ~180–260: verify ingest() signature
```

**Implementation sketch** (verify argument names against actual `pipeline.py`):

```python
import threading
from knowledge import pipeline as kp

def _archive_oracle_turn(user_input: str, response: str, session_id: str) -> None:
    try:
        kp.ingest(
            title=f"Oracle — {session_id[:8] if session_id else 'anon'}",
            content=f"User: {user_input}\n\nArkana: {response}",
            note_type="conversation",
            tags=["oracle", "conversation"],
        )
    except Exception:
        pass  # Never block the Oracle response

threading.Thread(
    target=_archive_oracle_turn,
    args=(user_input, arkana_response, session_id),
    daemon=True,
).start()
```

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
.bootstrap/01_STATE.md                          (mark K2 complete, set K1 as next)
NEXT_AGENT.md                                   (rewrite for K1)
docs/checkpoints/K2_conversation_archival.md    (checkpoint record)
docs/phase1/CONTINUATION_LEDGER.md              (session record — at session end)
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

The Implementation Steward writes the checkpoint. The Verification Steward signs it off before merge.

---

## Success Condition

At the end of this session:

- ✅ Oracle conversations begin entering the Knowledge Layer
- ✅ Architecture tests remain green (10/10)
- ✅ Existing Oracle behaviour is preserved (response shape and latency unchanged)
- ✅ Pre-push checklist clean
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next checkpoint (K1)

Then stop immediately.
