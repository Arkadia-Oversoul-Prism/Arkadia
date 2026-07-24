---
name: Phase 0 Security Hardening
description: Durable rules and traps for Arkadia's shell tool, write-path, auth, and CORS closures.
---

## Durable rules

### Shell tool allowlist (kernel/tools_real.py)

**Rule:** `ALLOWED_SHELL_COMMANDS` is a frozenset. Any addition must pass the "execution surface" test: does the command have a trampoline, `-exec` flag, hook system, config-driven helper, or binary-staging capability?

**Current allowlist:** `ls, cat, head, tail, grep, wc, echo, pwd, date, uname, whoami, printenv, stat, curl, wget, mkdir`

**Two-stage guard in `_check_shell_command()`:**
- Stage 1: Reject `args[0]` if it contains `/` or `\` (path separator guard — closes basename aliasing)
- Stage 2: Reject if `args[0]` not in `ALLOWED_SHELL_COMMANDS`

**Path separator guard is non-negotiable.** Without it, an attacker can `cp python3 ./ls` then invoke `ls` — the allowlist sees bare name `ls` and allows it. Stage 1 must precede Stage 2 always.

**Commands that cannot return to the general allowlist (and why):**
- `env` — execution trampoline: `env python3 -c ...` invokes python3 regardless of allowlist
- `find` — `-exec`/`-execdir` flags → arbitrary command execution
- `git` — hooks, difftool, mergetool, config-driven external commands
- `python`, `python3`, `node` — script file execution
- `pip`, `pip3`, `npm` — install hooks → arbitrary code
- `cp`, `mv` — binary staging vectors (copy interpreter → allowlisted name, then invoke)

If git read operations (log, status, diff) are needed by an agent capability, implement as a dedicated Python tool with an explicit git-subcommand allowlist — never re-add `git` to the general shell allowlist.

**Evaluation checklist for any new allowlist entry:**
- Trampoline: does it invoke another program? (`env`, `xargs`, `tee` with `>()`)
- Flag-exec: does any flag execute a subprocess? (`find -exec`)
- Hook: does it run user-provided scripts on init? (`git` hooks, `npm` scripts)
- Staging enabler: does it let you copy a binary under an allowlisted name? (`cp`, `mv`)

### Write-path (kernel/tools_real.py WriteFileTool)

**Rule:** All writes go through `_validate_write_path()`: symlink walk on *original* path first, then resolve, then symlink re-check, then containment in `APPROVED_WRITE_DIRS`.

**O_NOFOLLOW on `os.open()`** is mandatory. It closes the residual TOCTOU window between `resolve()` and write — if a symlink is created in that gap, the OS raises `ELOOP` (caught and returned as error).

**Why both symlink walk AND O_NOFOLLOW:** walk catches symlinks that redirect in-bounds paths to out-of-bounds; O_NOFOLLOW catches symlinks created in the race window between validation and write. They close different time windows and are both required.

### Auth fail-fast (api/auth.py + api/main.py)

**Rule:** In production, Firebase credentials must be present and valid. Any failure raises `RuntimeError` at startup.

The import guard in `api/main.py` re-raises `RuntimeError` from `api.auth` in production, so misconfigured auth cannot silently disable authentication.

Dev mode: credentials absent → unsigned JWT decode with explicit warning. Credentials present but broken → `RuntimeError` always (any env).

### CORS production lock (api/main.py)

**Rule:** When `ENVIRONMENT=production` and `CORS_ALLOWED_ORIGINS` is unset, the only allowed origin is `https://arkadia-n26k.onrender.com`. Localhost never appears in production defaults.

Override via `CORS_ALLOWED_ORIGINS` env var (comma-separated). Do not hardcode new origins in the default list.

## Accepted residual risks

- `curl`/`wget` in the shell allowlist can be used for SSRF to internal network endpoints. Mitigated by `requires_approval = True` gate on `ExecuteShellTool`. If automated (no-human-approval) agent pipelines are introduced, reconsider removing these.
- `O_NOFOLLOW` unavailable on Windows (not an issue — Arkadia runs on Linux/Render). Code uses `getattr(os, 'O_NOFOLLOW', 0)` as a graceful fallback.

## Production deployment checklist

Set these env vars in Render before enabling `ENVIRONMENT=production`:
- `FIREBASE_SERVICE_ACCOUNT_JSON` (required)
- `SOVEREIGN_KEY` (required)
- `CORS_ALLOWED_ORIGINS` (recommended — defaults to Render URL if unset)

## ADR

Full rationale: `docs/adr/ADR-013-phase0-security-hardening.md`
