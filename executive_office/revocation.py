"""Revocation cascade — Gate 1C.

Revoking a delegation must not merely stop new tokens. It must also:

  * invalidate every outstanding enterprise Authorization issued under that
    delegation, so Weaver dispatch refuses them even though they have not
    expired;
  * cancel queued work, so nothing dispatches after the revocation;
  * leave the audit trail intact.

This module performs that cascade against the existing stores. It creates no
new authority and no new execution path — it only withdraws.
"""
from __future__ import annotations

from typing import Any

from executive_office.registry import DelegationRegistry
from weaver.authorization_revocation import AuthorizationRevocationStore


def revoke_delegation_cascade(
    *,
    delegation_id: str,
    founder_uid: str,
    reason: str,
    registry: DelegationRegistry | None = None,
    revocations: AuthorizationRevocationStore | None = None,
) -> dict[str, Any]:
    """Revoke a delegation and withdraw everything that depended on it.

    Order matters and is deliberate: the delegation is committed to REVOKED
    first (so no new token can be issued), then outstanding authorizations are
    revoked, then queued work is cancelled. If the authorization revocation
    fails, the delegation is already revoked — the safe direction.
    """
    registry = registry or DelegationRegistry()
    revocations = revocations or AuthorizationRevocationStore()

    # Count queued work before the revoke: `registry.revoke` already cancels it,
    # so a post-hoc count would always read zero.
    queued_before = [
        job for job in registry.queued_work(delegation_id) if job.get("status") == "QUEUED"
    ]

    delegation = registry.revoke(
        delegation_id=delegation_id,
        founder_uid=founder_uid,
        reason=reason,
    )

    revoked_authorizations = revocations.revoke_for_delegation(
        delegation_id=delegation_id,
        reason=f"delegation revoked: {reason}",
        revoked_by=founder_uid,
    )

    # Idempotent: cancels anything still QUEUED (normally nothing, because the
    # revoke above already did it).
    registry.cancel_queued_work(
        delegation_id=delegation_id,
        reason=f"delegation revoked: {reason}",
    )
    cancelled_jobs = len(queued_before)

    return {
        "delegation": delegation.to_dict(),
        "revoked_authorizations": revoked_authorizations,
        "cancelled_jobs": cancelled_jobs,
        "credential_epoch": delegation.credential_epoch,
        "note": (
            "Delegation revoked, outstanding authorizations withdrawn and queued "
            "work cancelled. Audit history is preserved."
        ),
    }


__all__ = ["revoke_delegation_cascade"]
