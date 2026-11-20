"""Authority-policy digest binding.

A delegation is only valid while it is bound to the exact approved policy
snapshot. The digest is computed from the policy file itself so that editing
`governance/authority.yaml` without re-approval invalidates every outstanding
delegation and token — which is the required behaviour, not an accident.
"""
from __future__ import annotations

import hashlib
import os

_POLICY_PATH = os.path.join(os.path.dirname(__file__), "governance", "authority.yaml")


def policy_path() -> str:
    return _POLICY_PATH


def policy_digest(path: str | None = None) -> str:
    """SHA-256 of the policy file, normalised for line endings only.

    Raises FileNotFoundError when the policy is absent: an unknown policy is a
    deny condition, never a default-allow.
    """
    target = path or _POLICY_PATH
    with open(target, "rb") as handle:
        raw = handle.read()
    normalised = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalised).hexdigest()


def policy_identity(path: str | None = None) -> dict[str, object]:
    """The (id, version, digest) triple a delegation is bound to."""
    return {
        "policy_id": "ARK-EXEC-AUTH-001",
        "policy_version": 1,
        "policy_digest": policy_digest(path),
    }


__all__ = ["policy_path", "policy_digest", "policy_identity"]
