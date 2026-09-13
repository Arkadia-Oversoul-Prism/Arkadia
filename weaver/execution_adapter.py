"""Provider-neutral execution adapter interface.

Worker Contract is fixed; providers are replaceable.
Bootstrap uses NullExecutionAdapter (no mutation).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ExecutionRequest:
    move_id: str
    plan: dict[str, Any]
    dry_run: bool
    repo_root: str


@dataclass
class ExecutionResult:
    ok: bool
    message: str
    files_changed: list[str]
    provider: str


class ExecutionAdapter(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...


class NullExecutionAdapter:
    """Bootstrap adapter: refuses mutation; orientation only."""

    name = "null"

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.dry_run:
            return ExecutionResult(
                ok=True,
                message="dry-run: no mutation",
                files_changed=[],
                provider=self.name,
            )
        return ExecutionResult(
            ok=False,
            message="NullExecutionAdapter refuses live execution; configure an approved provider",
            files_changed=[],
            provider=self.name,
        )


class ForbiddenMergeAdapter:
    """Sentinel: merge/deploy always refused."""

    def merge(self, *_a: Any, **_k: Any) -> None:
        raise RuntimeError("merge is human-only")

    def deploy(self, *_a: Any, **_k: Any) -> None:
        raise RuntimeError("production deploy is human-only")
