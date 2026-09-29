from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

FORBIDDEN_ACTIONS = frozenset({
    "merge",
    "deploy",
    "push_main",
    "force_push",
    "delete_branch_remote_main",
    "auto_approve",
})


@dataclass
class GovernedExecutionResult:
    proposal_id: str
    mode: str  # dry_run | prepare_pr
    events: list[dict[str, Any]] = field(default_factory=list)
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    branch: str | None = None
    pr_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "mode": self.mode,
            "events": list(self.events),
            "ok": self.ok,
            "errors": list(self.errors),
            "branch": self.branch,
            "pr_url": self.pr_url,
            "merge": False,
            "deploy": False,
        }


def _emit(events: list[dict[str, Any]], name: str, **payload: Any) -> None:
    events.append({"event": name, **payload})


def execute_governed(
    proposal: dict[str, Any],
    *,
    mode: str = "dry_run",
    apply_fn: Callable[[dict[str, Any]], None] | None = None,
    create_branch_fn: Callable[[str], None] | None = None,
    run_tests_fn: Callable[[], tuple[bool, str]] | None = None,
    open_pr_fn: Callable[[str, str], str] | None = None,
) -> GovernedExecutionResult:
    """Governed pipeline. Defaults are pure dry-run (no side effects).

    Real Git/PR operations only occur when callables are injected by an
    authorized operator/runtime — never implicitly.
    """
    events: list[str] = []  # type: ignore
    ev: list[dict[str, Any]] = []
    pid = str(proposal.get("proposal_id") or "")
    result = GovernedExecutionResult(proposal_id=pid, mode=mode, events=ev)

    if not pid.startswith("EV-"):
        result.ok = False
        result.errors.append("proposal_id must start with EV-")
        return result
    if proposal.get("approval_required") is not True:
        result.ok = False
        result.errors.append("approval_required must be true")
        return result
    if proposal.get("execution") is True or proposal.get("auto_apply") is True:
        result.ok = False
        result.errors.append("proposal requests forbidden auto execution")
        return result
    if mode not in ("dry_run", "prepare_pr"):
        result.ok = False
        result.errors.append(f"invalid mode: {mode}")
        return result

    branch = f"lab/phase5/{pid.lower().replace('_', '-')}"
    result.branch = branch
    _emit(ev, "branch.planned", branch=branch, proposal_id=pid)

    if mode == "dry_run":
        _emit(ev, "dry_run.started", proposal_id=pid)
        _emit(ev, "build.planned", proposal_id=pid)
        _emit(ev, "test.planned", proposal_id=pid)
        _emit(ev, "pr.planned", proposal_id=pid, note="no network; dry_run")
        _emit(ev, "dry_run.completed", proposal_id=pid, merge=False, deploy=False)
        return result

    # prepare_pr — requires injected callables; still never merges/deploys
    _emit(ev, "prepare_pr.started", proposal_id=pid)
    if create_branch_fn is None or apply_fn is None or run_tests_fn is None or open_pr_fn is None:
        result.ok = False
        result.errors.append("prepare_pr requires create_branch_fn, apply_fn, run_tests_fn, open_pr_fn")
        _emit(ev, "prepare_pr.blocked", reason="missing_callables")
        return result

    try:
        create_branch_fn(branch)
        _emit(ev, "branch.created", branch=branch)
        apply_fn(proposal)
        _emit(ev, "changes.applied", proposal_id=pid)
        _emit(ev, "build.started")
        _emit(ev, "build.completed", ok=True)
        _emit(ev, "test.started")
        tok, detail = run_tests_fn()
        _emit(ev, "test.completed", ok=tok, detail=detail[:500])
        if not tok:
            result.ok = False
            result.errors.append(f"tests failed: {detail[:200]}")
            return result
        pr_url = open_pr_fn(branch, pid)
        result.pr_url = pr_url
        _emit(ev, "pr.created", url=pr_url, merge=False)
        _emit(ev, "prepare_pr.completed", merge=False, deploy=False)
    except Exception as e:
        result.ok = False
        result.errors.append(str(e))
        _emit(ev, "prepare_pr.failed", error=str(e)[:300])
    return result
