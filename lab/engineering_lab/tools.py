"""GATE L1 — agent-facing tool layer over the bounded sandbox.

A tool is a *capability* the loop may invoke. It is never authorization
(``CAPABILITY != AUTHORIZATION``). Every tool here is read-only: filesystem
read/list, bounded terminal run, and read-only git. There is deliberately no
write, commit, push, or PR tool — consequential repository mutation must cross
the existing PassSpec -> K15 -> K3 governed boundary (GATE L2), never this layer.

The registry is the single extension point: adding ``browser.*`` later is a new
tool spec here, not a change to the AgentLoop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .sandbox import Sandbox, SandboxError


@dataclass(frozen=True)
class ToolSpec:
    """The declarative contract for one tool."""

    name: str
    kind: str
    description: str
    input_schema: dict[str, Any]
    requires: tuple[str, ...] = ()
    mutating: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "input_schema": self.input_schema,
            "requires": list(self.requires),
            "mutating": self.mutating,
        }


class ToolError(RuntimeError):
    """Raised when a tool call cannot be honoured (never silently swallowed)."""


def _specs() -> dict[str, ToolSpec]:
    return {
        "filesystem.list": ToolSpec(
            name="filesystem.list",
            kind="read",
            description="List entries in a workspace directory.",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        ),
        "filesystem.read": ToolSpec(
            name="filesystem.read",
            kind="read",
            description="Read a file inside the workspace.",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
        "terminal.run": ToolSpec(
            name="terminal.run",
            kind="run",
            description="Run a bounded, allow-listed command inside the workspace.",
            input_schema={
                "type": "object",
                "properties": {"argv": {"type": "array", "items": {"type": "string"}}},
                "required": ["argv"],
            },
            requires=("terminal",),
        ),
        "git.status": ToolSpec(
            name="git.status",
            kind="git_read",
            description="Read the workspace git status (no mutation).",
            input_schema={"type": "object", "properties": {}},
            requires=("git_read",),
        ),
        "git.diff": ToolSpec(
            name="git.diff",
            kind="git_read",
            description="Read the workspace git diff (no mutation).",
            input_schema={"type": "object", "properties": {}},
            requires=("git_read",),
        ),
    }


class ToolRegistry:
    """Maps agent-intended tool names onto sandbox primitives.

    Tool access is intersected with the agent's granted tool envelope: a tool the
    run was not granted is reported as ``denied``, not executed.
    """

    def __init__(self, sandbox: Sandbox, granted: tuple[str, ...] | None = None) -> None:
        self._sandbox = sandbox
        self._granted = set(granted) if granted is not None else None
        self._specs = _specs()

    def available(self) -> list[dict[str, Any]]:
        return [
            spec.to_dict()
            for name, spec in self._specs.items()
            if self._permitted(name)
        ]

    def _permitted(self, name: str) -> bool:
        if self._granted is None:
            return True
        return name in self._granted

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run one tool call and return a structured observation.

        Errors are returned as ``{"ok": False, "error": ...}`` so the loop can
        feed the failure back to the model rather than crashing the run.
        """
        spec = self._specs.get(name)
        if spec is None:
            return {"tool": name, "ok": False, "error": f"unknown tool '{name}'"}
        if spec.mutating:
            # Defensive: nothing mutating should ever be registered pre-GATE-L2.
            return {"tool": name, "ok": False, "error": "mutating tools are not available in L1"}
        if not self._permitted(name):
            return {"tool": name, "ok": False, "error": f"tool '{name}' not granted to this run"}

        try:
            if name == "filesystem.list":
                entries = self._sandbox.list(arguments.get("path") or ".")
                return {"tool": name, "ok": True, "entries": entries}
            if name == "filesystem.read":
                content = self._sandbox.read(arguments["path"])
                return {"tool": name, "ok": True, "content": content}
            if name == "terminal.run":
                argv = list(arguments.get("argv") or [])
                result = self._sandbox.run(argv)
                return {"tool": name, "ok": result.get("ok", False), **result}
            if name == "git.status":
                result = self._sandbox.git(["status", "--short"])
                return {"tool": name, "ok": result.get("ok", False), **result}
            if name == "git.diff":
                result = self._sandbox.git(["diff"])
                return {"tool": name, "ok": result.get("ok", False), **result}
        except SandboxError as exc:
            return {"tool": name, "ok": False, "error": str(exc)}
        except KeyError as exc:
            return {"tool": name, "ok": False, "error": f"missing argument: {exc}"}
        return {"tool": name, "ok": False, "error": f"unhandled tool '{name}'"}
