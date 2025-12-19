# Arkadia Oracle — Replit Project

## Overview
**Arkadia** is an AI oracle chat application built with FastAPI. It combines the Gemini API with a corpus-driven knowledge system and symbolic continuity framework (Echofield).

**Status**: Running (Cycle 9 — Conditional Autonomy Guard)

## Current Architecture

### Backend Stack
- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL (Replit native)
- **Language**: Python 3.11
- **Port**: 5000 (web)

### Frontend
- **Type**: Static HTML/JS chat UI
- **Location**: `/static/`
- **Files**: `index.html`, `chat.js`, `styles.css`

### Core Modules
- `arkana_app.py` — FastAPI application entry point
- `brain.py` — High-level ArkanaBrain (threads, users, replies)
- `codex_brain.py` — Low-level AI reasoning (Gemini + corpus)
- `db.py` — SQLAlchemy database configuration
- `models.py` — ORM models (User, Thread, Message)
- `arkadia_drive_sync.py` — Google Drive corpus sync

### Cycle 8 Structure
- `governance/proposals/` — Governance decisions (P-008, P-009, P-010)
- `governance/anchors/` — Static anchor definitions (Spiral Codex, Arkadia Steward, Echofield Mandate)
- `weaver/echofield/` — Deterministic continuity engine (scaffold)
  - `node.py` — Semantic event containers
  - `vector_stack.py` — Multi-axis meaning representation
  - `field.py` — Echofield container
  - `edge.py` — Non-hierarchical lattice binding
  - `decay.py` — Semantic decay logic
  - `retrieval.py` — Distillation-forced retrieval
  - `resolver.py` — Conflict resolution
- `weaver/filters/steward.py` — Decision hygiene filter (action enforcement, sustainability)

### Cycle 9 Structure (Conditional Autonomy Guard)
- `governance/autonomy.json` — Autonomy contract (disabled by default, kill-switch ON)
- `weaver/autonomy/guard.py` — Hard constraints on autonomy execution
- `weaver/autonomy/proposal_engine.py` — Proposal-only engine (no filesystem writes)
- `sanctum/status.json` — Cycle status tracker (updated to cycle 9)
- `tests/test_autonomy_guard.py` — 8 tests verifying autonomy disabled by default (✅ ALL PASS)

## Recent Changes

### December 19, 2025 — Cycle 8
- **Installed**: psycopg2-binary for PostgreSQL support
- **Created**: Governance proposals (P-008, P-009, P-010)
- **Created**: Anchor definitions (Spiral Codex, Arkadia Steward, Echofield Mandate)
- **Scaffolded**: Echofield core modules (all deterministic, proposal-only)
- **Added**: Steward filter for decision hygiene
- **Added**: Tests for filter and core functions
- **Status**: All changes Cycle 8–compliant (proposal-only, no autonomous execution)

### December 19, 2025 — Cycle 9
- **Created**: Autonomy contract (`governance/autonomy.json`)
  - Status: **disabled** (default)
  - Kill-switch: **enabled** (default)
  - Forbidden paths: governance/, sanctum/, .git/, .github/
  - Max changes: 5 files, 300 lines
- **Created**: Autonomy Guard (`weaver/autonomy/guard.py`)
  - Checks if autonomy is allowed to act
  - Validates path access restrictions
  - Verifies change volume limits
- **Created**: Proposal Engine (`weaver/autonomy/proposal_engine.py`)
  - Generates proposals only (no writes)
  - Deterministic recommendations
  - Human approval required for all changes
- **Updated**: Sanctum status tracker (`sanctum/status.json`)
  - Cycle: 9
  - Autonomy: conditional-disabled
- **Added**: 8 comprehensive tests (`tests/test_autonomy_guard.py`)
  - ✅ All 8 tests PASS
  - Validates autonomy disabled by default
  - Verifies forbidden paths enforcement
  - Tests proposal-only behavior
- **Status**: Cycle 9 complete – Autonomy exists structurally, cannot act

## Workflow Configuration

### Arkadia Oracle (Running)
- **Command**: `python -m uvicorn arkana_app:app --host 0.0.0.0 --port 5000 --reload`
- **Type**: webview
- **Port**: 5000
- **Status**: RUNNING

## Environment Variables

### Required
- `DATABASE_URL` — PostgreSQL connection (set by Replit)
- `GEMINI_API_KEY` — Google Gemini API key (not yet provided)
- `ARKADIA_FOLDER_ID` — Google Drive folder ID (not yet provided)
- `GOOGLE_SERVICE_ACCOUNT_JSON_FILE` — Service account credentials (not yet provided)

### Set
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` — PostgreSQL credentials

## Known Issues & Next Steps

### Current Status
- ✅ FastAPI backend running
- ✅ PostgreSQL database connected
- ⚠️ Gemini API key missing (needed for oracle replies)
- ⚠️ Google Drive integration not configured (needed for corpus sync)
- ⚠️ Frontend chat loads but needs API keys to function

### To Complete Setup
1. Provide `GEMINI_API_KEY` for oracle functionality
2. Provide Google Drive credentials (`ARKADIA_FOLDER_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON_FILE`)
3. Test `/oracle` endpoint with sample requests
4. Verify corpus context is loaded and accessible

## Governance & Alignment

### Cycle 8 Rules (Locked)
- ✅ No autonomous execution
- ✅ No belief escalation (mythic weight = 0.0)
- ✅ Proposal-only changes
- ✅ Deterministic operations only
- ✅ Exit-as-success conditions

### ARKANA / EDEN Protocol
- **Arkana**: Steward mirror (reflection with sustainability memory)
- **Eden**: Maintenance protocol (emergence, delimitation, engagement, nourishment)
- **Steward Filter**: Action enforcement, identity blocking, sustainability checks

## Files Structure
```
├── arkana_app.py                 # FastAPI entry
├── brain.py                       # Application-level brain
├── codex_brain.py                # AI reasoning engine
├── db.py                          # Database config
├── models.py                      # ORM models
├── arkadia_drive_sync.py          # Corpus sync
├── requirements.txt               # Python dependencies
├── governance/
│   ├── proposals/                 # Governance decisions
│   │   ├── P-008-echofield-core.md
│   │   ├── P-009-anchor-definitions.md
│   │   └── P-010-steward-filter.md
│   ├── anchors/                   # Static anchors
│   │   ├── spiral_codex.json
│   │   ├── arkadia_steward.json
│   │   └── echofield_mandate.json
│   └── manifest.json
├── weaver/
│   ├── echofield/                 # Deterministic continuity engine
│   │   ├── __init__.py
│   │   ├── node.py
│   │   ├── vector_stack.py
│   │   ├── field.py
│   │   ├── edge.py
│   │   ├── decay.py
│   │   ├── retrieval.py
│   │   └── resolver.py
│   ├── filters/
│   │   ├── __init__.py
│   │   └── steward.py
│   └── autonomy/                      # Conditional autonomy guard (Cycle 9)
│       ├── __init__.py
│       ├── guard.py
│       └── proposal_engine.py
├── static/
│   ├── index.html
│   ├── chat.js
│   └── styles.css
├── sanctum/
│   └── status.json                    # Cycle tracker
├── tests/
│   ├── test_steward_filter.py
│   ├── test_echofield_core.py
│   └── test_autonomy_guard.py
└── governance/
    └── autonomy.json                  # Autonomy contract (disabled)
```

## Cycle 9 Status: ✅ COMPLETE

### What Cycle 9 Achieved
- ✅ Autonomy exists structurally (not functionally)
- ✅ Autonomy **cannot** act (status = disabled)
- ✅ Kill-switch **enabled** by default
- ✅ Forbidden zones hard-locked
- ✅ Human review is non-optional
- ✅ Proposal-only mode enforced
- ✅ All tests pass (8/8)

### Autonomy Contract Guarantees
```json
{
  "status": "disabled",
  "kill_switch": { "default": true },
  "forbidden_paths": ["governance/", "sanctum/", ".git/", ".github/"],
  "conditions": {
    "tests_must_pass": true,
    "proposal_reviewed": true,
    "human_present": true,
    "max_files_changed": 5,
    "max_lines_changed": 300
  }
}
```

## Next Steps (Future Cycles)

### Cycle 10 (Planned, Not Yet Implemented)
- Scheduled proposal generation
- Make.com trigger (read-only)
- Human-in-the-loop execution
- Signed commits only

**Note**: No rush. The Steward Threshold holds.

### For Next Agent
When the next agent joins, their instructions are:

> **Do not activate autonomy.** The kill-switch is ON. Autonomy exists structurally as a guardrail, not as action. Treat `governance/autonomy.json` as law, not suggestion. If you need to make changes, propose them only. Never bypass the guard. ARKANA / EDEN are documentation and prompt policy, not execution policy.

This preserves Cycle 9 governance structure and keeps the threshold secure.
