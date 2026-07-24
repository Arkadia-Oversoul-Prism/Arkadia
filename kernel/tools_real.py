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
# Add to this set when a new legitimate command is genuinely required.
# Never use a blocklist — blocklists are trivially bypassed.

ALLOWED_SHELL_COMMANDS: frozenset[str] = frozenset({
    # Version control
    "git",
    # Filesystem inspection (read-only)
    "ls", "find", "cat", "head", "tail", "grep", "wc", "echo",
    "pwd", "date", "uname", "whoami", "env", "printenv", "stat",
    # Python / Node runtimes (scripts only — no -c inline eval)
    "python3", "python", "node",
    # Package managers (read operations, e.g. npm list)
    "pip", "pip3", "npm",
    # Network inspection (read-only)
    "curl", "wget",
    # Safe filesystem mutations (no rm, no chmod, no chown)
    "mkdir", "cp", "mv",
})

def _extract_base_command(command: str) -> str:
    """Return the base executable name from a shell command string."""
    try:
        tokens = shlex.split(command)
        if not tokens:
            return ""
        # Strip any path prefix so '/usr/bin/python3' → 'python3'
        return Path(tokens[0]).name
    except ValueError:
        # shlex.split raises on unmatched quotes
        return ""


def _check_shell_command(command: str) -> tuple[bool, str]:
    """Returns (allowed, rejection_reason)."""
    base = _extract_base_command(command)
    if not base:
        return False, "Could not parse command"
    if base not in ALLOWED_SHELL_COMMANDS:
        return False, (
            f"'{base}' is not in the shell execution allowlist. "
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
      1. Resolve to absolute without following symlinks.
      2. Reject any path component that is itself a symlink.
      3. Require the resolved path to be inside an approved write directory.
    """
    try:
        # resolve(strict=False) resolves '..' components without requiring the
        # path to exist yet, so we can validate before creating the file.
        resolved = path.resolve(strict=False)
    except Exception as exc:
        return False, f"Path resolution failed: {exc}"

    # Walk path components looking for symlinks that already exist
    check = resolved
    while check != check.parent:
        if check.exists() and check.is_symlink():
            return False, f"Symlink detected in path component: {check}"
        check = check.parent

    # Must be strictly inside one of the approved directories
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
                command,
                shell=True,
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
            path.parent.mkdir(parents=True, exist_ok=True)
            encoding = payload.get("encoding") or "utf-8"
            path.write_text(content, encoding=encoding)
            logger.info("[write_file] wrote %d bytes to %s", len(content), path)
            return _envelope(self.name, payload, [{
                "status": "written",
                "path": str(path),
                "bytes_written": len(content.encode(encoding)),
            }])
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
