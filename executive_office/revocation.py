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

    # Gate 2: withdraw Engineering Lab grants issued under this delegation too.
    # Weaver's ledger above covers `ew_authorizations`; the Lab keeps its own
    # `el_authorizations` table, so a cascade that stopped at Weaver would leave
    # a Lab grant live. The Lab's dispatch gate re-reads the delegation and
    # would refuse it anyway — this makes the withdrawal explicit and durable
    # rather than relying on the guard alone.
    #
    # Deliberately non-fatal: the delegation is already REVOKED above, which is
    # the safe direction, and the dispatch guard is the backstop. A failure here
    # is reported, not swallowed.
    lab_revoked = 0
    lab_error: str | None = None
    try:
        from lab.engineering_lab.store import EngineeringLabStore

        lab_revoked = EngineeringLabStore().revoke_for_delegation(
            delegation_id, reason=f"delegation revoked: {reason}"
        )
    except Exception as exc:  # noqa: BLE001 - report, never mask the revocation
        lab_error = f"{type(exc).__name__}: {exc}"

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
        "revoked_lab_authorizations": lab_revoked,
        "lab_revocation_error": lab_error,
        "cancelled_jobs": cancelled_jobs,
        "credential_epoch": delegation.credential_epoch,
        "note": (
            "Delegation revoked, outstanding authorizations withdrawn and queued "
            "work cancelled. Audit history is preserved."
        ),
    }


__all__ = ["revoke_delegation_cascade"]
