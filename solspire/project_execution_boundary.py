"""Fail-closed container boundary for project-scoped agent work.

This module builds a hardened OCI-container invocation for a disposable project
copy. Agent edit proposals do not mutate that copy or the canonical project store.
Canonical persistence is a separate, explicitly authorized patch-application step.

The host must provide a trusted Docker-compatible runtime. This module does not
claim that a container is a VM or a complete defense against a compromised host.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from typing import Sequence


class BoundaryError(RuntimeError):
    """Execution cannot proceed without violating a boundary invariant."""


def safe_relative_path(value: str) -> str:
    """Return a normalized relative path or reject traversal/absolute paths."""
    raw = (value or "").replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise BoundaryError("path must be a normalized relative path")
    if any(":" in part or "\x00" in part for part in path.parts):
        raise BoundaryError("path contains a forbidden component")
    return path.as_posix()


def build_container_argv(
    *,
    image: str,
    workspace: str | Path,
    command: Sequence[str],
    runtime: str = "docker",
    memory: str = "512m",
    cpus: str = "1.0",
    pids_limit: int = 128,
    working_directory: str = ".",
    execution_id: str | None = None,
) -> list[str]:
    """Build an OCI invocation with no network and a disposable workspace.

    `workspace` is the ephemeral copy, never the canonical project directory.
    Caller must prepare it from a trusted snapshot and validate its diff before
    any canonical-store write.
    """
    import re
    if not re.fullmatch(r".+@sha256:[0-9a-fA-F]{64}", image or ""):
        raise BoundaryError("container image must be pinned by immutable SHA-256 digest")
    if not command or any(not isinstance(arg, str) or "\x00" in arg for arg in command):
        raise BoundaryError("command must be a non-empty argv sequence")
    if pids_limit < 1:
        raise BoundaryError("pids_limit must be positive")
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise BoundaryError("workspace must resolve to a real directory")
    relative_workdir = safe_relative_path(working_directory) if working_directory != "." else "."
    target_workdir = root if relative_workdir == "." else (root / relative_workdir).resolve(strict=True)
    try:
        target_workdir.relative_to(root)
    except ValueError as exc:
        raise BoundaryError("working directory escapes workspace") from exc
    if not target_workdir.is_dir():
        raise BoundaryError("working directory must be a directory")
    container_workdir = "/workspace" if relative_workdir == "." else f"/workspace/{relative_workdir}"
    return [
        runtime, "run", "--rm", "--label", f"arkadia.solspire.execution-id={execution_id or uuid.uuid4().hex}",
        "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--pids-limit", str(pids_limit), "--memory", memory,
        "--cpus", cpus, "--user", "65532:65532",
        "--mount", f"type=bind,src={root},dst=/workspace",
        "--workdir", container_workdir, "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        image, *command,
    ]


def _container_runtime_available(executable: str, runtime: str) -> bool:
    """True when the runtime CLI can actually reach its daemon.

    `shutil.which` finds the client binary only. A host with the client installed
    but no running daemon (or no socket) fails later, inside the container call,
    as an opaque process error. Probing here lets callers skip instead.
    """
    probe = [executable, "info"] if runtime == "docker" else [executable, "version"]
    try:
        result = subprocess.run(
            probe, shell=False, check=False, capture_output=True, text=True,
            timeout=10, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                             "LANG": "C.UTF-8"},
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def run_isolated(
    *, image: str, workspace: str | Path, command: Sequence[str],
    timeout_seconds: int = 60, runtime: str = "docker",
    working_directory: str = ".",
) -> subprocess.CompletedProcess[str]:
    """Execute without a shell; fail closed when the container runtime is absent."""
    if timeout_seconds < 1 or timeout_seconds > 900:
        raise BoundaryError("timeout_seconds must be between 1 and 900")
    executable = shutil.which(runtime)
    if not executable:
        raise BoundaryError("container runtime unavailable; refusing host execution")
    if not _container_runtime_available(executable, runtime):
        raise BoundaryError("container runtime daemon unavailable; refusing host execution")
    execution_id = uuid.uuid4().hex
    argv = build_container_argv(
        image=image, workspace=workspace, command=command, runtime=executable,
        working_directory=working_directory, execution_id=execution_id,
    )
    try:
        return subprocess.run(
            argv, shell=False, check=False, capture_output=True, text=True,
            timeout=timeout_seconds, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                         "LANG": "C.UTF-8"},
        )
    except subprocess.TimeoutExpired as exc:
        # Killing the client process does not guarantee the container stopped.
        # Find only this invocation by its random label, then forcibly remove it.
        label = f"arkadia.solspire.execution-id={execution_id}"
        try:
            listed = subprocess.run(
                [executable, "ps", "-aq", "--filter", f"label={label}"],
                shell=False, capture_output=True, text=True, timeout=5, check=False,
            )
            for container_id in (listed.stdout or "").split():
                subprocess.run([executable, "rm", "-f", container_id], shell=False,
                               capture_output=True, text=True, timeout=5, check=False)
        except Exception:
            pass
        raise BoundaryError("isolated command timed out; container cleanup was attempted") from exc


def require_reviewed_patch(*, approved: bool, expected_base_digest: str,
                           observed_base_digest: str, changed_paths: Sequence[str],
                           allowed_paths: Sequence[str]) -> tuple[str, ...]:
    """Gate candidate changes before a separate canonical-store persistence step."""
    if not approved:
        raise BoundaryError("canonical persistence requires explicit human approval")
    if not expected_base_digest or expected_base_digest != observed_base_digest:
        raise BoundaryError("canonical base changed; review must be refreshed")
    allowed = {safe_relative_path(p) for p in allowed_paths}
    changed = tuple(safe_relative_path(p) for p in changed_paths)
    if not changed:
        raise BoundaryError("empty patch")
    if any(p not in allowed for p in changed):
        raise BoundaryError("patch contains paths outside the approved allowlist")
    return changed
