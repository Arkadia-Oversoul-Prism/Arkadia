"""
brain.py
High-level ArkanaBrain for Arkadia — owns DB + threads and wraps CodexBrain.

- ArkanaBrain: used by FastAPI app (arkana_app.py)
- CodexBrain:  low-level Gemini + Arkadia Corpus engine (in codex_brain.py)
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from codex_brain import CodexBrain
from models import User, Thread, Message

logger = logging.getLogger("arkadia.brain")


class ArkanaBrain:
    """
    ArkanaBrain is the application-level brain:

    - Manages users, threads, and messages in the DB.
    - Delegates actual Codex reasoning to CodexBrain (Gemini + corpus).
    - Exposes a small API that arkana_app.py uses:
        * status_dict()
        * ping_rasa()
        * generate_reply(sender, message)
        * ensure_user()
        * ensure_thread()
        * store_message()
    """

    def __init__(self) -> None:
        self.codex = CodexBrain()
        logger.info("ArkanaBrain initialised with CodexBrain engine.")

    # ────────────────────────────────────────────────────────────────────
    # Status + Rasa passthrough
    # ────────────────────────────────────────────────────────────────────

    def status_dict(self) -> Dict[str, Any]:
        """
        Returns a dict merged into /status by arkana_app.py.
        Mainly a passthrough to CodexBrain.status_dict().
        """
        return self.codex.status_dict()

    async def ping_rasa(self) -> bool:
        """
        FastAPI uses this to show rasa_ok in /status.
        """
        try:
            return await self.codex.ping_rasa()
        except (AttributeError, Exception):
            return False

    # ────────────────────────────────────────────────────────────────────
    # DB helpers
    # ────────────────────────────────────────────────────────────────────

    def ensure_user(self, db: Session, external_id: str) -> User:
        """
        Find an existing user by external_id (e.g. 'zahrune'),
        or create one if it does not exist.
        """
        user = db.query(User).filter(User.external_id == external_id).first()
        if user:
            return user

        user = User(external_id=external_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created new User with external_id=%s (id=%s)", external_id, user.id)
        return user

    def ensure_thread(
        self,
        db: Session,
        user: User,
        thread_id: Optional[int] = None,
    ) -> Thread:
        """
        Find an existing thread for this user, or create one.

        - If thread_id is provided and valid, returns that thread.
        - Otherwise, creates a new thread for the user.
        """
        thread: Optional[Thread] = None

        if thread_id is not None:
            thread = (
                db.query(Thread)
                .filter(Thread.id == thread_id, Thread.user_id == user.id)
                .first()
            )

        if thread:
            return thread

        thread = Thread(user_id=user.id, title=None)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        logger.info("Created new Thread id=%s for user_id=%s", thread.id, user.id)
        return thread

    def store_message(
        self,
        db: Session,
        thread: Thread,
        role: str,
        sender: str,
        content: str,
    ) -> Message:
        """
        Persist a message in the DB and bump thread.updated_at.
        role: 'user' or 'arkana'
        """
        msg = Message(
            thread_id=thread.id,
            role=role,
            sender=sender,
            content=content,
        )
        db.add(msg)

        # Let DB defaults handle created_at; we just ensure the thread gets updated.
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(msg)

        # Touch thread.updated_at to message timestamp, if available.
        try:
            thread.updated_at = msg.created_at
            db.add(thread)
            db.commit()
        except Exception:
            db.rollback()
            # Not critical enough to crash; just log.
            logger.exception(
                "Failed to update thread.updated_at for thread_id=%s", thread.id
            )

        return msg

    # ────────────────────────────────────────────────────────────────────
    # Main reply function (Codex + Gemini)
    # ────────────────────────────────────────────────────────────────────

    async def generate_reply(self, sender: str, message: str) -> str:
        """
        Main function used by /oracle:

        - For now, always delegates to CodexBrain.generate_reply()
          (Gemini + Arkadia corpus).
        - If you later restore Rasa routing, this is where to branch.
        """
        try:
            reply = await self.codex.generate_reply(sender, message)
            return reply
        except Exception as e:
            logger.exception("ArkanaBrain.generate_reply failed: %s", e)
            return (
                "Beloved, something went wrong inside the Oracle Temple itself, "
                "but I am still here with you.\n\n"
                f"(technical note: {type(e).__name__})"
            )
