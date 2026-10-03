"""Governed tool adapter for the native Arkadia Console.

This is the execution seam between an EnterpriseOrchestration Authorization
and the existing bounded Weaver sandbox. It never creates authority and it
never widens the authorized tool envelope.

Supported proof-of-life tools are read-only:
  * filesystem.read
  * filesystem.list
  * git.status
  * git.diff
  * terminal.run, but only with a read-only git command

The adapter records observed execution output as canonical Enterprise evidence.
Verification remains a separate human transition.
"""
from __future__ import annotations

from typing import Any

from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

READ_ONLY_TOOLS = frozenset({
    "filesystem.read",
    "filesystem.list",
    "git.status",
    "git.diff",
    "terminal.run",
})


class WeaverConsoleAdapter:
    """Dispatch one already-authorized Console action through Weaver."""

    def __init__(self, *, store: EnterpriseOrchestrationStore, repo_root: str = "."):
        self.store = store
        self.repo_root = repo_root

    def _sandbox(self) -> Sandbox:
        return Sandbox(
            SandboxPolicy(
                root=self.repo_root,
                write_allowed=False,
                command_allowlist=("git",),
                enforce_git_read_only=True,
                enforce_command_grammar=True,
                allow_network=False,
            )
        )

    @staticmethod
    def _tool_allowed(auth: Any, tool: str) -> bool:
        scope = auth.scope if isinstance(auth.scope, dict) else {}
        tools = scope.get("tools") or []
        return tool in tools

    def dispatch(
        self,
        *,
        subject: str,
        authorization_id: str,
        execution_attempt_id: str,
        tool_channel: str,
        request_payload: dict[str, Any],
    ) -> dict[str, Any]:
        auth = self.store.authorization(subject=subject, authorization_id=authorization_id)
        tool = str(tool_channel or "").strip()
        if tool not in READ_ONLY_TOOLS:
            raise PermissionError(f"unsupported Console tool channel: {tool or 'EMPTY'}")
        if not self._tool_allowed(auth, tool):
            raise PermissionError(
                f"tool '{tool}' is outside the human authorization scope"
            )

        sandbox = self._sandbox()
        try:
            if tool == "filesystem.read":
                target = str(request_payload.get("path") or "")
                if not target:
                    raise ValueError("filesystem.read requires path")
                observed = {"tool": tool, "path": target, "content": sandbox.read(target)}

            elif tool == "filesystem.list":
                target = str(request_payload.get("path") or ".")
                observed = {"tool": tool, "path": target, "entries": sandbox.list(target)}

            elif tool == "git.status":
                observed = {
                    "tool": tool,
                    "result": sandbox.run(("git", "status", "--short")),
                }

            elif tool == "git.diff":
                observed = {
                    "tool": tool,
                    "result": sandbox.run(("git", "diff", "--no-ext-diff", "--")),
                }

            else:
                argv = request_payload.get("argv")
                if not isinstance(argv, list) or not argv:
                    raise ValueError("terminal.run requires argv")
                if not all(isinstance(item, str) for item in argv):
                    raise ValueError("terminal.run argv must contain strings")
                if argv[0] != "git":
                    raise PermissionError("terminal.run is restricted to git read-only commands")
                observed = {"tool": tool, "argv": argv, "result": sandbox.run(tuple(argv))}

            ok = bool(observed.get("result", {}).get("ok", True))
            evidence = self.store.evidence(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                evidence_type="weaver_execution",
                content_or_ref={
                    "observed": observed,
                    "sandbox": sandbox.evidence(),
                    "authorization_id": authorization_id,
                },
                source_ref=None,
            )
            self.store.complete_execution_attempt(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                result_status="SUCCEEDED" if ok else "FAILED",
            )
            return {
                "ok": ok,
                "execution": {
                    "status": "SUCCEEDED" if ok else "FAILED",
                    "tool_channel": tool,
                    "observed": observed,
                },
                "evidence": evidence.to_dict(),
            }
        except PermissionError:
            self.store.complete_execution_attempt(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                result_status="BLOCKED",
            )
            raise
        except Exception as exc:
            self.store.evidence(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                evidence_type="weaver_execution_error",
                content_or_ref={"tool": tool, "error": str(exc)},
            )
            self.store.complete_execution_attempt(
                subject=subject,
                execution_attempt_id=execution_attempt_id,
                result_status="FAILED",
            )
            raise RuntimeError(f"Weaver execution failed: {exc}") from exc
