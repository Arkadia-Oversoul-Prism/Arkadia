"""Phase 5 — Weaver Governed Execution (proposal → branch → test → PR).

No merge. No deploy. Approval is external to this module.
"""
from .governed import GovernedExecutionResult, execute_governed, FORBIDDEN_ACTIONS

__all__ = ["GovernedExecutionResult", "execute_governed", "FORBIDDEN_ACTIONS"]
