# 05 — Database Blueprint

Arkadia has **no single database** — it is a federation of JSON files, one SQLite database, and Firestore, each canonical for a different domain.

## JSON File Stores (`data/`)
| File | Canonical for | Read/Write code |
|---|---|---|
| `data/oracle_store.json` | SolSpire kernel state: `transactions`, `open_loops`, `assets`, `balance` (derived), `events` | `kernel/oracle_store.py` (CRUD), `kernel/memory.py` (read-only retrieval) |
| `data/job_store.json` | Background kernel job queue/status/trace | `kernel/jobs.py`; mirrored to Firestore via `api/firebase_store.py` |
| `data/goal_store.json` | Persistent long-running agent goals | `kernel/goals.py`; mirrored to Firestore via `api/firebase_store.py` |
| `data/nodes_seed.json` | Registered "nodes" (users) for auth mapping | `weaver/user_profiles.py`, `api/auth.py` |
| `data/ims_credentials_sealed.json` | Sealed IMS credential/access records | referenced by IMS product flow (not fully traced this pass) |
| `data/api_keys.json` | Fallback Gemini/Google API key storage | `api/key_manager.py` |

## SQLite
`data/solspire_projects.db` — canonical **only** for the SolSpire project-management domain (a different feature area than the kernel above): tables `project_conversations`, `project_files`, `project_repositories`, `project_tasks`, `project_memory`, `project_events`. Accessed via `solspire/project_store.py` using the stdlib `sqlite3` module (no ORM).

## Firestore (Firebase)
- Collections: `users`, `jobs`, `goals`.
- Frontend usage (`web/public_prism/src/services/conversationService.ts`): stores chat messages at `users/{uid}/conversations/{sid}/messages` and derived user "patterns" at `users/{uid}/profile`.
- Backend usage (`api/firebase_store.py`): acts as a **durability mirror** for `job_store.json`/`goal_store.json`, not an independent write path — important because Replit's filesystem is not guaranteed persistent across restarts/deploys.
- Firebase Auth (`web/public_prism/src/contexts/AuthContext.tsx`): `signInWithEmailLink`, `signInAnonymously`.

## PostgreSQL (isolated, non-canonical for main product)
Found only inside `attached_assets/arkadia_spirit/GovernanceSpirit/server/db.ts` — a fully separate nested project (Drizzle ORM, tables `users`, `essence_entries`, `hints`, `messages`). This is **not part of the live Arkadia product** as currently deployed; it is an archived/reference sub-app.

## Redis
Referenced only via `@upstash/redis` in dependency trees and Drizzle cache adapter typings — appears scoped to the `GovernanceSpirit` sub-app, not the main product. **No confirmed live Redis usage in `api/` or `kernel/`.**

## Growth / Performance Risk Notes (not measured — flagged for instrumentation)
- JSON-file stores (`oracle_store.json`, `job_store.json`, `goal_store.json`) have no indexing, no pagination, and are fully read/rewritten on each mutation (typical of the "atomic write to JSON" pattern per replit.md). This scales fine for the current scroll/job/goal counts (dozens–hundreds) but will need a real database if volume grows into the thousands. **Not currently measured** — no evidence of current file sizes was gathered this session.
