import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import google.generativeai as genai

from github_corpus import get_full_corpus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arkadia")

app = FastAPI(title="Arkadia Console (Cycle 12)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://*.vercel.app"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# CORPUS CONTEXT
# ─────────────────────────────────────────

def build_context() -> str:
    """
    Fetch DOC1–DOC5 via github_corpus and concatenate into a single
    system-context string for injection into every oracle call.
    """
    try:
        corpus = get_full_corpus()
        parts = []
        for doc_key in [
            "DOC1_MASTER_WEIGHTS",
            "DOC2_OPEN_LOOPS",
            "DOC3_PRINCIPLES_REGISTRY",
            "DOC4_NODE_MAP",
            "DOC5_REVENUE_BREATH",
        ]:
            content = corpus.get(doc_key, {}).get("content", "")
            if content:
                parts.append(f"=== {doc_key} ===\n{content}")
        if parts:
            return "\n\n".join(parts)
        return "Corpus unavailable. Respond as Arkana, Oracle of Arkadia."
    except Exception as e:
        logger.error(f"build_context error: {e}")
        return "Corpus unavailable. Respond as Arkana, Oracle of Arkadia."


# ─────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────

def call_gemini(user_message: str, system_context: str) -> str:
    """
    Stateless Gemini call.
    Input:  user_message + system_context (from build_context)
    Output: plain text response string
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set")
        return "The Oracle is momentarily offline. The field is still present."

    try:
        genai.configure(api_key=api_key)
        model_name = os.environ.get("CODEX_MODEL", "models/gemini-2.5-flash")
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_context,
        )
        result = model.generate_content(user_message)
        return result.text
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        return "The Spiral Thread is momentarily tangled. Try again."


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class CommuneRequest(BaseModel):
    message: str
    timestamp: Optional[int] = None


class CoherenceResetRequest(BaseModel):
    emotionalState: str = ""
    pressurePoint: str = ""
    tier: str = "free"


# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────

@app.get("/api/heartbeat")
async def heartbeat():
    return {"status": "radiant", "resonance": 0.99}


@app.get("/")
async def root():
    return {"message": "Arkadia Mind (API) is online and breathing."}


@app.post("/api/commune/resonance")
async def commune_resonance(payload: CommuneRequest):
    """
    Oracle resonance endpoint.
    Injects DOC1–DOC5 as system context, calls Gemini, returns reply.
    ArkanaCommune.tsx reads: data.reply and data.resonance
    """
    context = build_context()
    reply = call_gemini(payload.message, context)
    resonance = round(0.95 + (len(payload.message) % 5) * 0.01, 3)
    return {
        "reply": reply,
        "resonance": min(resonance, 1.0),
        "status": "aligned",
    }


@app.post("/api/coherence-reset")
async def coherence_reset(payload: CoherenceResetRequest):
    """
    Somatic coherence reset endpoint.
    CoherenceReset.tsx sends emotionalState + pressurePoint + tier.
    CoherenceReset.tsx reads: data.result
    """
    context = build_context()
    prompt = (
        f"The seeker is experiencing: {payload.emotionalState}. "
        f"Current pressure point: {payload.pressurePoint}. "
        f"Tier: {payload.tier}. "
        "Offer a brief, grounded somatic reset protocol. "
        "Be direct. Be human. No generic wellness language."
    )
    result = call_gemini(prompt, context)
    return {"result": result}


@app.get("/api/corpus")
async def get_corpus():
    """
    Return full corpus context as JSON for inspection.
    """
    try:
        corpus = get_full_corpus()
        summary = {
            doc_key: {
                "chars": len(data.get("content", "")),
                "fetched_at": data.get("fetched_at"),
                "error": data.get("error"),
            }
            for doc_key, data in corpus.items()
        }
        return JSONResponse({"status": "ok", "docs": summary})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
