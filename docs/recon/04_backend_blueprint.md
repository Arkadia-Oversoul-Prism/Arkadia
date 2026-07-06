# 04 — Backend Blueprint

Scope: `api/` (FastAPI).

## Entry Point
`api/main.py` (~88KB) — the largest single file in the repo. Boots a background corpus-sync daemon, mounts `/static`, configures CORS, registers kernel worker lifecycle events, and defines the majority of top-level routes directly (not all delegated to routers).

## Mounted Routers
| Router file | Mounted for |
|---|---|
| `api/nodes.py` | Node registry & personal codices |
| `api/distribution.py` | Music distribution / aggregator submission |
| `api/ims_products.py` | IMS diagnostic & product engine |
| `api/pulse.py` | Identity Measurement Engine (Likert-scale psychometrics) |
| `solspire/console_router.py` | SolSpire "Milestone 1" console API |

## Key Routes Defined Directly in `api/main.py`
| Path | Method | Purpose |
|---|---|---|
| `/api/forge` | POST | Image generation (archetype/prompt/count) |
| `/api/dashboard/loops` | GET | Enriched open-loops action matrix |
| `/api/ark-date` | GET | Arkadia epoch date/sync status |
| `/api/webhook/github` | POST | GitHub push → corpus re-sync trigger |
| `/api/codex/github-tree` | GET | Full corpus file list from GitHub |
| `/api/codex/upload` | POST | Direct scroll upload (multipart) |
| `/api/orders` | POST/GET | Living Larder orders (GET is sovereign-gated) |
| `/api/ims/inquiry` | POST/GET | IMS booking inquiries (GET is sovereign-gated) |
| `/api/jobs`, `/api/job/create`, `/api/job/{id}`, `/api/job/{id}/trace` | — | SolSpire kernel job orchestration |
| `/api/goals` (CRUD) | — | SolSpire persistent goals |
| `/api/ceo/chat` | POST | ARKANA CEO-advisor chat with tool-call parsing |
| `/api/heartbeat`, `/api/commune/resonance`, `/api/codex`, `/api/corpus`, `/api/corpus/refresh`, `/api/sources`, `/api/coherence-reset` | — | Oracle chat + corpus endpoints (documented in replit.md) |
| `/arkadia/generate`, `/arkadia/compress`, `/arkadia/expand` | POST | Symbolic Engine (deterministic, no LLM) |

## Router-Owned Endpoints
- **`api/nodes.py`**: `/api/codex/personal` (unauthenticated by design), `/api/me`, `/api/nodes` (sovereign), `/api/nodes/{key}/codex`.
- **`api/ims_products.py`**: `/api/ims/archetypal-analyze` (Gemini), `/api/ims/diagnostic`, `/api/products/purchase` (Paystack), `/api/products/dashboard/{id}`.
- **`api/distribution.py`**: `/api/distribution/upload`, `/api/distribution/covenant/sign`, `/api/distribution/submit`.
- **`api/pulse.py`**: `/api/pulse/analyze` (12-node score + sigil SVG + Oracle summary).
- **`api/arkadia_engine.py`**: no HTTP routes of its own — pure functions consumed by `main.py`'s `/arkadia/*` routes and by the chat command shortcut (`⟐ generate/compress/expand`).

## Authentication & Authorization
- `api/auth.py`: Firebase Admin SDK. `get_current_user` (decodes Firebase ID token), `require_auth`, `require_sovereign` (access level 3+).
- **Dev-mode fallback**: if `FIREBASE_SERVICE_ACCOUNT_JSON` is unset, `get_current_user` decodes JWTs **without verifying the signature**. Flagged as a security risk — see Security Audit.
- Node-to-user mapping via `data/nodes_seed.json`, matched by email hint or `node_key` claim.

## CORS
`allow_origins=["*"]`, all methods/headers allowed. Wide open — see Security Audit.

## Corpus Engine (`corpus/`)
- `manager.py`: `CorpusManager` aggregates `GitHubSource`, `GoogleDriveSource`, `JoplinSource`, `ObsidianSource`; supports `docs/CORPUS_MANIFEST.json` metadata overrides; 6-hour disk cache (`arkadia_cache.json`).
- `api/main.py` layers an additional 60-second in-memory cache on top for GitHub freshness checks.
- Priority scoring (1–3) is assigned per-document based on directory mapping in `github.py`.

## Uncertainty
- Exact line-by-line request/response Pydantic models for every route were not individually enumerated in this pass — recommend a follow-up OpenAPI-schema export (`/openapi.json`) diff if per-field contract documentation is needed.
