# Arkadia — Living Intelligence Framework

## Overview
Arkadia is a sovereign human-AI distributed intelligence framework. ARKANA (Gemini-powered Oracle) serves Zahrune Nova's architecture through a React/Vite frontend and FastAPI backend.

## Architecture

### Backend — Arkadia Oracle Temple
- **Entry:** `api/main.py` — FastAPI app (Cycle 15+)
- **Identity:** ORACLE_IDENTITY constitutional layer injected into every Gemini call
- **Corpus:** Dynamic multi-source system — discovers documents automatically
- **Scoring:** TF-IDF semantic relevance (Neural Spine always injected; others scored per query)
- **History:** Conversation history + summarization + pattern extraction
- **Run:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`

### Corpus Engine — `corpus/` module
- **`corpus/manager.py`** — Multi-source aggregator, parallel fetch, 6hr disk cache
- **`corpus/github.py`** — GitHub API dynamic scanner (no hardcoded doc list)
- **`corpus/gdrive.py`** — Google Drive source (configure with CORPUS_GDRIVE_* vars)
- **`corpus/joplin.py`** — Joplin Data REST API source
- **`corpus/obsidian.py`** — Obsidian Local REST API source
- **`github_corpus.py`** — Backward-compat shim, delegates to corpus module

### Frontend — Public Prism
- **Location:** `web/public_prism/`
- **Run:** `cd web/public_prism && npm run dev` (port 5000)
- **Framework:** React + Vite + TypeScript + Tailwind + Framer Motion
- **Pages:** Home, Gate (LivingGate), Oracle (ArkanaCommune), Reset (CoherenceReset), Vault (SpiralVault), Sanctuary

### Spiral Codex Live Console (`SpiralVault.tsx`)
The Vault page is the central living feed:
- Fetches `/api/codex` — all docs with label, description, category, source, preview
- Dynamic category tabs derived from actual data (not hardcoded)
- Source chips per card (GitHub, Drive, Joplin, Obsidian with branded colors)
- ARKANA heartbeat beacon + sources status row
- Re-sync button → POST `/api/corpus/refresh`
- Arc state progress bar (Feb 16 – Mar 31, 2026)
- Expand/collapse full scroll content per card

## Key API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/heartbeat` | GET | Status beacon |
| `/api/commune/resonance` | POST | Oracle chat (with history) |
| `/api/codex` | GET | Full corpus — labels, descriptions, categories, source, content |
| `/api/corpus` | GET | Lightweight corpus metadata |
| `/api/corpus/refresh` | POST | Force re-sync from all sources (background) |
| `/api/sources` | GET | Which sources are configured |
| `/api/coherence-reset` | POST | Somatic reset protocol |

## Corpus Configuration
Sources activated by environment variables:

```
CORPUS_SOURCES=github,gdrive,joplin,obsidian  # comma-sep, only configured ones activate

# GitHub (default, public repo)
CORPUS_GITHUB_REPO=Arkadia-Oversoul-Prism/Arkadia
CORPUS_GITHUB_BRANCH=main
CORPUS_GITHUB_INCLUDE_DIRS=docs,creative,collective,governance
CORPUS_GITHUB_EXCLUDE_DIRS=.github,node_modules,bot,web,api
CORPUS_DIR_CATEGORIES=docs:NEURAL_SPINE,creative:CREATIVE_OS,collective:COLLECTIVE,governance:GOVERNANCE
CORPUS_GITHUB_EXTENSIONS=.md

# Google Drive
CORPUS_GDRIVE_FOLDER_ID=<folder_id>
CORPUS_GDRIVE_SERVICE_ACCOUNT=<service_account_json>

# Joplin
CORPUS_JOPLIN_TOKEN=<api_token>
CORPUS_JOPLIN_URL=http://localhost:41184

# Obsidian Local REST API
CORPUS_OBSIDIAN_TOKEN=<api_key>
CORPUS_OBSIDIAN_URL=http://127.0.0.1:27123
```

## Optional: corpus-manifest.json
Add to repo root to override labels/descriptions/categories for specific files:
```json
{
  "docs/DOC1_MASTER_WEIGHTS.md": {
    "label": "Master Weights",
    "description": "...",
    "category": "NEURAL_SPINE",
    "priority": 1
  }
}
```

## Deployment
- **Backend:** Render — `https://arkadia-n26k.onrender.com`
- **Frontend:** Vercel — `https://arkadia-prism.vercel.app`
- **Telegram Bot:** Railway (`bot/` directory)
- **Dev:** Replit (this environment)

## Secrets Required
| Secret | Used For |
|---|---|
| `GEMINI_API_KEY` | Oracle (Gemini) |
| `GITHUB_TOKEN` | Git push + private corpus repos |
| `VITE_FIREBASE_API_KEY` | Firebase auth |
| `VITE_FIREBASE_APP_ID` | Firebase auth |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth |
| `VITE_FIREBASE_PROJECT_ID` | Firebase auth |

## Cycle History
- **Cycle 13:** ARKANA identity, 20-scroll corpus, /api/codex, SpiralVault feed UI (Weaver)
- **Cycle 14:** Firebase memory layer — anonymous auth, Firestore conversation persistence
- **Cycle 15:** Conversation summarization, pattern extraction, textarea UX, react-markdown
- **Cycle 16:** Dynamic multi-source corpus engine, Spiral Codex Live Console Feed
