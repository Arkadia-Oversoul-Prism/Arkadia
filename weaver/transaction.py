"""WEAVER-K3 — governed Plan → Implement → Verify transaction.

Runs entirely inside K0.1 session_kernel + K2 provider boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agent import run_authorized
from .pass_spec import PassSpec, PassSpecError
from .plan import Plan, PlanError, approve_plan, build_plan_from_spec, validate_plan_against_spec
from .session_kernel import SessionResult, finalize_session, preflight


@dataclass
class TransactionResult:
    ok: bool
    status: str  # PASS | NO_CHANGE | BLOCKED | FAILED | PENDING_PUBLICATION
    stage: str
    message: str = ""
    plan: dict[str, Any] = field(default_factory=dict)
    session: SessionResult | None = None


def run_transaction(
    spec: PassSpec,
    *,
    task: str | None = None,
    plan: Plan | None = None,
    require_plan_approval: bool = True,
    auto_approve_if_spec_is_authorization: bool = True,
    repo_root: str = ".",
) -> TransactionResult:
    """
    Execute a governed K3 transaction.

    Human authorization is the PassSpec. Dynamic plans require approval unless
    auto_approve_if_spec_is_authorization and the plan is derived from the spec.
    """
    try:
        preflight(spec, repo_root)
    except PassSpecError as e:
        return TransactionResult(ok=False, status="BLOCKED", stage="preflight", message=str(e))

    if plan is None:
        plan = build_plan_from_spec(spec)
        derived = True
    else:
        derived = False

    try:
        validate_plan_against_spec(plan, spec)
    except PlanError as e:
        return TransactionResult(
            ok=False,
            status="BLOCKED",
            stage="plan_scope",
            message=str(e),
            plan=plan.to_dict(),
        )

    if require_plan_approval:
        if not plan.approved:
            if auto_approve_if_spec_is_authorization and derived:
                # PassSpec itself is the human authorization for this envelope
                approve_plan(plan)
            else:
                return TransactionResult(
                    ok=False,
                    status="BLOCKED",
                    stage="plan_approval",
                    message="plan requires human approval (PLAN ≠ AUTHORIZATION)",
                    plan=plan.to_dict(),
                )

    # Merge plan tests into execution if spec has none
    if not spec.required_tests and plan.required_tests:
        spec.required_tests = list(plan.required_tests)

    task_text = task or spec.objective
    session = run_authorized(task_text, spec, repo_root=repo_root)

    status = session.status if session else "FAILED"
    return TransactionResult(
        ok=bool(session and session.ok),
        status=status,
        stage=session.stage if session else "implement",
        message=session.message if session else "no session",
        plan=plan.to_dict(),
        session=session,
    )


def finalize_no_change(spec: PassSpec, *, reason: str = "objective already satisfied", repo_root: str = ".") -> SessionResult:
    """Explicit NO_CHANGE terminal path."""
    return finalize_session(
        spec,
        [],
        commit_message=f"weaver: {spec.pass_id} — NO_CHANGE",
        status_hint="NO_CHANGE",
        failure_reason="",
        repo_root=repo_root,
    )
