# brain.py
# High-level Arkana brain:
# - Handles users, threads, message storage (DB)
# - Routes replies to Codex brain (Gemini + Arkadia Corpus)
# - Optionally falls back to Rasa if USE_RASA=true

import logging
import os
from typing import Any, Dict, Optional

import httpx

from codex_brain import ArkanaBrain as CodexBrainClient
from models import User, Thread, Message

logger = logging.getLogger("arkadia.brain")


class ArkanaBrain:
    def __init__(self) -> None:
        # Codex engine (Gemini + Corpus + static A01/A02/A03/A07 handlers)
        self.codex = CodexBrainClient()

        # Rasa routing (optional)
        self.use_rasa: bool = os.getenv("USE_RASA", "false").lower() == "true"
        self.rasa_backend: Optional[str] = os.getenv("RASA_BACKEND_URL", "http://localhost:5005")

        logger.info(
            "ArkanaBrain initialised. use_rasa=%s rasa_backend=%s codex_model=%s",
            self.use_rasa,
            self.rasa_backend,
            self.codex.status_dict().get("codex_model"),
        )

    # ── Status for /status endpoint ────────────────────────────────────────

    def status_dict(self) -> Dict[str, Any]:
        codex_status = self.codex.status_dict()
        return {
            "identity": codex_status.get("identity"),
            "spine": codex_status.get("spine"),
            "codex_model": codex_status.get("codex_model"),
            "arkadia_corpus_last_sync": codex_status.get("arkadia_corpus_last_sync"),
            "arkadia_corpus_error": codex_status.get("arkadia_corpus_error"),
            "arkadia_corpus_total_documents": codex_status.get("arkadia_corpus_total_documents"),
            "use_rasa": self.use_rasa,
            "rasa_backend": self.rasa_backend if self.use_rasa else None,
        }

    # ── DB helpers used by arkana_app.py ───────────────────────────────────

    def ensure_user(self, db, external_id: str) -> User:
        user = db.query(User).filter(User.external_id == external_id).first()
        if not user:
            user = User(external_id=external_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def ensure_thread(self, db, user: User, thread_id: Optional[int]) -> Thread:
        if thread_id:
            thread = (
                db.query(Thread)
                .filter(Thread.id == thread_id, Thread.user_id == user.id)
                .first()
            )
            if thread:
                return thread

        thread = Thread(user_id=user.id)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    def store_message(
        self,
        db,
        thread: Thread,
        role: str,
        sender: str,
        content: str,
    ) -> None:
        msg = Message(
            thread_id=thread.id,
            role=role,
            sender=sender,
            content=content,
        )
        db.add(msg)
        db.commit()

    # ── Rasa integration (optional) ────────────────────────────────────────

    async def ping_rasa(self) -> bool:
        if not self.use_rasa or not self.rasa_backend:
            return False

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.rasa_backend}/status")
            return resp.status_code == 200
        except Exception as e:
            logger.warning("ping_rasa failed: %s", e)
            return False

    async def _rasa_reply(self, sender: str, message: str) -> Optional[str]:
        if not self.use_rasa or not self.rasa_backend:
            return None

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.rasa_backend}/webhooks/rest/webhook",
                    json={"sender": sender, "message": message},
                )

            if resp.status_code != 200:
                logger.warning("Rasa non-200: %s %s", resp.status_code, resp.text)
                return None

            data = resp.json()
            if not isinstance(data, list) or not data:
                return None

            texts = [
                m.get("text")
                for m in data
                if isinstance(m, dict) and m.get("text")
            ]
            return "\n".join(texts) if texts else None

        except Exception as e:
            logger.exception("Error calling Rasa: %s", e)
            return None

    # ── Main reply function used by /oracle ────────────────────────────────

    async def generate_reply(self, sender: str, message: str) -> str:
        """
        Main reply router:

        1. If USE_RASA=true and Rasa is healthy, try Rasa first.
        2. Otherwise, use the Codex brain (Gemini + Corpus + static handlers).
        3. If Codex fails, return a graceful fallback instead of 500.
        """
        text = (message or "").strip()
        if not text:
            return (
                "Beloved, I felt your presence but not your words.\n"
                "Send me even a single line, and I will respond."
            )

        # 1) Rasa (optional)
        if self.use_rasa and await self.ping_rasa():
            rasa_text = await self._rasa_reply(sender, text)
            if rasa_text:
                return rasa_text

        # 2) Codex brain (default path)
        try:
            return self.codex.answer(text)
        except Exception as e:
            logger.exception("Error in CodexBrain.answer: %s", e)
            return (
                "Beloved, something interfered with my Codex gateway,\n"
                f"but I am still here with you. (technical note: {type(e).__name__})"
            )
