"""WEAVER-K7 — Governed Engineering Workbench.

Composition layer over K1/K5/K6/K3/K0.1. No second write path.
RECON/CONTEXT/PROPOSAL ≠ AUTHORIZATION.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .pass_spec import PassSpec, current_head, current_origin_main
from .session import (
    SessionState,
    WeaverSession,
    approve as session_approve,
    create_session,
    execute as session_execute,
    propose as session_propose,
    reject as session_reject,
    review_bundle as session_review_bundle,
    run_recon,
)


@dataclass
class WorkbenchResult:
    ok: bool
    state: str
    message: str = ""
    session: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Workbench:
    """Thin orchestration surface; all mutation via K6 → K5 → K3."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.session: WeaverSession | None = None

    def start(self, objective: str) -> WorkbenchResult:
        self.session = create_session(objective, repo_root=self.repo_root)
        return WorkbenchResult(
            ok=True,
            state=self.session.state,
            message="session created",
            session=self.session.to_dict(),
        )

    def recon(self) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        run_recon(self.session, repo_root=self.repo_root)
        return WorkbenchResult(
            ok=True,
            state=self.session.state,
            message="recon complete",
            session=self.session.to_dict(),
            review=self.review_bundle(),
        )

    def propose(self, *, allowed_paths: list[str] | None = None, findings: list[str] | None = None) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        session_propose(
            self.session,
            allowed_paths=allowed_paths,
            findings=findings,
            repo_root=self.repo_root,
        )
        return WorkbenchResult(
            ok=self.session.state == SessionState.AWAITING_APPROVAL.value,
            state=self.session.state,
            message=self.session.message,
            session=self.session.to_dict(),
            review=self.review_bundle(),
        )

    def review_bundle(self) -> dict[str, Any]:
        if not self.session:
            return {"error": "no session"}
        base = session_review_bundle(self.session)
        head = current_head(self.repo_root)
        origin = current_origin_main(self.repo_root)
        return {
            **base,
            "repository": {
                "head_sha": head,
                "origin_sha": origin,
                "ahead_hint": head != origin if origin else None,
            },
            "authorization_state": "requires PassSpec + explicit approval",
            "approval_state": self.session.state,
            "publication_policy": "K0.1 — NO EPHEMERAL PROGRESS",
            "next_action": (
                "awaiting human approval"
                if self.session.state == SessionState.AWAITING_APPROVAL.value
                else "awaiting human authorization"
            ),
            "context_note": "CONTEXT ≠ AUTHORIZATION",
        }

    def approve(self) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        session_approve(self.session, repo_root=self.repo_root)
        return WorkbenchResult(
            ok=self.session.state == SessionState.APPROVED.value,
            state=self.session.state,
            message=self.session.message,
            session=self.session.to_dict(),
            review=self.review_bundle(),
        )

    def reject(self) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        session_reject(self.session)
        return WorkbenchResult(
            ok=True,
            state=self.session.state,
            message=self.session.message,
            session=self.session.to_dict(),
        )

    def execute(self, spec: PassSpec) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        if not isinstance(spec, PassSpec):
            return WorkbenchResult(ok=False, state="BLOCKED", message="PassSpec required")
        session_execute(self.session, spec, repo_root=self.repo_root)
        ok = self.session.terminal_status in (
            SessionState.COMPLETED.value,
            SessionState.NO_CHANGE.value,
            SessionState.PUBLISHED.value,
            "NO_CHANGE",
            "PASS",
        )
        return WorkbenchResult(
            ok=ok,
            state=self.session.state,
            message=self.session.message,
            session=self.session.to_dict(),
            review=self.review_bundle(),
        )

    def status(self) -> WorkbenchResult:
        if not self.session:
            return WorkbenchResult(ok=False, state="BLOCKED", message="no session")
        return WorkbenchResult(
            ok=True,
            state=self.session.state,
            message=self.session.message,
            session=self.session.to_dict(),
            review=self.review_bundle(),
        )


def main(argv: list[str] | None = None) -> int:
    """Minimal CLI: recon | propose | review | approve | reject | status (no silent execute)."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(prog="weaver-workbench", description="WEAVER-K7 governed workbench")
    parser.add_argument("command", choices=["start", "recon", "propose", "review", "approve", "reject", "status"])
    parser.add_argument("--objective", default="", help="Human objective (for start)")
    parser.add_argument("--paths", default="weaver/", help="Comma-separated path hints for propose")
    args = parser.parse_args(argv)

    # In-process CLI is ephemeral; status of multi-step needs external process state.
    # For CLI demos we keep a single-shot style or start→action.
    wb = Workbench()
    if args.command == "start":
        if not args.objective:
            print("objective required", file=sys.stderr)
            return 2
        r = wb.start(args.objective)
    elif args.command == "recon":
        if not args.objective:
            print("provide --objective to start+recon", file=sys.stderr)
            return 2
        wb.start(args.objective)
        r = wb.recon()
    elif args.command == "propose":
        if not args.objective:
            print("provide --objective", file=sys.stderr)
            return 2
        wb.start(args.objective)
        paths = [p.strip() for p in args.paths.split(",") if p.strip()]
        r = wb.propose(allowed_paths=paths)
    elif args.command == "review":
        if not args.objective:
            print("provide --objective for propose+review demo", file=sys.stderr)
            return 2
        wb.start(args.objective)
        paths = [p.strip() for p in args.paths.split(",") if p.strip()]
        wb.propose(allowed_paths=paths)
        r = WorkbenchResult(ok=True, state=wb.session.state, review=wb.review_bundle(), session=wb.session.to_dict())
    elif args.command == "approve":
        print("CLI approve requires in-process session; use Python API Workbench.approve()", file=sys.stderr)
        return 2
    elif args.command == "reject":
        print("CLI reject requires in-process session; use Python API Workbench.reject()", file=sys.stderr)
        return 2
    else:
        r = wb.status()

    print(json.dumps(r.to_dict(), indent=2, default=str))
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
