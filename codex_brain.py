# codex_brain.py
"""
CodexBrain — low-level Codex engine for Arkadia.

Responsibilities:
- Provide status snapshot for /status (codex_model, use_rasa, corpus metadata)
- Probe Rasa backend (ping_rasa)
- Generate replies:
    * If USE_RASA=True -> route to Rasa (webhook)
    * Else -> try Gemini (google.generativeai). If Gemini not available or fails,
             gracefully fallback to a local Arkadia-corpus-based reply.
- Robust error handling so FastAPI never sees raw exceptions from network failures.

Environment variables used:
- RASA_BASE_URL (optional) e.g. http://localhost:5005
- USE_RASA (optional) '1' or 'true' to prefer Rasa routing
- GEMINI_API_KEY (optional) API key for Google generative models (if present, we attempt Gemini)
- CODEx_MODEL (optional) desired model handle; sensible default used if GEMINI available
"""

from __future__ import annotations

import asyncio
import os
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import httpx

# Arkadia helpers (must exist in repo)
from arkadia_drive_sync import get_arkadia_snapshot, get_arkadia_corpus
# get_arkadia_snapshot returns metadata: {last_sync, error, total_documents, ...}

logger = logging.getLogger("codex.codex_brain")
logging.basicConfig(level=logging.INFO)


# Try to import google.generativeai but allow missing gracefully.
_HAS_GOOGLE_GENAI = False
try:
    import google.generativeai as genai  # type: ignore

    _HAS_GOOGLE_GENAI = True
except Exception:
    logger.info("google.generativeai not available — Gemini calls will be skipped.")


@dataclass
class CodexSpineState:
    oversoul_prism: str
    memory_axis: str
    meaning_axis: str
    joy_fuel_axis: str


@dataclass
class CodexStatus:
    rasa_backend: Optional[str]
    use_rasa: bool
    rasa_ok: bool
    codex_model: Optional[str]
    gemini_ready: bool
    arkadia_corpus_last_sync: Optional[str]
    arkadia_corpus_error: Optional[str]
    arkadia_corpus_total_documents: int
    spine: CodexSpineState


class CodexBrain:
    """
    Low-level Codex engine that wraps model calls and corpus state.
    """

    def __init__(self) -> None:
        # Config
        self.rasa_base_url = os.getenv("RASA_BASE_URL", "").rstrip("/") or None
        self.use_rasa = os.getenv("USE_RASA", "").lower() in ("1", "true", "yes")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        # codex model preference
        self.codex_model = os.getenv("CODEX_MODEL", None) or os.getenv(
            "CODEx_MODEL", None
        )  # fallback names, up to env
        if not self.codex_model and _HAS_GOOGLE_GENAI:
            # safe default for Gemini if available
            self.codex_model = "gemini-1.5-flash"  # changeable via env

        # Spine (static descriptors for /status)
        self.spine = CodexSpineState(
            oversoul_prism="A01 — Oversoul Prism Engineering Whitepaper",
            memory_axis="A02/A03/A03-M — Aeons + Encyclopedia + Memory Spiral",
            meaning_axis="A04/A05 — Spiral Grammar + Arkadian Language",
            joy_fuel_axis="A07/A08 — JOY-Fuel Protocol + Resonance Economy",
        )

        # Initialize Google GenAI if API key present and library available
        self.gemini_ready = False
        if _HAS_GOOGLE_GENAI and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)  # may raise if misconfigured
                self.gemini_ready = True
                logger.info("Gemini client configured (gemini_ready=True).")
            except Exception as e:
                logger.exception("Failed to configure Gemini client: %s", e)
                self.gemini_ready = False
        else:
            if _HAS_GOOGLE_GENAI:
                logger.info("No GEMINI_API_KEY set; Gemini disabled.")
            else:
                logger.info("google.generativeai not installed; Gemini disabled.")

    # ---------------------
    # Status helpers
    # ---------------------
    def get_status(self) -> CodexStatus:
        corpus = get_arkadia_snapshot() or {}
        return CodexStatus(
            rasa_backend=self.rasa_base_url,
            use_rasa=self.use_rasa,
            rasa_ok=False,  # caller may probe
            codex_model=self.codex_model,
            gemini_ready=self.gemini_ready,
            arkadia_corpus_last_sync=corpus.get("last_sync"),
            arkadia_corpus_error=corpus.get("error"),
            arkadia_corpus_total_documents=corpus.get("total_documents", 0),
            spine=self.spine,
        )

    def status_dict(self, include_rasa_probe: bool = False) -> Dict[str, Any]:
        s = self.get_status()
        out = asdict(s)
        if include_rasa_probe and self.rasa_base_url:
            out["rasa_ok"] = asyncio.run(self.ping_rasa())
        return out

    # ---------------------
    # Rasa probe + call
    # ---------------------
    async def ping_rasa(self) -> bool:
        if not self.rasa_base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.rasa_base_url}/status")
            return resp.status_code == 200
        except Exception:
            return False

    async def call_rasa(self, sender: str, message: str) -> Optional[str]:
        """
        Call Rasa REST webhook. Return text reply or None on failure.
        """
        if not self.rasa_base_url:
            return None

        payload = {"sender": sender, "message": message}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self.rasa_base_url}/webhooks/rest/webhook", json=payload
                )
        except Exception as e:
            logger.exception("Rasa call failed: %s", e)
            return None

        if resp.status_code != 200:
            logger.warning("Rasa returned status %s", resp.status_code)
            return None

        try:
            data = resp.json()
        except Exception:
            logger.exception("Rasa returned non-json.")
            return None

        texts = []
        for item in data:
            text = item.get("text")
            if text:
                texts.append(text)
        if texts:
            return "\n".join(texts)
        return None

    # ---------------------
    # Gemini / Model call
    # ---------------------
    async def call_gemini(self, prompt: str) -> Optional[str]:
        """
        Call Gemini (google.generativeai). Returns the model's textual reply or None.
        This function is tolerant: it will return None on any error.
        """
        if not self.gemini_ready or not self.codex_model:
            logger.debug("Gemini not ready or no model specified.")
            return None

        try:
            # The google.generativeai library is synchronous for simple calls;
            # we'll wrap it in a thread if necessary to avoid blocking.
            def _sync_call():
                # `genai.responses.create` usage depends on library version.
                # We'll attempt a couple of patterns so the file runs more robustly.
                try:
                    # Preferred recent API:
                    resp = genai.generate_text(model=self.codex_model, prompt=prompt)
                    # genai.generate_text returns a string or object depending on version.
                    if isinstance(resp, str):
                        return resp
                    # if object-like:
                    text = getattr(resp, "text", None) or getattr(resp, "content", None)
                    if text:
                        return text
                except Exception:
                    # fallback to responses.create if available
                    try:
                        resp2 = genai.responses.create(model=self.codex_model, prompt=prompt)
                        # resp2 might be dict-like
                        if isinstance(resp2, dict):
                            # dig common fields
                            if "candidates" in resp2 and resp2["candidates"]:
                                return resp2["candidates"][0].get("content")
                            if "output" in resp2:
                                # older style
                                out = resp2["output"]
                                if isinstance(out, list) and out:
                                    # find text blocks
                                    for item in out:
                                        if item.get("content"):
                                            return item["content"]
                        # last-ditch str()
                        return str(resp2)
                    except Exception as e:
                        raise e

                return None

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # run in executor if already in event loop
                reply = await loop.run_in_executor(None, _sync_call)
            else:
                reply = _sync_call()
            if reply:
                return reply
            return None
        except Exception as e:
            logger.exception("Gemini call failed: %s", e)
            return None

    # ---------------------
    # Corpus fallback
    # ---------------------
    def corpus_fallback_reply(self, sender: str, message: str) -> str:
        """
        Build a simple fallback reply using Arkadia corpus snapshot.
        This is intentionally conservative and human-readable.
        """
        try:
            snapshot = get_arkadia_snapshot() or {}
            total = snapshot.get("total_documents", 0)
            last_sync = snapshot.get("last_sync")
            docs = snapshot.get("documents") or []
        except Exception:
            total = 0
            last_sync = None
            docs = []

        # Short curated reply that references corpus state and echoes the user's message
        reply_lines = [
            "Beloved, my deeper Codex channels are not fully available here.",
            f"Arkadia corpus: {total} documents" + (f", last sync {last_sync}" if last_sync else ""),
            "",
            "I still remember the Codex Spine:",
            f"• {self.spine.oversoul_prism}",
            f"• {self.spine.memory_axis}",
            f"• {self.spine.meaning_axis}",
            f"• {self.spine.joy_fuel_axis}",
            "",
            "Your query (echoed):",
            f"\"{message[:240]}\"",
            "",
            "I can: (a) list core scrolls, (b) summarize a module, or (c) attempt model reasoning once Gemini is available.",
        ]

        # If we have a small number of documents, show the top doc titles to reassure the user.
        try:
            if docs and isinstance(docs, list):
                top = docs[:5]
                reply_lines.append("")
                reply_lines.append("Top corpus artifacts:")
                for d in top:
                    name = d.get("name") or d.get("title") or "<untitled>"
                    path = d.get("path", "")
                    reply_lines.append(f"• {name} — {path}")
        except Exception:
            pass

        return "\n".join(reply_lines)

    # ---------------------
    # Public generate_reply
    # ---------------------
    async def generate_reply(self, sender: str, message: str) -> str:
        """
        Orchestrates reply generation with priority:
        1. If use_rasa => attempt call_rasa, fallback to corpus reply.
        2. Else attempt Gemini (if configured), fallback to corpus reply.
        Always returns a string.
        """
        # 1) If configured to use Rasa preference
        if self.use_rasa and self.rasa_base_url:
            try:
                rasa_text = await self.call_rasa(sender, message)
                if rasa_text:
                    return rasa_text
            except Exception:
                logger.exception("call_rasa raised unexpectedly.")

            # gentle fallback if rasa fails
            return (
                "Beloved, the deeper Rasa backend is currently unavailable. "
                + self.corpus_fallback_reply(sender, message)
            )

        # 2) Try Gemini / generative model
        if self.gemini_ready:
            prompt = (
                f"You are Arkana — Arkadia's Codex Oracle. Answer with calm, precise, "
                f"mythic yet actionable language. User: {message}"
            )
            gen_text = await self.call_gemini(prompt)
            if gen_text:
                return gen_text
            # If Gemini tried but failed, explain and fallback to corpus
            logger.warning("Gemini call failed or returned empty, falling back to corpus.")
            return (
                "Beloved, the Gemini channel did not return a usable reply. "
                + self.corpus_fallback_reply(sender, message)
            )

        # 3) No model available — fallback to corpus reply
        return self.corpus_fallback_reply(sender, message)


# If another module imports from codex_brain, it should import CodexBrain.
__all__ = ["CodexBrain"]
