"""EL-01 — bounded sandbox execution boundary.

The sandbox is where the Engineering Lab's *hands* live. It gives a bounded
agent run filesystem, terminal, and git access — but only inside a workspace
root, only under an explicit policy, and always fail-closed.

Canonical principle (directive section 2): execution occurs through bounded
runtime boundaries. The sandbox is that boundary. It does not hold authority:
it enforces the envelope the governance plane handed it.

Design invariants:

  * Default policy is READ-ONLY (``write_allowed=False``).
  * Path access is confined to ``policy.root`` after ``resolve()``; symlink or
    ``..`` escapes raise :class:`SandboxEscape`.
  * Writes additionally require an allow-list match and honour a forbidden list.
  * Terminal commands run with ``shell=False``, a sanitised environment (no
    ambient secrets), a timeout, and bounded output.
  * Every operation is recorded as a :class:`SandboxEvent` for evidence.
  * Remote git requires an explicit network policy; otherwise it is refused.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .contracts import utc_now

#: Environment variables that must never reach a sandboxed process.
_SECRET_ENV_MARKERS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "API_KEY",
    "APIKEY",
    "PRIVATE",
    "CREDENTIAL",
)


class SandboxError(RuntimeError):
    """Base class for sandbox refusals. The sandbox fails closed."""


class SandboxEscape(SandboxError):
    """Raised when a path or cwd would leave the workspace root."""


class SandboxWriteDenied(SandboxError):
    """Raised when a write is not permitted by the active policy."""


class SandboxCommandDenied(SandboxError):
    """Raised when a command is not permitted by the active policy."""


@dataclass(frozen=True)
class SandboxPolicy:
    """The bounded envelope a sandboxed run may operate inside.

    ``root`` is resolved to an absolute path at construction. ``write_allowed``
    defaults to ``False`` — a run must be explicitly granted write capability.
    """

    root: str
    write_allowed: bool = False
    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    allow_network: bool = False
    command_allowlist: tuple[str, ...] = ()
    #: When True, a ``git`` command may only use read-only subcommands (GATE L1).
    #: An allow-listed binary does not by itself make a command safe: ``git``
    #: with ``commit``/``reset``/``checkout`` mutates the repository. This closes
    #: that path without weakening the binary allow-list.
    enforce_git_read_only: bool = False
    #: When True, only binaries in ``L1_TERMINAL_BINARIES`` may run, regardless
    #: of ``command_allowlist``. A caller-supplied allow-list must not be able to
    #: widen ``terminal.run`` into a mutation capability (e.g. ``python -c ...``).
    enforce_command_grammar: bool = False
    default_timeout: float = 30.0
    max_output_bytes: int = 200_000
    max_file_bytes: int = 2_000_000


#: The closed set of binaries the L1 terminal capability may execute. Every
#: member either takes no path argument (``echo``/``pwd``/``true``/``false``) or
#: is separately constrained (``git``). Nothing here can mutate the workspace.
L1_TERMINAL_BINARIES: frozenset[str] = frozenset({"git", "echo", "pwd", "true", "false"})


#: Git subcommands that only observe repository state. Anything else — by
#: default, not by enumeration — is treated as mutation and refused when
#: ``enforce_git_read_only`` is set.
READ_ONLY_GIT_SUBCOMMANDS: frozenset[str] = frozenset({
    "status", "diff", "log", "show", "rev-parse", "rev-list", "ls-files",
    "ls-tree", "describe", "blame", "shortlog", "whatchanged", "grep",
    "cat-file", "name-rev", "for-each-ref", "show-ref", "verify-commit",
    "verify-tag", "merge-base", "symbolic-ref", "var", "count-objects",
})

#: Git global options that take a following argument (e.g. ``-C <path>``).
_GIT_OPTIONS_WITH_ARG: frozenset[str] = frozenset({
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env",
})

#: The subset of those options that redirect git at a filesystem path outside
#: ``policy.root``. ``-c``/``--config-env`` are config overrides, not paths.
_GIT_PATH_OPTIONS: frozenset[str] = frozenset({"-C", "--git-dir", "--work-tree"})


@dataclass
class SandboxEvent:
    """A single observable sandbox operation (evidence substrate)."""

    operation: str
    target: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "target": self.target,
            "ok": self.ok,
            "detail": self.detail,
            "timestamp_utc": self.timestamp_utc,
        }


def _sanitised_env() -> dict[str, str]:
    """Return a minimal environment with secret-bearing variables removed."""
    env: dict[str, str] = {}
    git_path_overrides = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
        "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
    for key, value in os.environ.items():
        upper = key.upper()
        if upper in git_path_overrides or any(marker in upper for marker in _SECRET_ENV_MARKERS):
            continue
        env[key] = value
    # A bounded run never inherits a git credential helper configuration.
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    return env


def _git_path_redirect(argv: Sequence[str]) -> str:
    """Return a git path-redirection option if present, else ``""``.

    ``-C``, ``--git-dir``, ``--work-tree``, ``--namespace`` and ``--config-env``
    change where git operates. The sandbox's ``_resolve`` never sees them, so
    they would let a run read a repository outside ``policy.root``.
    """
    for token in argv[1:]:
        name = token.split("=", 1)[0]
        if token.startswith("-C") and token != "-C":
            return "-C"
        if name in _GIT_PATH_OPTIONS:
            return name
        if name in _GIT_OPTIONS_WITH_ARG:
            continue
        if token.startswith("-"):
            continue
        break
    return ""


def _git_subcommand(argv: Sequence[str]) -> str:
    """Extract the git subcommand, skipping global options and their arguments.

    ``git -c user.email=x commit`` must resolve to ``commit``, not ``-c``.
    """
    i = 1
    while i < len(argv):
        token = argv[i]
        if token in _GIT_OPTIONS_WITH_ARG:
            i += 2
            continue
        if token.startswith("--") and "=" in token:
            i += 1
            continue
        if token.startswith("--"):
            # e.g. --no-pager / --version: a global flag without an argument.
            i += 1
            continue
        if token.startswith("-"):
            # A short global flag (e.g. -P). Assume no argument.
            i += 1
            continue
        return token
    return ""


def _matches_any(rel: str, prefixes: Sequence[str]) -> bool:
    rel = rel.replace("\\", "/").lstrip("./")
    for prefix in prefixes:
        p = prefix.replace("\\", "/").lstrip("./")
        if rel == p or rel.startswith(p.rstrip("/") + "/"):
            return True
    return False


class Sandbox:
    """A bounded execution workspace.

    Construct with a :class:`SandboxPolicy`. The sandbox owns no authority; it
    enforces the envelope it is given and records every operation as evidence.
    """

    def __init__(self, policy: SandboxPolicy) -> None:
        self.policy = policy
        self.root = Path(policy.root).expanduser().resolve()
        self._events: list[SandboxEvent] = []
        if not self.root.exists():
            raise SandboxError(f"sandbox root does not exist: {self.root}")

    # -- introspection --------------------------------------------------------

    @property
    def events(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events]

    def _record(
        self, operation: str, target: str, ok: bool, detail: dict[str, Any] | None = None
    ) -> None:
        self._events.append(
            SandboxEvent(operation=operation, target=target, ok=ok, detail=detail or {})
        )

    # -- path confinement -----------------------------------------------------

    def _resolve(self, rel: str) -> Path:
        """Resolve *rel* inside the root, refusing any escape."""
        candidate = (self.root / rel).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:  # pragma: no cover - defensive
            self._record("resolve", rel, False, {"reason": "escape"})
            raise SandboxEscape(
                f"path '{rel}' resolves outside sandbox root"
            ) from exc
        return candidate

    def _check_write_allowed(self, rel: str) -> None:
        if not self.policy.write_allowed:
            raise SandboxWriteDenied(
                f"write to '{rel}' denied: sandbox policy is read-only"
            )
        if self.policy.forbidden_paths and _matches_any(rel, self.policy.forbidden_paths):
            raise SandboxWriteDenied(f"write to '{rel}' denied: forbidden path")
        if self.policy.allowed_paths and not _matches_any(rel, self.policy.allowed_paths):
            raise SandboxWriteDenied(
                f"write to '{rel}' denied: not in allow-list {self.policy.allowed_paths}"
            )

    # -- filesystem -----------------------------------------------------------

    def read(self, rel: str) -> str:
        path = self._resolve(rel)
        if not path.is_file():
            self._record("read", rel, False, {"reason": "not_a_file"})
            raise SandboxError(f"not a file: {rel}")
        if path.stat().st_size > self.policy.max_file_bytes:
            self._record("read", rel, False, {"reason": "too_large"})
            raise SandboxError(f"file exceeds sandbox max_file_bytes: {rel}")
        text = path.read_text(encoding="utf-8", errors="replace")
        self._record("read", rel, True, {"bytes": len(text)})
        return text

    def list(self, rel: str = ".") -> list[dict[str, Any]]:
        path = self._resolve(rel)
        if not path.is_dir():
            self._record("list", rel, False, {"reason": "not_a_dir"})
            raise SandboxError(f"not a directory: {rel}")
        entries: list[dict[str, Any]] = []
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            if child.name in {".git", "__pycache__", "node_modules"}:
                continue
            entries.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(self.root)),
                    "kind": "dir" if child.is_dir() else "file",
                }
            )
        self._record("list", rel, True, {"count": len(entries)})
        return entries

    def write(self, rel: str, content: str) -> dict[str, Any]:
        self._check_write_allowed(rel)
        path = self._resolve(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        existed = path.exists()
        path.write_text(content, encoding="utf-8")
        self._record(
            "write", rel, True, {"bytes": len(content), "existed": existed}
        )
        return {"path": rel, "bytes": len(content), "existed": existed}

    # -- terminal -------------------------------------------------------------

    def run(
        self, argv: Sequence[str], *, timeout: float | None = None, cwd: str = "."
    ) -> dict[str, Any]:
        """Run a bounded command inside the workspace.

        ``shell=False`` is mandatory. The binary must satisfy the command
        allow-list when one is configured.
        """
        if not argv:
            raise SandboxCommandDenied("empty command")
        binary = os.path.basename(argv[0])
        if self.policy.enforce_command_grammar and binary not in L1_TERMINAL_BINARIES:
            self._record("run", binary, False, {"reason": "binary_outside_l1_grammar"})
            raise SandboxCommandDenied(
                f"binary '{binary}' is not in the closed L1 terminal set "
                f"{sorted(L1_TERMINAL_BINARIES)}; a caller allow-list cannot widen "
                "the terminal into a mutation capability"
            )
        if self.policy.command_allowlist and binary not in self.policy.command_allowlist:
            self._record("run", binary, False, {"reason": "not_allowlisted"})
            raise SandboxCommandDenied(
                f"command '{binary}' not in allow-list {self.policy.command_allowlist}"
            )
        if self.policy.enforce_git_read_only and binary == "git":
            redirect = _git_path_redirect(argv)
            if redirect:
                self._record("run", "git " + redirect, False,
                             {"reason": "git_path_redirect_denied"})
                raise SandboxCommandDenied(
                    f"git path option '{redirect}' would escape the sandbox root; "
                    "workspace confinement forbids it"
                )
            subcommand = _git_subcommand(argv)
            if subcommand not in READ_ONLY_GIT_SUBCOMMANDS:
                self._record("run", "git " + subcommand, False,
                             {"reason": "git_mutation_denied"})
                raise SandboxCommandDenied(
                    f"git subcommand '{subcommand}' is not read-only; repository "
                    "mutation must cross the governed boundary (PassSpec -> K15 -> K3)"
                )
        workdir = self._resolve(cwd)
        timeout = timeout if timeout is not None else self.policy.default_timeout
        try:
            proc = subprocess.run(
                list(argv),
                cwd=str(workdir),
                env=_sanitised_env(),
                shell=False,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            self._record("run", binary, False, {"reason": "timeout", "timeout": timeout})
            return {
                "ok": False,
                "binary": binary,
                "reason": "timeout",
                "stdout": "",
                "stderr": "",
                "returncode": None,
            }
        except FileNotFoundError:
            self._record("run", binary, False, {"reason": "not_found"})
            return {
                "ok": False,
                "binary": binary,
                "reason": "not_found",
                "stdout": "",
                "stderr": "",
                "returncode": None,
            }

        limit = self.policy.max_output_bytes
        stdout = proc.stdout[:limit]
        stderr = proc.stderr[:limit]
        result = {
            "ok": proc.returncode == 0,
            "binary": binary,
            "argv": list(argv),
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": len(proc.stdout) > limit or len(proc.stderr) > limit,
        }
        self._record(
            "run",
            binary,
            proc.returncode == 0,
            {"returncode": proc.returncode, "truncated": result["truncated"]},
        )
        return result

    # -- git ------------------------------------------------------------------

    def git(self, args: Sequence[str], *, remote: bool = False, timeout: float | None = None) -> dict[str, Any]:
        """Run a bounded git command inside the workspace.

        ``remote=True`` (fetch/push/ls-remote) requires ``allow_network``.
        Merge, force-push, and direct pushes to main are forbidden outright.
        """
        argv = list(args)
        joined = " ".join(argv)
        if "merge" in argv or "--force" in argv or "-f" in argv or "push" in argv and "main" in argv:
            self._record("git", joined, False, {"reason": "forbidden_operation"})
            raise SandboxCommandDenied(f"forbidden git operation: {joined}")
        if remote and not self.policy.allow_network:
            self._record("git", joined, False, {"reason": "network_denied"})
            raise SandboxCommandDenied(
                "remote git requires an explicit network policy (allow_network=True)"
            )
        if remote:
            argv = ["git", "-c", "credential.helper=", *argv[1:]]
        else:
            argv = ["git", *argv]
        return self.run(argv, timeout=timeout)

    # -- evidence export ------------------------------------------------------

    def evidence(self) -> dict[str, Any]:
        """Return a truthful sandbox evidence summary."""
        return {
            "root": str(self.root),
            "policy": {
                "write_allowed": self.policy.write_allowed,
                "allow_network": self.policy.allow_network,
                "command_allowlist": list(self.policy.command_allowlist),
                "allowed_paths": list(self.policy.allowed_paths),
                "forbidden_paths": list(self.policy.forbidden_paths),
            },
            "operations": self.events,
            "operation_count": len(self._events),
        }
