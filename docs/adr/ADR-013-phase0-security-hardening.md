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

### 1. Shell Execution — Allowlist + Path-Separator Guard

**File:** `kernel/tools_real.py`  
**Change:** `BLOCKED_COMMANDS` (blacklist) → `ALLOWED_SHELL_COMMANDS` (frozenset allowlist) + two-stage guard in `_check_shell_command()`

`_check_shell_command()` now enforces two gates before any subprocess is created:

**Stage 1 — Path separator rejection:**  
If `args[0]` contains `/` or `\`, the command is immediately rejected. This closes the basename-aliasing bypass: an attacker cannot rename `python3` to `./ls` and invoke it, because path-prefixed tokens are refused before the allowlist is consulted.

**Stage 2 — Allowlist:**  
The bare command name must be in `ALLOWED_SHELL_COMMANDS`. Current allowlist:

```
ls, cat, head, tail, grep, wc, echo, pwd, date, uname, whoami, printenv, stat
curl, wget
mkdir
```

**Execution is always `subprocess.run(..., shell=False)`:**  
The command is parsed via `shlex.split()` into a token list. Shell metacharacters (`;`, `&&`, `|`, `$()`) have no effect inside `subprocess.run(shell=False)` — they become literal arguments.

**Intentionally excluded (with rationale):**
- `env` — execution trampoline: `env python3 -c ...` invokes `python3` regardless of allowlist
- `find` — `-exec`/`-execdir` flags allow arbitrary command execution
- `git` — hooks, `difftool`, `mergetool`, config-driven helpers allow arbitrary execution
- `python`, `python3`, `node` — script-file execution → arbitrary code
- `pip`, `pip3`, `npm` — install hooks → arbitrary code
- `cp`, `mv` — binary staging vectors: attacker copies `python3 → ./ls`, then invokes it as a bare name

**Why an allowlist, not a blacklist:** Blacklists are trivially bypassed via path prefixes, base64-encoded payloads, renamed binaries, and command aliases. Any allowlist bypass closes the entire class of bypass, not just the specific instance. With LLM-driven planning, a prompt injection on the planner could become full RCE if the shell tool is insufficiently constrained.

**Adding to the allowlist:** Any addition to `ALLOWED_SHELL_COMMANDS` must be a conscious decision documented in an ADR update. Evaluation criteria: does the command have a secondary execution path (trampoline, `-exec` flag, hook system, config-driven helper)?

---

### 2. File Write — Canonical Root Validation + O_NOFOLLOW

**File:** `kernel/tools_real.py`  
**Change:** `WriteFileTool.run()` validates every write path before any disk I/O, then writes atomically via `os.open(O_NOFOLLOW)`

Four checks in sequence (`_validate_write_path()`):
1. Walk the **original** (pre-resolution) path components rejecting any that are symlinks — catches symlink redirects before `resolve()` follows them
2. Resolve to absolute (`Path.resolve(strict=False)`) — eliminates `../` traversal
3. Re-walk resolved components rejecting any new symlinks (TOCTOU mitigation between steps 1 and 2)
4. Require the resolved path to be inside `APPROVED_WRITE_DIRS`: `vault/`, `knowledge/`, `data/`, `tmp/`, `artifacts/`, `web/public_prism/public/`

**Write is via `os.open(..., O_NOFOLLOW)`:**  
Even if a symlink is created between `resolve()` and the write, the OS rejects the `open()` call with `ELOOP`, which is caught and returned as an error. This is a kernel guarantee, not a Python race.

`ReadFileTool` and `ListDirectoryTool` enforce containment within the project root.

**Why:** The original `WriteFileTool` accepted any path. An LLM planner could be manipulated into writing to `api/main.py`, `.env`, or any credential file. The approved-directories model ensures agents can only write to knowledge artefact locations.

---

### 3. Authentication — No Silent Production Bypass

**File:** `api/auth.py`  
**Change:** Firebase init failure is now always a hard error if credentials were provided; missing credentials in production is a hard startup error

Two conditions now cause `RuntimeError` on startup:
- `FIREBASE_SERVICE_ACCOUNT_JSON` is unset AND `ENVIRONMENT=production`
- `FIREBASE_SERVICE_ACCOUNT_JSON` is set but Firebase Admin SDK initialisation fails (any environment)

The import guard in `api/main.py` re-raises any `RuntimeError` from `api/auth.py` in production, so a misconfigured auth module cannot silently disable authentication at startup.

Development without credentials continues to work — dev-mode with unsigned JWT decoding, with an explicit warning that signatures are not verified.

**Why:** The previous code silently downgraded to no-auth on any Firebase failure. A misconfigured service account in production would result in an apparently-running system where every token is accepted unsigned. This is worse than a crash — it's invisible.

---

### 4. Sovereign Configuration — Fail Fast

**File:** `api/main.py`  
**Change:** Missing `SOVEREIGN_KEY` in production raises `RuntimeError` at module load

Previously: logged a warning and continued, leaving sovereign-gated endpoints in a permanently-rejecting broken state.  
Now: if `ENVIRONMENT=production` and `SOVEREIGN_KEY` is unset, the process refuses to start.

In development: warning is retained (sovereign endpoints will reject, but the rest of the system is usable locally).

**Why:** Broken systems should fail loudly. A server that starts and silently rejects all sovereign operations is harder to debug than one that refuses to start with a clear message.

---

### 5. CORS — Explicit Origin List, Production-Locked Default

**File:** `api/main.py`  
**Change:** `allow_origins=["*"]` → explicit `_CORS_ORIGINS` list; production default excludes localhost

When `CORS_ALLOWED_ORIGINS` is not set:
- **Development:** `localhost:5000`, `localhost:5173`, `localhost:3000`, `https://arkadia-n26k.onrender.com`
- **Production (`ENVIRONMENT=production`):** `https://arkadia-n26k.onrender.com` only — no localhost

`allow_headers` tightened from `["*"]` to `["Authorization", "Content-Type", "X-Requested-With"]`.  
`allow_credentials=True` added (required when origins are explicit).

**Why:** Wildcard CORS combined with state-mutating endpoints (spawn, write, forge) is CSRF attack surface. Explicit origins enforce the same-origin policy intention and prevent arbitrary third-party sites from making credentialed requests to the API. Production localhost leakage would also allow a compromised developer machine to call the production API from a browser.

---

## Consequences

### Positive
- Prompt injection → RCE path via shell tool is closed (allowlist + path-separator guard + no trampolines + shell=False)
- Arbitrary file write path is closed (path validation + O_NOFOLLOW)
- Silent auth bypass is closed (fail-fast on misconfigured or missing credentials in production)
- CORS surface is reduced to declared origins; production is locked to Render URL
- All security failures are observable at startup, not silently at runtime

### Risks to monitor
- The shell allowlist may need extension as new legitimate agent capabilities are added. Any addition to `ALLOWED_SHELL_COMMANDS` requires conscious review — see evaluation criteria in Decision 1.
- The approved write directories list (`APPROVED_WRITE_DIRS`) should be reviewed when new knowledge storage locations are added.
- CORS origins must be kept current as new frontends or domains are added — use `CORS_ALLOWED_ORIGINS` env var rather than modifying the default list.
- `curl`/`wget` in the shell allowlist can fetch arbitrary data over the network (SSRF risk). This is an accepted residual risk given the `requires_approval = True` gate on `ExecuteShellTool`. If automated agent pipelines are introduced (no human in the loop), reconsider.

---

## What This Does Not Address

The following remain open as later-phase work:
- Job queue durability (in-memory `queue.Queue` — Phase 1)
- SQLite concurrency under multi-worker load (Phase 1)
- Unbounded GitHub corpus fetch (Phase 1)
- `api/main.py` monolith decomposition (Phase 2)
- Client-side `isSovereign` flag (Phase 2)
- Frontend Oracle request timeout (near-term, low effort)
- `curl`/`wget` SSRF exposure in automated (no-approval) agent pipelines (if introduced)

---

## Related ADRs

- ADR-010: Knowledge Vault
- ADR-011: Provider Router
- ADR-012: Context Engine
- ADR-014 (pending): Phase 1 — Kernel Stabilisation and Boundary Freeze
