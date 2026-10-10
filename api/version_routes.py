"""Read-only build/revision identity for the Arkadia deployment (ADR-016).

Arkadia has one canonical reconciled deployment (see
``docs/adr/ADR-016-single-canonical-deployment.md``). This module exposes a
*read-only* probe so the actual running revision can be observed, never inferred
from source.

Three boundaries are deliberate:

* ``GET /api/version`` reports only an allowlisted set of build values. It does
  not read or echo environment variables wholesale, so no secret, credential,
  token, or arbitrary configuration can leak through it. Only *revision*
  variables are inspected, and a value is echoed only once it has been validated
  as a Git revision identifier.
* Reporting a revision is **necessary** evidence of source-to-runtime
  consistency; it is **not** proof that the application is functioning
  correctly, and it cannot describe an already-running deployment until a build
  containing this endpoint has been deployed. Acceptance remains human.
* Absence, placeholders, invalid values, and disagreement between revision
  sources are all reported explicitly and are never smoothed into a revision.
  The semantics live in ``kernel.revision_identity`` so this endpoint and
  ``scripts/version_reconciliation.py`` cannot disagree about what "absent"
  means.

Payload schema note: ``arkadia.version/v1`` is unchanged and additive. A
non-revision value (a tag, a padded SHA, an uppercase placeholder) is no longer
echoed as ``source_revision``; its classification is reported in
``revision_sources`` instead.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Response

from kernel.revision_identity import (
    ABSENT_REVISION,
    CONFLICT_SOURCE_PAIR,
    REVISION,
    REVISION_ENV_VARS,
    classify,
    normalize,
)

router = APIRouter(tags=["version"])

# Ordered by precedence. The first entry yielding a *valid* revision wins.
_REVISION_ENV_VARS = REVISION_ENV_VARS

_BUILD_TIME_ENV_VAR = "ARKADIA_BUILD_TIME"
_SERVICE_ENV_VAR = "ARKADIA_SERVICE"


def _source_provenance(name: str) -> dict[str, Any]:
    """Describe one revision source without echoing anything unusable.

    ``value`` is populated only for a validated Git identifier. A misconfigured
    variable (a tag, a placeholder, a truncated SHA) is reported by its
    classification alone, so diagnostics never turn into an environment dump.
    """
    status = classify(os.environ.get(name))
    raw = normalize(os.environ.get(name))
    return {
        "status": status,
        "value": raw if status == REVISION else None,
    }


def _select_revision() -> tuple[str | None, str]:
    """Return ``(revision, source_name)`` for the first valid revision: ``(None, "none")`` if none."""
    for name in _REVISION_ENV_VARS:
        value = os.environ.get(name)
        if classify(value) == REVISION:
            return normalize(value), name
    return None, "none"


def _detect_conflict(sources: dict[str, dict[str, Any]]) -> bool:
    """True when both members of the conflict pair are valid revisions that differ.

    A baked build argument and a provider-injected commit describe the same
    build. If both are valid and disagree, one of them names a revision that was
    not built, and precedence must not be read as proof that the winner is
    correct.
    """
    values = []
    for name in CONFLICT_SOURCE_PAIR:
        entry = sources.get(name, {})
        if entry.get("status") != REVISION:
            return False
        values.append(entry.get("value"))
    return len(values) == 2 and values[0] != values[1]


def resolve_build_metadata() -> dict[str, Any]:
    """Assemble the allowlisted build metadata projection.

    Only values from an explicit allowlist are returned. No value is derived
    from the request, the caller, or any other environment variable.
    """
    revision, revision_source = _select_revision()
    sources = {name: _source_provenance(name) for name in CONFLICT_SOURCE_PAIR}
    conflict = _detect_conflict(sources)
    build_time_raw = os.environ.get(_BUILD_TIME_ENV_VAR, "")
    build_time = (
        build_time_raw.strip()
        if isinstance(build_time_raw, str) and build_time_raw.strip()
        else ABSENT_REVISION
    )
    service_raw = os.environ.get(_SERVICE_ENV_VAR, "")
    service = (
        service_raw.strip()
        if isinstance(service_raw, str) and service_raw.strip()
        else "arkadia"
    )

    return {
        "schema": "arkadia.version/v1",
        "service": service,
        "read_only": True,
        "canonical_deployment": "one_reconciled_deployment",
        "source_revision": revision if revision is not None else ABSENT_REVISION,
        "revision_source": revision_source,
        "revision_conflict": conflict,
        "revision_sources": sources,
        "build_time": build_time,
        "metadata_present": revision is not None,
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
