"""Read-only, secret-redacted production security attestation for operators."""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request, Response

from api.auth import require_sovereign

logger = logging.getLogger("arkadia.operator_security")
router = APIRouter(tags=["operator-security"])


@router.get("/api/operator/security-verification")
async def security_verification(
    request: Request,
    response: Response,
    user: dict[str, Any] = Depends(require_sovereign),
) -> dict[str, Any]:
    """Return a redacted snapshot of auth posture for the authorized caller.

    This endpoint is deliberately read-only. It never returns secret values,
    request headers, user identifiers, emails, or raw exception text.
    """
    import api.auth as auth

    run_id = str(uuid.uuid4())
    production = os.environ.get("ENVIRONMENT", "").strip().lower() == "production"
    firebase_ready = bool(getattr(auth, "_firebase_app", None)) and not bool(
        getattr(auth, "_dev_mode", True)
    )

    # Verify the exact bearer token through the same Firebase Admin verifier.
    # Do not infer successful verification merely from a profile's uid field.
    token = auth._extract_token(request)
    try:
        claims = auth.verify_firebase_token(token) if token else None
    except Exception:
        # Never propagate raw provider/auth exception details to the response or logs.
        claims = None
    verified_identity = (
        production
        and firebase_ready
        and isinstance(claims, dict)
        and bool(claims.get("uid"))
        and claims.get("uid") == user.get("uid")
    )
    try:
        sovereign_authorized = int(user.get("access_level", 0) or 0) >= 3
    except (TypeError, ValueError):
        sovereign_authorized = False

    checks = [
        {"id": "production_environment", "status": "PASS" if production else "FAIL"},
        {"id": "firebase_admin_initialized", "status": "PASS" if firebase_ready else "FAIL"},
        {"id": "firebase_identity_verified", "status": "PASS" if verified_identity else "FAIL"},
        {"id": "sovereign_authorization", "status": "PASS" if sovereign_authorized else "FAIL"},
    ]
    overall = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    observed_at = datetime.now(timezone.utc).isoformat()
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"

    # Deliberately exclude caller identity, token material, and request headers.
    logger.info(
        "[OPERATOR_SECURITY_VERIFICATION] run_id=%s result=%s production=%s "
        "firebase_admin=%s verified_identity=%s sovereign_authorized=%s",
        run_id, overall, production, firebase_ready, verified_identity,
        sovereign_authorized,
    )
    return {
        "run_id": run_id,
        "observed_at": observed_at,
        "result": overall,
        "read_only": True,
        "checks": checks,
        "redaction": "secret-values-and-caller-identifiers-omitted",
    }
