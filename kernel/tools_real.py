"""Phase A — Real executable tools for the Arkadia kernel.

Registers alongside the existing stub tools. Each tool follows the
BaseTool contract so the registry, planner, and worker need no changes.

Tools added here:
  execute_shell   — run bash commands in a sandboxed subprocess
  read_file       — read a file from the local filesystem
  write_file      — write / overwrite a file (approved directories only)
  list_directory  — list directory contents
  generate_image  — Gemini Imagen image generation (real)

Security model (Phase 0 hardening):
  • execute_shell: allowlist-only — only explicitly permitted base commands
    may execute. Shell=True is kept for argument passing but the base
    command is validated before execution. Prompt-injection cannot reach
    an un-listed binary.
  • write_file: canonical root validation — paths are resolved to absolute,
    checked for symlink components, and must fall inside APPROVED_WRITE_DIRS.
    Traversal sequences ("../") and symlinks are rejected before any disk I/O.
  • read_file: containment check — resolved path must remain inside the
    project root. Prevents reading /etc/passwd, private key files, etc.
"""
from __future__ import annotations

import logging
import os
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("arkadia.tools_real")

from kernel.tools import BaseTool, _envelope, register_tool

# ── Safety constants ─────────────────────────────────────────────────────────

_EXEC_TIMEOUT   = int(os.environ.get("TOOL_SHELL_TIMEOUT", "30"))
_FILE_SIZE_LIMIT = int(os.environ.get("TOOL_FILE_SIZE_BYTES", str(512 * 1024)))  # 512 KB
_WORKDIR        = Path(os.environ.get("TOOL_WORKDIR", os.getcwd())).resolve()

# ops that need user approval before running
SENSITIVE_OPS: set[str] = {"execute_shell", "write_file"}

# ── Shell execution: allowlist ────────────────────────────────────────────────
# Only the base command name (first token) is checked.
# Add to this set only when a new command is genuinely required AND safe.
# Never use a blocklist — blocklists are trivially bypassed.
#
# INTERPRETER EXCLUSION: python, python3, node, pip, npm are intentionally
# absent. Even with shell=False, `python3 script.py` permits arbitrary code
# execution if an attacker (via prompt injection) can first write a script
# to an approved directory. The kernel is itself a Python process — any
# Python logic needed by a tool should be implemented directly in Python,
# not by spawning a new interpreter. The same applies to Node and package
# managers (pip install and npm install run arbitrary hook scripts).

ALLOWED_SHELL_COMMANDS: frozenset[str] = frozenset({
    # Filesystem inspection — read-only, no execution or trampoline surfaces
    "ls", "cat", "head", "tail", "grep", "wc", "echo",
    "pwd", "date", "uname", "whoami", "printenv", "stat",
    # Network data fetching — cannot execute fetched content with shell=False
    "curl", "wget",
    # Directory creation only — no execution surface
    "mkdir",
    #
    # INTENTIONALLY EXCLUDED (with rationale):
    # - env: execution trampoline (env <cmd> ... invokes <cmd> directly)
    # - find: -exec/-execdir flags → arbitrary command execution
    # - git: hooks, difftool, mergetool, config-driven helpers → arbitrary execution
    # - python/python3/node: script-file execution → arbitrary code
    # - pip/pip3/npm: install hooks → arbitrary code
    # - cp, mv: binary staging vectors — attacker copies python3→ls, then runs ./ls
    #   ('cp' and 'mv' combined with basename aliasing bypass allowlist enforcement)
    #
    # If git or interpreter operations are needed by an agent capability,
    # implement them as dedicated Python tools with strict argument validation —
    # do not add them to this general shell allowlist.
})

def _check_shell_command(command: str) -> tuple[bool, str]:
    """
    Returns (allowed, rejection_reason).

    Two-stage check:
      1. Path separator rejection — bars './ls', '/bin/sh', '../python' and any
         other path-prefixed invocation that would bypass allowlist enforcement
         via basename aliasing (copy python3 → ./ls, then run it).
      2. Allowlist check — the first token must be a bare name present in
         ALLOWED_SHELL_COMMANDS.

    NOTE: shlex.split() is intentionally re-run inside run() so that the same
    token list drives both validation and subprocess.run(). This function is
    a fast pre-flight guard, NOT the final exec gate.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False, "Could not parse command (unmatched quotes?)"

    if not tokens:
        return False, "Empty command"

    cmd = tokens[0]

    # Stage 1 — reject path-prefixed commands
    if "/" in cmd or "\\" in cmd:
        return False, (
            f"Path-prefixed commands are not permitted: '{cmd}'. "
            "Use bare command names only (e.g. 'ls', not './ls' or '/bin/ls')."
        )

    # Stage 2 — allowlist
    if cmd not in ALLOWED_SHELL_COMMANDS:
        return False, (
            f"'{cmd}' is not in the shell execution allowlist. "
            f"Allowed base commands: {sorted(ALLOWED_SHELL_COMMANDS)}"
        )

    return True, ""


# ── File write: path validation ───────────────────────────────────────────────
# Writes are restricted to these subdirectories of the project root.
# Rationale: agents must never overwrite source code, configuration, or
# credentials. Knowledge artefacts live in vault/, knowledge/, and data/.

APPROVED_WRITE_DIRS: tuple[Path, ...] = tuple(
    _WORKDIR / d for d in (
        "vault",
        "knowledge",
        "data",
        "tmp",
        "artifacts",
        "web/public_prism/public",   # generated media only
    )
)


def _validate_write_path(path: Path) -> tuple[bool, str]:
    """
    Returns (allowed, rejection_reason).

    Checks performed (in order):
      1. Walk the ORIGINAL (pre-resolution) path components rejecting any that
         are already symlinks. This must happen before resolve() so that symlinks
         which redirect an in-bounds path to an out-of-bounds location are caught.
         (Checking only the resolved path would miss them — the resolved path
         would appear to be inside the approved dir even though it was reached
         via a symlink that escapes it.)
      2. Resolve to absolute (strict=False) to eliminate any '..' traversal.
      3. Re-check: reject any resolved component that is a symlink (TOCTOU
         mitigation — a symlink created between steps 1 and 3 is caught here).
      4. Require the resolved path to be inside an approved write directory.
    """
    # Step 1 — walk original path components for existing symlinks
    check = path
    while check != check.parent:
        if check.exists() and check.is_symlink():
            return False, f"Symlink detected in original path component: {check}"
        check = check.parent

    # Step 2 — resolve to eliminate '..' traversal
    try:
        resolved = path.resolve(strict=False)
    except Exception as exc:
        return False, f"Path resolution failed: {exc}"

    # Step 3 — re-check resolved components (TOCTOU mitigation)
    check = resolved
    while check != check.parent:
        if check.exists() and check.is_symlink():
            return False, f"Symlink detected in resolved path component: {check}"
        check = check.parent

    # Step 4 — containment inside approved directories
    for approved in APPROVED_WRITE_DIRS:
        approved_resolved = approved.resolve()
        try:
            resolved.relative_to(approved_resolved)
            return True, ""   # inside this approved dir — accept
        except ValueError:
            continue

    approved_labels = [str(d) for d in APPROVED_WRITE_DIRS]
    return False, (
        f"'{resolved}' is outside approved write directories. "
        f"Approved: {approved_labels}"
    )


def _validate_read_path(path: Path) -> tuple[bool, str]:
    """
    Returns (allowed, rejection_reason).
    Read paths must resolve inside the project root (no /etc/passwd etc.).
    """
    try:
        resolved = path.resolve(strict=False)
    except Exception as exc:
        return False, f"Path resolution failed: {exc}"

    try:
        resolved.relative_to(_WORKDIR)
        return True, ""
    except ValueError:
        return False, f"'{resolved}' is outside the project root '{_WORKDIR}'"


# ── execute_shell ────────────────────────────────────────────────────────────

class ExecuteShellTool(BaseTool):
    name = "execute_shell"
    description = (
        "Run a shell command and return stdout/stderr. "
        "Only commands from the explicit allowlist are permitted. "
        "Requires user approval."
    )
    payload_schema = {
        "command": "str — shell command to execute",
        "timeout": "int — seconds to wait (default 30)",
        "workdir": "str — working directory (default project root)",
    }
    requires_approval = True

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = (payload.get("command") or "").strip()
        if not command:
            return _envelope(self.name, payload, [{"status": "error", "error": "No command provided"}])

        allowed, reason = _check_shell_command(command)
        if not allowed:
            logger.warning("[shell] rejected command=%r reason=%s", command[:120], reason)
            return _envelope(self.name, payload, [{
                "status": "error",
                "error": f"Command not permitted: {reason}",
            }])

        # Parse into token list for subprocess. shlex.split() is the
        # injection boundary — shell metacharacters (;&&|) become literal
        # arguments when shell=False. ValueError on unmatched quotes.
        try:
            args = shlex.split(command)
        except ValueError as exc:
            return _envelope(self.name, payload, [{
                "status": "error",
                "error": f"Could not parse command (unmatched quotes?): {exc}",
            }])

        if not args:
            return _envelope(self.name, payload, [{"status": "error", "error": "Empty command after parsing"}])

        timeout = int(payload.get("timeout") or _EXEC_TIMEOUT)

        # workdir must stay inside the project root
        workdir_str = payload.get("workdir") or str(_WORKDIR)
        workdir = Path(workdir_str).resolve()
        try:
            workdir.relative_to(_WORKDIR)
        except ValueError:
            return _envelope(self.name, payload, [{
                "status": "error",
                "error": f"workdir '{workdir}' is outside the project root",
            }])

        try:
            result = subprocess.run(
                args,        # token list — shell metacharacters (;&&|) have no effect
                shell=False, # MUST be False: shell=True with an allowlist is still bypassable
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(workdir),
            )
            output = result.stdout or ""
            stderr = result.stderr or ""
            success = result.returncode == 0
            logger.info("[shell] cmd=%r rc=%d", command[:80], result.returncode)
            return _envelope(self.name, payload, [{
                "status": "success" if success else "error",
                "command": command,
                "exit_code": result.returncode,
                "stdout": output[:8000],
                "stderr": stderr[:2000],
            }])
        except subprocess.TimeoutExpired:
            return _envelope(self.name, payload, [{
                "status": "error",
                "error": f"Command timed out after {timeout}s",
                "command": command,
            }])
        except Exception as exc:
            logger.exception("[shell] unexpected error")
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])


# ── read_file ────────────────────────────────────────────────────────────────

class ReadFileTool(BaseTool):
    name = "read_file"
    description = (
        "Read a file from the filesystem and return its contents. "
        "Path must resolve inside the project root."
    )
    payload_schema = {
        "path": "str — absolute or relative file path",
        "encoding": "str — default utf-8",
    }
    requires_approval = False

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        path_str = (payload.get("path") or "").strip()
        if not path_str:
            return _envelope(self.name, payload, [{"status": "error", "error": "No path provided"}])

        path = Path(path_str)
        if not path.is_absolute():
            path = _WORKDIR / path

        allowed, reason = _validate_read_path(path)
        if not allowed:
            logger.warning("[read_file] rejected path=%r reason=%s", str(path), reason)
            return _envelope(self.name, payload, [{"status": "error", "error": f"Read not permitted: {reason}"}])

        if not path.exists():
            return _envelope(self.name, payload, [{"status": "error", "error": f"File not found: {path}"}])

        if path.stat().st_size > _FILE_SIZE_LIMIT:
            return _envelope(self.name, payload, [{"status": "error", "error": f"File too large (>{_FILE_SIZE_LIMIT} bytes)"}])

        encoding = payload.get("encoding") or "utf-8"
        try:
            content = path.read_text(encoding=encoding, errors="replace")
            return _envelope(self.name, payload, [{
                "status": "success",
                "path": str(path),
                "content": content,
                "lines": content.count("\n"),
            }])
        except Exception as exc:
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])


# ── write_file ───────────────────────────────────────────────────────────────

class WriteFileTool(BaseTool):
    name = "write_file"
    description = (
        "Write content to a file (creates or overwrites). Requires user approval. "
        "Writes are restricted to approved knowledge directories: "
        "vault/, knowledge/, data/, tmp/, artifacts/."
    )
    payload_schema = {
        "path": "str — file path to write (must be in an approved directory)",
        "content": "str — text content",
        "encoding": "str — default utf-8",
    }
    requires_approval = True

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        path_str = (payload.get("path") or "").strip()
        content = payload.get("content") or ""
        if not path_str:
            return _envelope(self.name, payload, [{"status": "error", "error": "No path provided"}])

        path = Path(path_str)
        if not path.is_absolute():
            path = _WORKDIR / path

        allowed, reason = _validate_write_path(path)
        if not allowed:
            logger.warning("[write_file] rejected path=%r reason=%s", str(path), reason)
            return _envelope(self.name, payload, [{
                "status": "error",
                "error": f"Write not permitted: {reason}",
            }])

        try:
            import errno as _errno
            encoding = payload.get("encoding") or "utf-8"

            # Write to the RESOLVED (canonical) path to eliminate the primary
            # TOCTOU window (path swapped between validation and write).
            canonical = path.resolve(strict=False)
            canonical.parent.mkdir(parents=True, exist_ok=True)

            # O_NOFOLLOW: if the final component of `canonical` is a symlink,
            # the OS rejects the open() call with ELOOP — closing the residual
            # TOCTOU window where a symlink is created between resolve() and
            # write_text(). This is a Linux/macOS kernel guarantee, not a Python
            # race. Falls back to ordinary open on platforms without O_NOFOLLOW.
            _nofollow = getattr(os, "O_NOFOLLOW", 0)
            _flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _nofollow

            fd = os.open(str(canonical), _flags, 0o644)
            try:
                fobj = os.fdopen(fd, "w", encoding=encoding)
            except Exception:
                os.close(fd)
                raise
            with fobj:
                fobj.write(content)

            logger.info("[write_file] wrote %d bytes to %s", len(content), canonical)
            return _envelope(self.name, payload, [{
                "status": "written",
                "path": str(canonical),
                "bytes_written": len(content.encode(encoding)),
            }])
        except OSError as exc:
            import errno as _errno
            if exc.errno in (_errno.ELOOP, _errno.EMLINK):
                logger.warning("[write_file] O_NOFOLLOW: symlink at write target %s", canonical)
                return _envelope(self.name, payload, [{
                    "status": "error",
                    "error": f"Write blocked: symlink detected at '{canonical}' at write time.",
                }])
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])
        except Exception as exc:
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])


# ── list_directory ───────────────────────────────────────────────────────────

class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and directories at a given path."
    payload_schema = {
        "path": "str — directory path (default: project root)",
        "recursive": "bool — default false",
    }
    requires_approval = False

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        path_str = (payload.get("path") or str(_WORKDIR)).strip()
        path = Path(path_str)
        if not path.is_absolute():
            path = _WORKDIR / path

        # Containment check
        allowed, reason = _validate_read_path(path)
        if not allowed:
            return _envelope(self.name, payload, [{"status": "error", "error": f"Read not permitted: {reason}"}])

        if not path.exists():
            return _envelope(self.name, payload, [{"status": "error", "error": f"Path not found: {path}"}])

        recursive = bool(payload.get("recursive", False))
        try:
            if recursive:
                entries = [str(p.relative_to(path)) for p in path.rglob("*") if not any(
                    part.startswith(".") or part == "node_modules" for part in p.parts
                )][:500]
            else:
                entries = sorted(
                    [f"{e.name}{'/' if e.is_dir() else ''}" for e in path.iterdir()]
                )
            return _envelope(self.name, payload, [{
                "status": "success",
                "path": str(path),
                "entries": entries,
                "count": len(entries),
            }])
        except Exception as exc:
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])


# ── generate_image (real) ────────────────────────────────────────────────────

class GenerateImageTool(BaseTool):
    name = "generate_image"
    description = (
        "Generate an image using the Gemini image generation API. "
        "Returns a base64 PNG or a URL if saved to disk."
    )
    payload_schema = {
        "prompt": "str — image description",
        "save_path": "str — optional file path to save the image",
        "model": "str — default 'imagen-3.0-generate-002'",
    }
    requires_approval = False

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        import base64
        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            return _envelope(self.name, payload, [{"status": "error", "error": "No prompt provided"}])

        api_key = _active_api_key()
        if not api_key:
            return _envelope(self.name, payload, [{"status": "error", "error": "No GOOGLE_API_KEY configured"}])

        model = payload.get("model") or "imagen-3.0-generate-002"
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
            resp = httpx.post(url, json={
                "instances": [{"prompt": prompt}],
                "parameters": {"sampleCount": 1},
            }, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            predictions = data.get("predictions", [])
            if not predictions:
                return _envelope(self.name, payload, [{"status": "error", "error": "No image returned from API"}])

            b64 = predictions[0].get("bytesBase64Encoded", "")
            result: dict[str, Any] = {"status": "success", "prompt": prompt, "model": model}

            save_path = payload.get("save_path")
            if save_path:
                p = Path(save_path)
                if not p.is_absolute():
                    p = _WORKDIR / p
                # Image saves are restricted to the same approved dirs as writes
                img_allowed, img_reason = _validate_write_path(p)
                if not img_allowed:
                    return _envelope(self.name, payload, [{"status": "error", "error": f"Save path not permitted: {img_reason}"}])
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(base64.b64decode(b64))
                result["saved_to"] = str(p)
            else:
                result["base64_png"] = b64[:200] + "…" if len(b64) > 200 else b64

            return _envelope(self.name, payload, [result])
        except Exception as exc:
            logger.exception("[generate_image] failed")
            return _envelope(self.name, payload, [{"status": "error", "error": str(exc)}])


# ── API key helper ───────────────────────────────────────────────────────────

def _active_api_key() -> str:
    """Return the currently active Gemini API key.
    Prefers the key manager store, falls back to env var.
    """
    try:
        from api.key_manager import get_active_key
        key = get_active_key()
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY", "")


# ── Auto-register all tools ──────────────────────────────────────────────────

def register_real_tools() -> None:
    for tool_cls in [
        ExecuteShellTool,
        ReadFileTool,
        WriteFileTool,
        ListDirectoryTool,
        GenerateImageTool,
    ]:
        register_tool(tool_cls())
        logger.info("[tools_real] registered: %s", tool_cls.name)
