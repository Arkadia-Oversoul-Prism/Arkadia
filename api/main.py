import asyncio
import logging
import os
import re
import time
import json
import base64
import hashlib
import hmac
import httpx
import threading
import uuid as _uuid_mod
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os as _os

# ── Arkadia auth + node registry ─────────────────────────────────────────────
# In production (ENVIRONMENT=production) an auth import failure is a fatal
# startup error — the server must not run with authentication silently disabled.
try:
    from api.auth import (
        get_current_user as _get_current_user,
        get_personal_codex as _get_personal_codex,
        require_auth as _require_auth,
    )
    _AUTH_AVAILABLE = True
except Exception as _ae:
    if _os.environ.get("ENVIRONMENT", "").strip().lower() == "production":
        raise RuntimeError(
            f"[AUTH] Auth module failed to load in production — refusing to start "
            f"with authentication disabled. Error: {_ae}"
        ) from _ae
    logging.getLogger("arkadia").warning(
        f"[AUTH] Import failed — personal context disabled (dev-mode only): {_ae}"
    )
    _AUTH_AVAILABLE = False
    async def _get_current_user(request): return None  # type: ignore
    def _get_personal_codex(nk): return None  # type: ignore
    async def _require_auth(request):  # type: ignore
        # Fail closed: a route that depends on authentication must never run
        # unauthenticated merely because the auth module failed to import.
        raise HTTPException(status_code=503, detail="Authentication unavailable")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arkadia")

GITHUB_REPO    = "Arkadia-Oversoul-Prism/Arkadia"
GITHUB_BRANCH  = "main"
GITHUB_TOKEN   = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
SOVEREIGN_KEY  = os.environ.get("SOVEREIGN_KEY", "")
_is_production = os.environ.get("ENVIRONMENT", "").strip().lower() == "production"
if not SOVEREIGN_KEY:
    if _is_production:
        raise RuntimeError(
            "[SECURITY] SOVEREIGN_KEY is required in production. "
            "The server will not start without it. "
            "Set SOVEREIGN_KEY to a long random secret in your environment variables."
        )
    logger.warning(
        "[SECURITY] SOVEREIGN_KEY env var is not set — sovereign-key-gated endpoints "
        "(forge, webhook signature, sovereign admin routes) will reject all requests. "
        "Set SOVEREIGN_KEY before deploying to production."
    )

# ── Category → SpiralVault category + display priority ───────────────────────
# Handles both root-level dirs and Oversoul_Prism/ prefixed dirs
PATH_TO_CATEGORY = {
    "00_Master":               ("NEURAL_SPINE",  1),
    "10_Core_Papers":           ("NEURAL_SPINE",  2),
    "20_Specs_Schemas":         ("COLLECTIVE",    3),
    "30_Protocols":              ("GOVERNANCE",    4),
    "40_Design_UI":              ("CREATIVE_OS",   5),
    "50_Code_Modules":           ("NEURAL_SPINE",  6),
    "60_Atlas":                  ("COLLECTIVE",    7),
    "70_Governance_Licensing":   ("GOVERNANCE",    8),
    "80_Research_Citations":     ("COLLECTIVE",    9),
    "90_Scrolls_Sigilry":        ("CREATIVE_OS",  10),
    "docs":                      ("CREATIVE_OS",  11),
}

# ── Ark Date — Spiral Star Date coordinate system ────────────────────────────
# Epoch: March 31, 2026 — the Birthday Seal. Day 1 of the 8-year Ark.
# Source: DOC1_MASTER_WEIGHTS.md — Zahrune Nova / Arkadia Nexus EchoField
from datetime import date as _date

ARK_EPOCH = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
ARK_DURATION_YEARS = 8

def _ark_date() -> dict:
    """Compute the living Ark Date — the Oracle's true temporal memory coordinate.

    Epoch: March 31 2026 (Birthday Seal). 8-year Ark. Day 1 = March 31 2026.
    Linear time is a sideways scaffold; the Ark Date is the primary coordinate.
    """
    now         = datetime.now(timezone.utc)
    delta       = now - ARK_EPOCH
    total_days  = max(1, delta.days + 1)          # Day 1 = epoch day itself

    ark_year    = min(((total_days - 1) // 365) + 1, ARK_DURATION_YEARS)
    day_in_year = ((total_days - 1) % 365) + 1

    pulse  = now.hour
    breath = now.minute
