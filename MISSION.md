# Arkadia Implementation Steward
> Copy this file as the opening message to the next agent session.

---

## Status

| Item | State |
|---|---|
| Backend | **LIVE** — https://arkadia-kw64.onrender.com |
| Workstream B | **COMPLETE** — SQLite durability in production |
| Gate B | **CLOSED** |
| Workstream C | Started |
| Knowledge Layer Recon | COMPLETE — `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` |
| Deployment | STABLE — do not revisit unless a checkpoint requires it |

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
3. `docs/recon/KNOWLEDGE_OS_EVOLUTION.md`

Then run:

```bash
pytest tests/architecture -q
```

If architecture tests fail: repair only those failures.
If they pass: continue immediately.

Do not read ADRs. Do not read ROADMAP. Do not read ENGINEERING_PRINCIPLES.
Do not read CONTINUATION_LEDGER at startup — only at session end to update it.

---

## Repository Truth

Assume these are facts. Do not re-verify them.

- Runtime durability is complete. SQLite is production ready.
- Architecture governance is frozen.
- `knowledge/pipeline.py` exists and works — `ingest()` is the entry point.
- `knowledge/context_engine.py` exists and works — `assemble_context()` is the retrieval entry point.
- Semantic search, knowledge graph, timeline, and embeddings all exist.
- Corpus pipeline (`corpus/manager.py`) exists and is connected to the Oracle today.

Do not rebuild any of these.

---

## Objective

Implement the first checkpoint of Workstream K.

**Inspect only what is required** — do not explore beyond this list:

```
knowledge/pipeline.py          — find the ingest() signature
api/main.py                    — find the /api/commune/resonance handler
kernel/memory.py               — understand what currently feeds the Oracle
```

Identify:
1. Where Oracle responses are produced in `api/main.py`
2. The exact signature of `knowledge/pipeline.ingest()`
3. Where to add the post-response hook

---

## Implementation Rule

**Before writing any new code, search the repository for an existing implementation.**
If the required capability already exists anywhere in the codebase, reuse it.
Duplicate implementations are defects unless explicitly authorised by the active checkpoint.

Do not redesign.
Do not create new abstractions.
Do not create a second pipeline.
Do not replace the Context Engine.
Do not create a new graph implementation.

Connect existing systems using the smallest possible change.

---

## The Checkpoint: K2 — Oracle Conversation Archival

Every Oracle turn currently ends and is discarded.
Zero embeddings. Zero graph links. Zero future retrieval.

**The fix:** add a background thread after the Oracle response is assembled in `/api/commune/resonance` that calls `knowledge/pipeline.ingest()` with the conversation turn.

Implementation sketch (verify exact argument names against `pipeline.py`):

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

## Deliverables

Exactly one checkpoint. Exactly one commit. Exactly one push.

Update only:

```
MISSION.md                              (rewrite for next session)
.bootstrap/01_STATE.md                  (mark K2 complete, set next checkpoint)
docs/checkpoints/K2_conversation_archival.md   (checkpoint record)
docs/phase1/CONTINUATION_LEDGER.md     (session record)
```

Nothing else outside checkpoint scope.

---

## Verification

After implementation, run once:

```bash
pytest tests/architecture -q           # must be 10/10
pytest tests/ -q                       # must pass (or show only pre-existing failures)
```

The repository must remain deployable.
Workflow failures due to missing secrets are pre-existing — ignore them.

---

## Success Condition

At the end of this session:

- ✅ Oracle conversations begin entering the Knowledge Layer
- ✅ Architecture tests remain green (10/10)
- ✅ Existing Oracle behaviour is preserved (no change to response shape or latency)
- ✅ One commit pushed
- ✅ MISSION.md rewritten for the next checkpoint

Then stop immediately.
