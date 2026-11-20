"""Arkadia Executive Identity Broker — Gate 1A.

Issues short-lived, asymmetrically signed machine JWTs for
`service:ARKADIA-CHIEF-001`. The broker is a separate trust boundary from the
agent process: it holds the private signing key, and the agent never receives
it. The agent can only *request* a token; it cannot choose or widen the claims.

Every claim is fixed from the server-side delegation record. A token is issued
only when the delegation is ACTIVE, unexpired, unrevoked, and bound to the
current approved policy digest.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from executive_office import (
    MAX_TOKEN_TTL_SECONDS,
    PRINCIPAL_ID,
    PRINCIPAL_SUBJECT,
    PRINCIPAL_TYPE,
    TOKEN_AUDIENCE,
)
from executive_office.policy import policy_digest
from executive_office.registry import Delegation, DelegationRegistry

DEFAULT_ISSUER = "arkadia-executive-identity-broker"
KEY_ID = "eo-broker-ed25519-1"
ALGORITHM = "EdDSA"


def issuer() -> str:
    return os.environ.get("EXECUTIVE_BROKER_ISSUER", DEFAULT_ISSUER).strip() or DEFAULT_ISSUER


def _key_dir() -> str:
    return os.environ.get("EXECUTIVE_BROKER_KEY_DIR") or os.path.join(
        os.environ.get("SOLSPIRE_DATA_DIR", "data"), "executive_broker_keys"
    )


def _private_key_path() -> str:
    return os.path.join(_key_dir(), "broker_ed25519_private.pem")


def _public_key_path() -> str:
    return os.path.join(_key_dir(), "broker_ed25519_public.pem")


class BrokerUnavailable(RuntimeError):
    """Raised when the broker cannot issue. Callers must deny, never retry-open."""


class ExecutiveIdentityBroker:
    """Issues machine tokens. Holds the only copy of the signing key."""

    def __init__(self, *, registry: DelegationRegistry | None = None, key_dir: str | None = None) -> None:
        self.registry = registry or DelegationRegistry()
        self._key_dir = key_dir

    # ── key material ─────────────────────────────────────────────────────────
    def _paths(self) -> tuple[str, str]:
        if self._key_dir:
            return (
                os.path.join(self._key_dir, "broker_ed25519_private.pem"),
                os.path.join(self._key_dir, "broker_ed25519_public.pem"),
            )
        return _private_key_path(), _public_key_path()

    def ensure_keypair(self) -> tuple[str, str]:
        """Create the broker keypair once, on first use. Returns (priv, pub) paths."""
        priv_path, pub_path = self._paths()
        os.makedirs(os.path.dirname(priv_path), exist_ok=True)
        if os.path.exists(priv_path) and os.path.exists(pub_path):
            return priv_path, pub_path
        key = Ed25519PrivateKey.generate()
        private_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_pem = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # 0600: the private key is readable only by the broker process owner.
        fd = os.open(priv_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(private_pem)
        with open(pub_path, "wb") as handle:
            handle.write(public_pem)
        return priv_path, pub_path

    def public_key_pem(self) -> bytes:
        """The verification key. Safe to publish; this is the JWKS material."""
        _, pub_path = self.ensure_keypair()
        with open(pub_path, "rb") as handle:
            return handle.read()

    def _private_key_pem(self) -> bytes:
        priv_path, _ = self.ensure_keypair()
        with open(priv_path, "rb") as handle:
            return handle.read()

    # ── issuance ─────────────────────────────────────────────────────────────
    def issue(
        self,
        *,
        delegation_id: str | None = None,
        ttl_seconds: int = MAX_TOKEN_TTL_SECONDS,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Mint one token for the active delegation.

        Raises BrokerUnavailable when no serviceable delegation exists, when the
        policy digest has drifted, or when the registry cannot be read. There is
        no path that issues a token without a live, current grant.
        """
        try:
            delegation = (
                self.registry.get(delegation_id)
                if delegation_id
                else self.registry.active_for_principal(PRINCIPAL_ID)
            )
        except Exception as exc:  # registry unreadable → deny
            raise BrokerUnavailable(f"delegation registry unavailable: {exc}") from exc

        if delegation is None:
            raise BrokerUnavailable("no active delegation for principal")
        if not delegation.is_serviceable(now):
            raise BrokerUnavailable(f"delegation is not serviceable (status={delegation.status})")

        try:
            current_digest = policy_digest()
        except OSError as exc:
            raise BrokerUnavailable(f"authority policy unavailable: {exc}") from exc
        if current_digest != delegation.policy_digest:
            raise BrokerUnavailable("delegation is bound to a stale policy digest")

        issued_at = int(now if now is not None else time.time())
        ttl = max(1, min(int(ttl_seconds), MAX_TOKEN_TTL_SECONDS))
        claims = {
            "iss": issuer(),
            "aud": TOKEN_AUDIENCE,
            "sub": PRINCIPAL_SUBJECT,
            "principal_type": PRINCIPAL_TYPE,
            "owner_sub": delegation.owner_uid,
            "workspace_id": delegation.workspace_id,
            "delegation_id": delegation.delegation_id,
            "policy_id": delegation.policy_id,
            "policy_version": delegation.policy_version,
            "policy_digest": delegation.policy_digest,
            "scope": delegation.capability_scope,
            "resource_scope": delegation.resource_scope,
            "credential_epoch": delegation.credential_epoch,
            "jti": f"eojti-{uuid.uuid4().hex}",
            "iat": issued_at,
            "nbf": issued_at,
            "exp": issued_at + ttl,
        }
        token = jwt.encode(
            claims,
            self._private_key_pem(),
            algorithm=ALGORITHM,
            headers={"kid": KEY_ID, "typ": "JWT"},
        )
        return {
            "token": token,
            "token_type": "Bearer",
            "expires_in": ttl,
            "expires_at": issued_at + ttl,
            "delegation_id": delegation.delegation_id,
            "credential_epoch": delegation.credential_epoch,
            "jti": claims["jti"],
        }


__all__ = [
    "ExecutiveIdentityBroker",
    "BrokerUnavailable",
    "issuer",
    "KEY_ID",
    "ALGORITHM",
    "DEFAULT_ISSUER",
]
