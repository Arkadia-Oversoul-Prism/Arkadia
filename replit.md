# Arkadia Knowledge OS

## Overview

Arkadia is a local-first **Knowledge Operating System** — not a chatbot, not an AI wrapper.

Knowledge is the primary asset. AI providers are interchangeable reasoning adapters.

> If every current AI provider disappeared tomorrow, the user's accumulated knowledge and the architecture that organises it would remain intact and usable.

---

## Architecture

```
Prism (React/Vite)  →  Oracle Temple (FastAPI)  →  Knowledge Vault (Markdown + SQLite)
                                 ↓
                        Provider Router (Gemini, Claude, GPT, …)
```

### Five Services

| Service | Path | Run command |
|---------|------|-------------|
| Oracle Temple (backend) | `api/main.py` | `python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000` |
| Arkadia Prism (frontend) | `web/public_prism/` | `cd web/public_prism && npm run dev` |
| Discord Bot | `bot/discord-bot.mjs` | `node bot/discord-bot.mjs` |
| Telegram Bot | `bot/telegram-bot.mjs` | `node bot/telegram-bot.mjs` |

---

## Knowledge OS Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| Knowledge Vault | `vault/` | Markdown note storage (human format) |
| SQLite Database | `knowledge/arkadia.db` | Machine-readable index |
| Pipeline | `knowledge/pipeline.py` | `ingest()` — the main entry point |
| Context Engine | `knowledge/context_engine.py` | Semantic retrieval for providers |
| Knowledge Graph | `knowledge/graph.py` | Note relationships + traversal |
| Search | `knowledge/search.py` | 7 search modes |
| Timeline | `knowledge/timeline.py` | Immutable event log |
| Embeddings | `knowledge/embeddings.py` | Gemini embed + BM25 fallback |
| Provider Router | `providers/router.py` | AI provider abstraction |
| Gemini Adapter | `providers/gemini.py` | Implements BaseProvider |
| Knowledge API | `api/knowledge_routes.py` | `/api/knowledge/*` routes |

---

## Required Environment Variables

### Critical (backend won't function without these)
```
GEMINI_API_KEY          — Google Gemini API key (primary LLM + embeddings)
```

### Firebase (auth + Firestore sync)
```
FIREBASE_CREDENTIALS    — Firebase Admin SDK service account JSON (base64 or path)
VITE_FIREBASE_API_KEY
VITE_FIREBASE_AUTH_DOMAIN
VITE_FIREBASE_PROJECT_ID
VITE_FIREBASE_APP_ID
VITE_FIREBASE_MESSAGING_SENDER_ID
VITE_FIREBASE_STORAGE_BUCKET
```

### Optional / Additive
```
GEMINI_MODEL            — Override default model (default: gemini-2.0-flash)
ARKADIA_DB_PATH         — Override SQLite db path (default: knowledge/arkadia.db)
GITHUB_PERSONAL_ACCESS_TOKEN  — GitHub corpus integration
SOVEREIGN_KEY           — Internal auth key (default: arkadia-forge-2026)
```

### Bot-specific
```
DISCORD_BOT_TOKEN
TELEGRAM_BOT_TOKEN
WHATSAPP_TOKEN
```

---

## Knowledge OS API

All routes are at `/api/knowledge/*`. See `ARKADIA_KNOWLEDGE_OS.md` for full docs.

### Quick reference

```bash
# Ingest a note through the full pipeline
POST /api/knowledge/ingest

# Ingest a conversation (prompt + response)
POST /api/knowledge/ingest/conversation

# Send a message with automatic knowledge context
POST /api/knowledge/providers/send

# Search (semantic + fulltext + tag + ...)
POST /api/knowledge/search

# Knowledge graph
GET /api/knowledge/graph

# Timeline
GET /api/knowledge/timeline

# System status
GET /api/knowledge/status
```

---

## Migration (run once)

To port existing oracle_store.json data into the Knowledge OS:

```bash
python -m knowledge.migrate
```

---

## Architecture Decision Records

| ADR | Decision |
|-----|---------|
| ADR-010 | Knowledge Vault as canonical truth store |
| ADR-011 | Provider Router — AI providers as replaceable adapters |
| ADR-012 | Context Engine — semantic retrieval, not memory dump |

Full ADRs: `docs/adr/`  
Full architecture doc: `ARKADIA_KNOWLEDGE_OS.md`

---

## Architectural Laws

1. **One capability. One implementation. One canonical home.**
2. **Local First.** Cloud sync is additive. Never required.
3. **Markdown is the human format. SQLite is the machine format.**
4. **Oracle retrieves knowledge. Providers generate language.**
5. **Every subsystem must have a single responsibility.**

---

## User Preferences

- Knowledge OS architecture must be preserved — do not introduce duplicate implementations
- Markdown is the canonical human format for all notes
- SQLite is the canonical machine format — no alternative databases
- Provider router interface is fixed — new providers implement BaseProvider only
- Timeline is immutable — never update or delete timeline rows
