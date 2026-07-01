"""Phase A — Real executable tools for the Arkadia kernel.

Registers alongside the existing stub tools. Each tool follows the
BaseTool contract so the registry, planner, and worker need no changes.

Tools added here:
  execute_shell   — run bash commands in a sandboxed subprocess
  read_file       — read a file from the local filesystem
  write_file      — write / overwrite a file
  list_directory  — list directory contents
  generate_image  — Gemini Imagen image generation (real)
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

# ── Safety ──────────────────────────────────────────────────────────────────

BLOCKED_COMMANDS = {
    "rm -rf /", ":(){ :|:& };:", "dd if=/dev/zero",
    "mkfs", "shutdown", "reboot", "halt",
}

_EXEC_TIMEOUT = int(os.environ.get("TOOL_SHELL_TIMEOUT", "30"))
_FILE_SIZE_LIMIT = int(os.environ.get("TOOL_FILE_SIZE_BYTES", str(512 * 1024)))  # 512 KB
_WORKDIR = os.environ.get("TOOL_WORKDIR", os.getcwd())

# ops that need user approval before running
SENSITIVE_OPS: set[str] = {"execute_shell", "write_file"}


# ── execute_shell ────────────────────────────────────────────────────────────

class ExecuteShellTool(BaseTool):
    name = "execute_shell"
    description = (
        "Run a bash shell command and return stdout/stderr. "
        "Use for terminal tasks, running scripts, checking system state. "
        "Requires user approval for destructive commands."
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

        for blocked in BLOCKED_COMMANDS:
            if blocked in command:
                return _envelope(self.name, payload, [{
                    "status": "error",
                    "error": f"Blocked command pattern: '{blocked}'",
                }])

        timeout = int(payload.get("timeout") or _EXEC_TIMEOUT)
        workdir = payload.get("workdir") or _WORKDIR

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workdir,
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
    description = "Read a file from the filesystem and return its contents."
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
            path = Path(_WORKDIR) / path

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
    description = "Write content to a file (creates or overwrites). Requires user approval."
    payload_schema = {
        "path": "str — file path to write",
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
            path = Path(_WORKDIR) / path

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
        path_str = (payload.get("path") or _WORKDIR).strip()
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(_WORKDIR) / path

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
        import os, base64
        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            return _envelope(self.name, payload, [{"status": "error", "error": "No prompt provided"}])

        api_key = _active_api_key()
        if not api_key:
            return _envelope(self.name, payload, [{"status": "error", "error": "No GOOGLE_API_KEY configured"}])

        model = payload.get("model") or "imagen-3.0-generate-002"
        try:
            import httpx, json
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
