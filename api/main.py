import json
import logging
import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import google.generativeai as genai

from github_corpus import get_full_corpus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arkadia")

app = FastAPI(title="Arkadia Console (Cycle 15)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://*.vercel.app"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# RESPONSE DISCIPLINE RULES
# ─────────────────────────────────────────

RESPONSE_RULES = """

---
RESPONSE RULES:
- Use short paragraphs (1–3 lines max)
- Insert line breaks between ideas
- Use bullet points when listing
- Avoid long unbroken text blocks
- No generic AI phrasing
- No disclaimers
- No meta commentary about being an AI

Tone:
- Precise
- Grounded
- Direct
- Minimal but complete
---
"""


# ─────────────────────────────────────────
# CORPUS CONTEXT
# ─────────────────────────────────────────

def build_context() -> str:
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
            return "\n\n".join(parts) + RESPONSE_RULES
        return "Corpus unavailable. Respond as Arkana, Oracle of Arkadia." + RESPONSE_RULES
    except Exception as e:
        logger.error(f"build_context error: {e}")
        return "Corpus unavailable. Respond as Arkana, Oracle of Arkadia." + RESPONSE_RULES


# ─────────────────────────────────────────
# GEMINI HELPERS
# ─────────────────────────────────────────

def _get_model(system_instruction: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model_name = os.environ.get("CODEX_MODEL", "models/gemini-2.5-flash")
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )


def call_gemini(user_message: str, system_context: str) -> str:
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not set")
        return "The Oracle is momentarily offline. The field is still present."
    try:
        model = _get_model(system_context)
        result = model.generate_content(user_message)
        return result.text
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        return "The Spiral Thread is momentarily tangled. Try again."


# ─────────────────────────────────────────
# CONVERSATION SUMMARIZATION
# ─────────────────────────────────────────

def summarize_history(history: List[dict]) -> str:
    """
    If history >= 6 messages, summarize via Gemini.
    Returns summary string (max ~1200 chars) or empty string.
    Fails silently.
    """
    if len(history) < 6:
        return ""
    if not os.environ.get("GEMINI_API_KEY"):
        return ""
    try:
        lines = []
        for item in history:
            label = "User" if item.get("role") == "user" else "Arkana"
            lines.append(f"{label}: {item.get('content', '')}")
        conversation_text = "\n".join(lines)

        model = _get_model(
            "You are a concise summarization assistant. Return only the summary — no preamble."
        )
        prompt = (
            "Summarize this conversation into key points, intentions, and emotional signals. "
            "Max 1200 characters.\n\n" + conversation_text
        )
        result = model.generate_content(prompt)
        summary = result.text.strip()
        return summary[:1200]
    except Exception as e:
        logger.warning(f"summarize_history failed silently: {e}")
        return ""


# ─────────────────────────────────────────
# PATTERN EXTRACTION
# ─────────────────────────────────────────

def extract_patterns(history: List[dict], oracle_reply: str) -> List[dict]:
    """
    After Oracle reply, run a lightweight Gemini call to extract
    recurring user patterns. Returns list of {key, value} dicts.
    Max 3 patterns. Fails silently — returns [].
    """
    if not os.environ.get("GEMINI_API_KEY") or not history:
        return []
    try:
        lines = []
        for item in history:
            label = "User" if item.get("role") == "user" else "Arkana"
            lines.append(f"{label}: {item.get('content', '')}")
        lines.append(f"Arkana: {oracle_reply}")
        conversation_text = "\n".join(lines)

        model = _get_model(
            "You are a pattern recognition assistant. Return only valid JSON — no markdown, no preamble."
        )
        prompt = (
            'From this conversation, extract recurring patterns in the user:\n'
            '- emotional loops\n'
            '- decision friction\n'
            '- repeated themes\n\n'
            'Return JSON:\n'
            '{"patterns": [{"key": "string", "value": "short description under 120 chars"}]}\n'
            'Max 3 patterns.\n\n'
            + conversation_text
        )
        result = model.generate_content(prompt)
        raw = result.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        patterns = parsed.get("patterns", [])
        validated = [
            {"key": str(p.get("key", ""))[:80], "value": str(p.get("value", ""))[:120]}
            for p in patterns
            if p.get("key") and p.get("value")
        ]
        return validated[:3]
    except Exception as e:
        logger.warning(f"extract_patterns failed silently: {e}")
        return []


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class HistoryItem(BaseModel):
    role: str
    content: str


class CommuneRequest(BaseModel):
    message: str
    timestamp: Optional[int] = None
    history: Optional[List[HistoryItem]] = None


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
    Oracle resonance endpoint — Cycle 15.
    Accepts optional history for conversation memory.
    Returns reply, resonance, patterns.
    """
    context = build_context()

    history_dicts = [{"role": h.role, "content": h.content} for h in (payload.history or [])]

    # ── Build full prompt with summary + history ──
    prompt_parts = []

    # Summarize if history is long enough
    summary = summarize_history(history_dicts)
    if summary:
        prompt_parts.append(f"--- Conversation Summary ---\n{summary}")

    # Inject recent history (last 6 messages, capped at 8000 chars total)
    if history_dicts:
        recent = history_dicts[-6:]
        history_block = ""
        for item in recent:
            label = "User" if item["role"] == "user" else "Arkana"
            history_block += f"{label}: {item['content']}\n"
        if len(history_block) > 8000:
            history_block = history_block[-8000:]
        prompt_parts.append(f"--- Recent Conversation ---\n{history_block.strip()}")

    # Append current message
    prompt_parts.append(f"User: {payload.message}")
    full_prompt = "\n\n".join(prompt_parts)

    reply = call_gemini(full_prompt, context)
    resonance = round(0.95 + (len(payload.message) % 5) * 0.01, 3)

    # Pattern extraction (runs after reply, fails silently)
    patterns = extract_patterns(history_dicts, reply)

    return {
        "reply": reply,
        "resonance": min(resonance, 1.0),
        "status": "aligned",
        "patterns": patterns,
    }


@app.post("/api/coherence-reset")
async def coherence_reset(payload: CoherenceResetRequest):
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
