"""Read-only build/revision identity for the Arkadia deployment (ADR-016).

Arkadia has one canonical reconciled deployment (see
``docs/adr/ADR-016-single-canonical-deployment.md``). This module exposes a
*read-only* probe so the actual running revision can be observed, never inferred
from source.

Two boundaries are deliberate:

* ``GET /api/version`` reports only an allowlisted set of build values. It does
  not read or echo environment variables wholesale, so no secret, credential,
  token, or arbitrary configuration can leak through it.
* Reporting a revision is **necessary** evidence of source-to-runtime
  consistency; it is **not** proof that the application is functioning
  correctly, and it cannot describe an already-running deployment until a build
  containing this endpoint has been deployed. Acceptance remains human.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Response

router = APIRouter(tags=["version"])

# Ordered by precedence. The first non-empty value wins.
_REVISION_ENV_VARS = (
    "ARKADIA_SOURCE_REVISION",
    "RENDER_GIT_COMMIT",
    "GIT_COMMIT",
    "GIT_SHA",
    "SOURCE_VERSION",
)

_BUILD_TIME_ENV_VAR = "ARKADIA_BUILD_TIME"
_SERVICE_ENV_VAR = "ARKADIA_SERVICE"

_META = "unknown"


def _first_present(names: tuple[str, ...]) -> tuple[str, str]:
    """Return ``(value, source_name)`` for the first non-empty env var, or unknown."""
    for name in names:
        raw = os.environ.get(name, "")
        value = raw.strip() if isinstance(raw, str) else ""
        if value:
            return value, name
    return _META, "none"


def resolve_build_metadata() -> dict[str, Any]:
    """Assemble the allowlisted build metadata projection.

    Only values from an explicit allowlist are returned. No value is derived
    from the request, the caller, or any other environment variable.
    """
    revision, revision_source = _first_present(_REVISION_ENV_VARS)
    build_time = os.environ.get(_BUILD_TIME_ENV_VAR, "").strip() or _META
    service = os.environ.get(_SERVICE_ENV_VAR, "").strip() or "arkadia"

    metadata_present = revision != _META
    return {
        "schema": "arkadia.version/v1",
        "service": service,
        "read_only": True,
        "canonical_deployment": "one_reconciled_deployment",
        "source_revision": revision,
        "revision_source": revision_source,
        "build_time": build_time,
        "metadata_present": metadata_present,
        "verification_note": (
            "Revision metadata is necessary evidence of source-to-runtime "
            "consistency; it is not proof of correct application behaviour and "
            "is not deployment acceptance."
        ),
    }


@router.get("/api/version")
async def version(response: Response) -> dict[str, Any]:
    """Return the read-only build/revision identity of this running deployment."""
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return resolve_build_metadata()
