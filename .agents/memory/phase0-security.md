---
name: Phase 0 Security Hardening
description: Five security closures implemented before any Phase 1 architectural work. All production guards gated on ENVIRONMENT=production.
---

## Rules implemented

1. **Shell execution** (`kernel/tools_real.py`) — `ALLOWED_SHELL_COMMANDS` frozenset allowlist replaces blacklist. Base command name (first token, path-stripped) must be in the set. Workdir also constrained to project root.

2. **File write path validation** (`kernel/tools_real.py`) — `WriteFileTool`, `ReadFileTool`, `ListDirectoryTool` all validate paths before I/O. Write must resolve inside `APPROVED_WRITE_DIRS` (vault/, knowledge/, data/, tmp/, artifacts/, web/public_prism/public/). Symlink components rejected. Read/list must stay inside project root.

3. **Auth fail-fast** (`api/auth.py`) — `FIREBASE_SERVICE_ACCOUNT_JSON` present but init fails → always hard error (any env). Missing in production (`ENVIRONMENT=production`) → hard error. Missing in dev → warning + dev-mode (unsigned JWT).

4. **SOVEREIGN_KEY fail-fast** (`api/main.py`) — Missing in production → `RuntimeError` at module load. Missing in dev → warning only.

5. **CORS explicit origins** (`api/main.py`) — `allow_origins=["*"]` replaced with `_CORS_ORIGINS` list. Default covers localhost variants + Render URL. Override via `CORS_ALLOWED_ORIGINS` env var (comma-separated). `allow_headers` tightened from `*` to explicit set.

## Production deployment checklist

Set these env vars in Render before enabling `ENVIRONMENT=production`:
- `FIREBASE_SERVICE_ACCOUNT_JSON` (required)
- `SOVEREIGN_KEY` (required)
- `CORS_ALLOWED_ORIGINS` (recommended — defaults to Render URL if unset)

**Why:** All five guards are gated on `ENVIRONMENT=production` so Replit dev environment continues to work without credentials. Render must have `ENVIRONMENT=production` set for the guards to activate.

## ADR

Full rationale in `docs/adr/ADR-013-phase0-security-hardening.md`.
