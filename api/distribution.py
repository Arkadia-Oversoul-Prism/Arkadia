"""
Arkadia Distribution Module — FastAPI router
============================================
Handles sovereign music distribution: upload, covenant signing, and aggregator submission.

AGGREGATOR: Placeholder service is active.
To activate a live aggregator (STEM / DistroKid), set the AGGREGATOR env var:
    AGGREGATOR=stem   — STEM Disintermedia API
    AGGREGATOR=distrokid — DistroKid API
And populate AGGREGATOR_API_KEY in your environment secrets.
"""
import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("arkadia.distribution")

router = APIRouter(prefix="/api/distribution", tags=["distribution"])

# ── Storage paths ────────────────────────────────────────────────────────────
RELEASES_FILE   = "data/releases.json"
COVENANTS_FILE  = "data/covenants.json"
UPLOAD_DIR      = "static/releases"

AGGREGATOR_MODE = os.environ.get("AGGREGATOR", "placeholder")
AGGREGATOR_KEY  = os.environ.get("AGGREGATOR_API_KEY", "")


# ── Persistence helpers ───────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _load_releases() -> list[dict]:
    _ensure_dirs()
    try:
        with open(RELEASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("releases", [])
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning(f"[DIST] releases load error: {e}")
        return []


def _save_releases(releases: list[dict]) -> None:
    _ensure_dirs()
    with open(RELEASES_FILE, "w", encoding="utf-8") as f:
        json.dump({"releases": releases}, f, ensure_ascii=False, indent=2)


def _load_covenants() -> list[dict]:
    _ensure_dirs()
    try:
        with open(COVENANTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("covenants", [])
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning(f"[DIST] covenants load error: {e}")
        return []


def _save_covenants(covenants: list[dict]) -> None:
    _ensure_dirs()
    with open(COVENANTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"covenants": covenants}, f, ensure_ascii=False, indent=2)


def _get_release(release_id: str) -> Optional[dict]:
    return next((r for r in _load_releases() if r["releaseId"] == release_id), None)


def _update_release(release_id: str, updates: dict) -> Optional[dict]:
    releases = _load_releases()
    for i, r in enumerate(releases):
        if r["releaseId"] == release_id:
            releases[i] = {**r, **updates, "updatedAt": _now_iso()}
            _save_releases(releases)
            return releases[i]
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Placeholder aggregator ────────────────────────────────────────────────────

async def _submit_to_aggregator(release: dict) -> dict:
    """
    PLACEHOLDER AGGREGATOR — logs submission and returns mock success.

    Replace this function body with a real API call when live keys are available.
    Supported targets: STEM Disintermedia, DistroKid.

    Environment variables needed for live mode:
        AGGREGATOR=stem|distrokid
        AGGREGATOR_API_KEY=<your_api_key>
    """
    logger.info(
        f"[DIST][PLACEHOLDER] Submitting release to aggregator. "
        f"Mode={AGGREGATOR_MODE}, releaseId={release['releaseId']}, "
        f"title='{release['title']}', artist='{release['artistName']}'"
    )

    # Simulate network delay
    await asyncio.sleep(1.5)

    fake_ref_id = f"ARK-{release['releaseId'][:8].upper()}"

    return {
        "success": True,
        "aggregator": AGGREGATOR_MODE,
        "referenceId": fake_ref_id,
        "message": "Release accepted by placeholder aggregator. Will go live shortly.",
        "platforms": ["Spotify", "Apple Music", "Boomplay", "Tidal", "YouTube Music"],
        "estimatedLiveDate": "14-21 business days (placeholder)",
        "submittedAt": _now_iso(),
    }


async def _simulate_processing(release_id: str) -> None:
    """Background task: moves status from 'processing' → 'live' after 30s (placeholder only)."""
    await asyncio.sleep(30)
    _update_release(release_id, {"status": "live"})
    logger.info(f"[DIST][PLACEHOLDER] Release {release_id} status set to 'live' (mock)")


# ── Models ────────────────────────────────────────────────────────────────────

class CovenantSignRequest(BaseModel):
    releaseId: str
    artistId: str
    signedTerms: bool


class SubmitRequest(BaseModel):
    releaseId: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_release(
    request: Request,
    audio: UploadFile = File(...),
    artwork: UploadFile = File(...),
    title: str = Form(...),
    artistName: str = Form(...),
    featuring: str = Form(""),
    genre: str = Form(""),
    releaseDate: str = Form(""),
    isrc: str = Form(""),
    upc: str = Form(""),
):
    """
    Step 1 — Upload audio + artwork + metadata.
    Creates a release document with status 'draft'.
    Returns: releaseId
    """
    _ensure_dirs()

    # Validate file types
    audio_ct = audio.content_type or ""
    artwork_ct = artwork.content_type or ""
    allowed_audio    = {"audio/mpeg", "audio/wav", "audio/flac", "audio/x-flac", "audio/mp3", "audio/x-wav"}
    allowed_artwork  = {"image/jpeg", "image/png", "image/jpg"}

    if audio_ct not in allowed_audio:
        raise HTTPException(400, f"Audio must be MP3, WAV, or FLAC. Got: {audio_ct}")
    if artwork_ct not in allowed_artwork:
        raise HTTPException(400, f"Artwork must be JPEG or PNG. Got: {artwork_ct}")

    release_id = str(uuid.uuid4())

    # Save audio file
    audio_ext  = audio.filename.rsplit(".", 1)[-1] if audio.filename and "." in audio.filename else "mp3"
    audio_fn   = f"{release_id}_audio.{audio_ext}"
    audio_path = os.path.join(UPLOAD_DIR, audio_fn)
    with open(audio_path, "wb") as out:
        out.write(await audio.read())

    # Save artwork file
    art_ext    = artwork.filename.rsplit(".", 1)[-1] if artwork.filename and "." in artwork.filename else "jpg"
    art_fn     = f"{release_id}_artwork.{art_ext}"
    art_path   = os.path.join(UPLOAD_DIR, art_fn)
    with open(art_path, "wb") as out:
        out.write(await artwork.read())

    # Generate ISRC if not provided
    final_isrc = isrc.strip() or f"ARK{release_id[:10].upper().replace('-', '')}"

    # Get artist ID from token if available (graceful)
    artist_id = "anonymous"
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In a full Firebase integration, decode token here
            # For now, use the provided artistName as identifier
            artist_id = artistName.lower().replace(" ", "_")
    except Exception:
        pass

    release = {
        "releaseId":          release_id,
        "artistId":           artist_id,
        "title":              title.strip(),
        "artistName":         artistName.strip(),
        "featuring":          featuring.strip(),
        "genre":              genre.strip(),
        "releaseDate":        releaseDate.strip(),
        "isrc":               final_isrc,
        "upc":                upc.strip(),
        "audioUrl":           f"/static/releases/{audio_fn}",
        "artworkUrl":         f"/static/releases/{art_fn}",
        "status":             "draft",
        "aggregatorResponse": None,
        "covenantSigned":     False,
        "covenantId":         None,
        "createdAt":          _now_iso(),
        "updatedAt":          _now_iso(),
    }

    releases = _load_releases()
    releases.append(release)
    _save_releases(releases)

    logger.info(f"[DIST] Release created: {release_id} — '{title}' by {artistName}")
    return {"releaseId": release_id, "status": "draft", "release": release}


@router.post("/covenant/sign")
async def sign_covenant(body: CovenantSignRequest):
    """
    Step 2 — Artist signs the Arkadia Distribution Covenant.
    Creates a covenant record and marks the release covenantSigned = true.
    """
    if not body.signedTerms:
        raise HTTPException(400, "You must agree to the covenant terms.")

    release = _get_release(body.releaseId)
    if not release:
        raise HTTPException(404, f"Release {body.releaseId} not found.")

    covenant_id = str(uuid.uuid4())
    signature   = f"ARK-SIG-{body.artistId[:8]}-{int(time.time())}"

    covenant = {
        "covenantId": covenant_id,
        "releaseId":  body.releaseId,
        "artistId":   body.artistId,
        "signedAt":   _now_iso(),
        "terms": {
            "masterOwnership":       "100% retained by artist",
            "arkadiaFee":            "5% of streaming revenue",
            "feeCap":                "$500 USD or equivalent",
            "feeCollectionTiming":   "After artist is paid by aggregator",
            "exitClause":            "Exit at any time, no fees, masters leave with you",
            "bindingWitness":        "Arkadia mesh — stored in IMS archive",
        },
        "signature": signature,
    }

    covenants = _load_covenants()
    covenants.append(covenant)
    _save_covenants(covenants)

    _update_release(body.releaseId, {
        "covenantSigned": True,
        "covenantId":     covenant_id,
    })

    logger.info(f"[DIST] Covenant signed: {covenant_id} for release {body.releaseId}")
    return {"covenantId": covenant_id, "signature": signature, "signedAt": covenant["signedAt"]}


@router.post("/submit")
async def submit_release(body: SubmitRequest, background_tasks=None):
    """
    Step 3 — Submit release to aggregator.
    Validates: audio, artwork, metadata, covenant signed.
    Calls placeholder (or live) aggregator API.
    """
    from fastapi import BackgroundTasks
    release = _get_release(body.releaseId)
    if not release:
        raise HTTPException(404, f"Release {body.releaseId} not found.")

    # Validate readiness
    if not release.get("covenantSigned"):
        raise HTTPException(400, "Covenant must be signed before submission.")
    if not release.get("audioUrl"):
        raise HTTPException(400, "Audio file missing.")
    if not release.get("artworkUrl"):
        raise HTTPException(400, "Artwork file missing.")
    if not release.get("title"):
        raise HTTPException(400, "Title is required.")

    if release["status"] in ("submitted", "processing", "live"):
        return {"status": release["status"], "message": "Release already submitted."}

    # Update to submitted
    _update_release(body.releaseId, {"status": "submitted"})

    # Call aggregator
    try:
        agg_response = await _submit_to_aggregator(release)
        _update_release(body.releaseId, {
            "status":             "processing",
            "aggregatorResponse": agg_response,
        })

        # Placeholder: simulate going live after 30s
        if AGGREGATOR_MODE == "placeholder":
            asyncio.create_task(_simulate_processing(body.releaseId))

        logger.info(f"[DIST] Release submitted to aggregator: {body.releaseId}")
        return {
            "status":      "processing",
            "releaseId":   body.releaseId,
            "aggregator":  agg_response,
        }

    except Exception as e:
        _update_release(body.releaseId, {"status": "failed"})
        logger.error(f"[DIST] Aggregator submission failed: {e}")
        raise HTTPException(500, f"Aggregator submission failed: {e}")


@router.get("/releases/{artist_id}")
async def get_releases(artist_id: str):
    """
    Returns all releases for the given artistId.
    Includes: title, status, releaseDate, artworkUrl, createdAt.
    """
    releases = _load_releases()
    artist_releases = [
        {
            "releaseId":   r["releaseId"],
            "title":       r["title"],
            "artistName":  r["artistName"],
            "featuring":   r.get("featuring", ""),
            "genre":       r.get("genre", ""),
            "releaseDate": r.get("releaseDate", ""),
            "status":      r["status"],
            "artworkUrl":  r.get("artworkUrl", ""),
            "covenantSigned": r.get("covenantSigned", False),
            "createdAt":   r["createdAt"],
            "updatedAt":   r.get("updatedAt", ""),
            "isrc":        r.get("isrc", ""),
        }
        for r in releases
        if r.get("artistId") == artist_id
    ]
    return {"artistId": artist_id, "releases": artist_releases, "total": len(artist_releases)}


@router.get("/analytics/{release_id}")
async def get_analytics(release_id: str):
    """
    Returns streaming analytics for a release.
    PLACEHOLDER: Returns mock data until live aggregator is connected.
    """
    release = _get_release(release_id)
    if not release:
        raise HTTPException(404, f"Release {release_id} not found.")

    if release["status"] not in ("live",):
        return {
            "releaseId": release_id,
            "status":    release["status"],
            "message":   "Analytics available once release is live.",
            "analytics": None,
        }

    # Placeholder analytics — replace with real aggregator API call
    return {
        "releaseId": release_id,
        "status":    "live",
        "aggregator": AGGREGATOR_MODE,
        "note":      "Placeholder analytics. Connect live aggregator for real data.",
        "analytics": {
            "totalStreams":   1170,
            "platforms": {
                "Spotify":      712,
                "Apple Music":  243,
                "Boomplay":     158,
                "Tidal":        47,
                "YouTube Music": 10,
            },
            "estimatedRevenue": "$2.34 USD (placeholder)",
            "lastUpdated":    _now_iso(),
        },
    }


@router.get("/release/{release_id}")
async def get_release_detail(release_id: str):
    """Full release detail including covenant and aggregator response."""
    release = _get_release(release_id)
    if not release:
        raise HTTPException(404, f"Release {release_id} not found.")

    # Attach covenant if signed
    covenant = None
    if release.get("covenantId"):
        covenants = _load_covenants()
        covenant = next((c for c in covenants if c["covenantId"] == release["covenantId"]), None)

    return {"release": release, "covenant": covenant}
