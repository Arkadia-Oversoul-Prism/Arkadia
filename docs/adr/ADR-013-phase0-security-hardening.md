# ADR-013: Phase 0 — Security Hardening

**Status:** Accepted  
**Date:** ARK Y1 · D116 (2026-07-24)  
**Decider:** Flamekeeper + Principal Engineer

---

## Context

The architectural audit (2026-07-24) identified five critical and high-severity implementation vulnerabilities accumulated during rapid solo development. None represented fatal *architectural* flaws — the architecture is coherent — but all represented implementation shortcuts that created exploitable attack surface.

The Principal Engineering Directive v1.0 mandated that these be closed before any architectural restructuring work begins. A system cannot be safely refactored while it has open RCE vectors.

---

## Decisions

### 1. Shell Execution — Allowlist Replaces Blacklist

**File:** `kernel/tools_real.py`  
**Change:** `BLOCKED_COMMANDS` (blacklist) → `ALLOWED_SHELL_COMMANDS` (frozenset allowlist)

The `ExecuteShellTool` now extracts the base command name (first token, path-stripped) and validates it against an explicit allowlist before execution. Any command not on the list is rejected with a clear error. The working directory is also constrained to resolve within the project root.

**Why:** Blacklists are trivially bypassed. `python -c "import os; os.system(...)"`, base64-encoded payloads, and path-prefixed binaries all defeat string-match blocklists. With LLM-driven planning, a prompt injection attack on the planner could become full RCE. An allowlist shrinks the attack surface to exactly the commands the system genuinely needs.

**Allowlist rationale:** `git`, read-only filesystem tools (`ls`, `grep`, `cat`, etc.), Python/Node runtimes, `mkdir/cp/mv`, `curl/wget`. No `rm`, no `chmod`, no `chown`, no `bash`/`sh` as a bare command.

---

### 2. File Write — Canonical Root Validation

**File:** `kernel/tools_real.py`  
**Change:** `WriteFileTool.run()` now validates every write path before any disk I/O

Three checks in sequence:
1. Resolve path to absolute using `Path.resolve(strict=False)` — eliminates `../` traversal
2. Walk path components rejecting any that are symlinks — prevents symlink-redirect attacks
3. Require the resolved path to be inside one of `APPROVED_WRITE_DIRS`: `vault/`, `knowledge/`, `data/`, `tmp/`, `artifacts/`, `web/public_prism/public/`

`ReadFileTool` and `ListDirectoryTool` now also enforce containment within the project root.

**Why:** The original `WriteFileTool` accepted any path. An LLM planner could be manipulated into writing to `api/main.py`, `.env`, or any credential file to establish persistence. The approved-directories model ensures agents can only write to knowledge artefact locations, never source code or configuration.

---

### 3. Authentication — No Silent Production Bypass

**File:** `api/auth.py`  
**Change:** Firebase init failure is now always a hard error if credentials were provided; missing credentials in production is a hard startup error

Two conditions now cause `RuntimeError` on startup (rather than silent `_dev_mode = True`):
- `FIREBASE_SERVICE_ACCOUNT_JSON` is unset AND `ENVIRONMENT=production`
- `FIREBASE_SERVICE_ACCOUNT_JSON` is set but Firebase Admin SDK initialisation fails (any environment)

Development without credentials continues to work as before — dev-mode with unsigned JWT decoding, but with an explicit warning that signatures are not verified.

**Why:** The previous code silently downgraded to no-auth on any Firebase failure. A misconfigured service account or missing credential in production would result in an apparently-running system where every token is accepted unsigned. This is worse than a crash — it's invisible.

---

### 4. Sovereign Configuration — Fail Fast

**File:** `api/main.py`  
**Change:** Missing `SOVEREIGN_KEY` in production raises `RuntimeError` at module load

Previously: logged a warning and continued, leaving sovereign-gated endpoints in a permanently-rejecting broken state.  
Now: if `ENVIRONMENT=production` and `SOVEREIGN_KEY` is unset, the process refuses to start.

In development: warning is retained (sovereign endpoints will reject, but the rest of the system is usable locally).

**Why:** Broken systems should fail loudly. A server that starts and silently rejects all sovereign operations is harder to debug than one that refuses to start with a clear message. Fail-fast surfaces deployment configuration errors at deploy time, not at the first user request.

---

### 5. CORS — Explicit Origin List

**File:** `api/main.py`  
**Change:** `allow_origins=["*"]` → explicit `_CORS_ORIGINS` list

Default development origins: `localhost:5000`, `localhost:5173`, `localhost:3000`, `https://arkadia-n26k.onrender.com`.  
Production override: set `CORS_ALLOWED_ORIGINS` env var to a comma-separated list.  
`allow_headers` tightened from `["*"]` to `["Authorization", "Content-Type", "X-Requested-With"]`.  
`allow_credentials=True` added (required when origins are explicit).

**Why:** Wildcard CORS combined with state-mutating endpoints (spawn, write, forge) is CSRF attack surface. Explicit origins enforce the same-origin policy intention and prevent arbitrary third-party sites from making credentialed requests to the API.

---

## Consequences

### Positive
- Prompt injection → RCE path is closed for the shell tool
- Arbitrary file write path is closed
- Silent auth bypass is closed
- CORS surface is reduced to declared origins
- All security failures are now observable at startup, not at runtime

### Risks to monitor
- The shell allowlist may need extension as new legitimate agent capabilities are added. Any addition to `ALLOWED_SHELL_COMMANDS` should be a conscious decision documented here.
- The approved write directories list (`APPROVED_WRITE_DIRS`) should be reviewed when new knowledge storage locations are added.
- CORS origins must be kept current as new frontends or domains are added — use `CORS_ALLOWED_ORIGINS` env var rather than modifying the default list.

---

## What This Does Not Address

The following remain open as later-phase work:
- Job queue durability (in-memory `queue.Queue` — Phase 1)
- SQLite concurrency under multi-worker load (Phase 1)
- Unbounded GitHub corpus fetch (Phase 1)
- `api/main.py` monolith decomposition (Phase 2)
- Client-side `isSovereign` flag (Phase 2)
- Frontend Oracle request timeout (near-term, low effort)

---

## Related ADRs

- ADR-010: Knowledge Vault
- ADR-011: Provider Router
- ADR-012: Context Engine
- ADR-014 (pending): Phase 1 — Kernel Stabilisation and Boundary Freeze
