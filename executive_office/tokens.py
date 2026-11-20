"""Machine-token verification and the `require_executive_principal` dependency.

A valid signature is necessary and never sufficient. After the cryptographic
checks, the live delegation record is re-read and must still be ACTIVE,
unexpired, unrevoked, on the same credential epoch, and bound to the current
policy digest. Anything else is a deny.

This module deliberately does not touch `api.auth.require_auth`. Human routes
keep Firebase verification; machine routes use this dependency. A Firebase
human token is not a machine identity and is rejected here.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import HTTPException, Request

from executive_office import (
    PRINCIPAL_SUBJECT,
    PRINCIPAL_TYPE,
    TOKEN_AUDIENCE,
)
from executive_office.broker import ALGORITHM, KEY_ID, ExecutiveIdentityBroker, issuer
from executive_office.policy import policy_digest
from executive_office.registry import Delegation, DelegationRegistry


class ExecutiveAuthError(HTTPException):
    """401/403 with a machine-readable reason. Never leaks token material."""

    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(status_code=status_code, detail=reason)
        self.reason = reason


def _deny(reason: str, status_code: int = 401) -> ExecutiveAuthError:
    return ExecutiveAuthError(status_code, reason)


@dataclass(frozen=True)
class ExecutivePrincipal:
    """The validated machine principal. Derived only from server-side state."""

    principal_id: str
    subject: str
    owner_uid: str
    workspace_id: str
    delegation_id: str
    policy_id: str
    policy_version: int
    policy_digest: str
    capability_scope: Any
    resource_scope: Any
    credential_epoch: int
    jti: str
    expires_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "subject": self.subject,
            "owner_uid": self.owner_uid,
            "workspace_id": self.workspace_id,
            "delegation_id": self.delegation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_digest": self.policy_digest,
            "capability_scope": self.capability_scope,
            "resource_scope": self.resource_scope,
            "credential_epoch": self.credential_epoch,
            "jti": self.jti,
            "expires_at": self.expires_at,
        }

    def has_capability(self, capability: str) -> bool:
        scope = self.capability_scope
        if isinstance(scope, dict):
            allowed = scope.get("capabilities") or scope.get("tools") or []
        elif isinstance(scope, list):
            allowed = scope
        else:
            allowed = []
        return capability in allowed

    def allows_resource(self, resource: str) -> bool:
        scope = self.resource_scope
        if isinstance(scope, dict):
            allowed = scope.get("resources") or scope.get("projects") or []
        elif isinstance(scope, list):
            allowed = scope
        else:
            allowed = []
        return resource in allowed


def _extract_bearer(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip() or None
    return None


def verify_machine_token(
    token: str,
    *,
    registry: DelegationRegistry | None = None,
    broker: ExecutiveIdentityBroker | None = None,
    now: float | None = None,
) -> ExecutivePrincipal:
    """Verify a broker token and the live delegation behind it.

    Raises ExecutiveAuthError on every failure path. There is no permissive
    branch: an unreadable registry, a missing claim, or a drifted policy all
    deny.
    """
    if not token:
        raise _deny("machine token required")

    broker = broker or ExecutiveIdentityBroker(registry=registry)
    registry = registry or broker.registry

    try:
        public_key = broker.public_key_pem()
    except Exception as exc:
        raise _deny("identity broker unavailable", 503) from exc

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise _deny("malformed machine token") from exc

    if header.get("kid") != KEY_ID:
        raise _deny("unknown signing key id")
    if header.get("alg") != ALGORITHM:
        raise _deny("unsupported token algorithm")

    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            audience=TOKEN_AUDIENCE,
            issuer=issuer(),
            options={"require": ["exp", "iat", "nbf", "aud", "iss", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise _deny("machine token expired") from exc
    except jwt.ImmatureSignatureError as exc:
        raise _deny("machine token not yet valid") from exc
    except jwt.InvalidAudienceError as exc:
        raise _deny("machine token audience mismatch") from exc
    except jwt.InvalidIssuerError as exc:
        raise _deny("machine token issuer mismatch") from exc
    except jwt.PyJWTError as exc:
        raise _deny("machine token signature invalid") from exc

    # ── claim shape ──────────────────────────────────────────────────────────
    if claims.get("sub") != PRINCIPAL_SUBJECT:
        raise _deny("machine token subject is not the executive principal")
    if claims.get("principal_type") != PRINCIPAL_TYPE:
        raise _deny("machine token principal type mismatch")
    for required in ("owner_sub", "workspace_id", "delegation_id", "policy_digest", "credential_epoch"):
        if not claims.get(required):
            raise _deny(f"machine token missing claim: {required}")

    # ── live delegation ──────────────────────────────────────────────────────
    try:
        delegation: Delegation | None = registry.find(str(claims["delegation_id"]))
    except Exception as exc:
        raise _deny("delegation registry unavailable", 503) from exc
    if delegation is None:
        raise _deny("delegation not found")
    if not delegation.is_serviceable(now):
        raise _deny(f"delegation is not serviceable (status={delegation.status})", 403)
    if int(claims["credential_epoch"]) != delegation.credential_epoch:
        raise _deny("credential epoch superseded", 403)
    if str(claims["owner_sub"]) != delegation.owner_uid:
        raise _deny("token owner does not match the delegation", 403)
    if str(claims["workspace_id"]) != delegation.workspace_id:
        raise _deny("token workspace does not match the delegation", 403)
    if str(claims["policy_digest"]) != delegation.policy_digest:
        raise _deny("token policy digest does not match the delegation", 403)

    try:
        current_digest = policy_digest()
    except OSError as exc:
        raise _deny("authority policy unavailable", 503) from exc
    if current_digest != delegation.policy_digest:
        raise _deny("delegation is bound to a stale policy digest", 403)

    return ExecutivePrincipal(
        principal_id=str(claims["sub"]).split(":", 1)[-1],
        subject=str(claims["sub"]),
        owner_uid=delegation.owner_uid,
        workspace_id=delegation.workspace_id,
        delegation_id=delegation.delegation_id,
        policy_id=delegation.policy_id,
        policy_version=delegation.policy_version,
        policy_digest=delegation.policy_digest,
        capability_scope=delegation.capability_scope,
        resource_scope=delegation.resource_scope,
        credential_epoch=delegation.credential_epoch,
        jti=str(claims["jti"]),
        expires_at=int(claims["exp"]),
    )


async def require_executive_principal(request: Request) -> ExecutivePrincipal:
    """FastAPI dependency for machine-only Executive Office routes.

    A Firebase human token presented here fails: it is not a broker token, so
    the signature check rejects it. That is the intended separation.
    """
    token = _extract_bearer(request)
    if not token:
        raise _deny("machine token required")
    return verify_machine_token(token)


__all__ = [
    "ExecutivePrincipal",
    "ExecutiveAuthError",
    "verify_machine_token",
    "require_executive_principal",
]
