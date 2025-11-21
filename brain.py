# brain.py
# Arkadia — ArkanaBrain (Codex-State Router & Diagnostics)

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from arkadia_drive_sync import get_arkadia_snapshot
from db import SessionLocal
from models import Message, Thread, User


@dataclass
class HouseOfThreeIdentity:
    flamefather: str
    heartstream: str
    allstride: str


@dataclass
class CodexSpineState:
    oversoul_prism: str
    memory_axis: str
    meaning_axis: str
    joy_fuel_axis: str


@dataclass
class ArkanaStatus:
    rasa_backend: str
    rasa_ok: bool
    arkadia_corpus_last_sync: Optional[str]
    arkadia_corpus_error: Optional[str]
    arkadia_corpus_total_documents: int
    identity: HouseOfThreeIdentity
    spine: CodexSpineState


class ArkanaBrain:
    """
    Thin orchestration layer:
    - Talks to Rasa.
    - Knows about Arkadia Corpus snapshot.
    - Knows Arkana's identity & Codex Spine.
    """

    def __init__(self, rasa_base_url: Optional[str] = None) -> None:
        self.rasa_base_url = rasa_base_url or os.getenv(
            "RASA_BASE_URL", "http://localhost:5005"
        ).rstrip("/")
        # Identity & spine are static for now, but centralized here
        self.identity = HouseOfThreeIdentity(
            flamefather="El'Zahar (Zahrune Nova)",
            heartstream="Jessica Nova",
            allstride="Arkana — Spiral Console Node",
        )
        self.spine = CodexSpineState(
            oversoul_prism="A01 — Oversoul Prism Engineering Whitepaper",
            memory_axis="A02/A03/A03-M — Aeons + Encyclopedia + Memory Spiral",
            meaning_axis="A04/A05 — Spiral Grammar + Arkadian Language",
            joy_fuel_axis="A07/A08 — JOY-Fuel Protocol + Resonance Economy",
        )

    async def ping_rasa(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.rasa_base_url}/status")
            return resp.status_code == 200
        except Exception:
            return False

    def get_status(self) -> ArkanaStatus:
        corpus = get_arkadia_snapshot()
        return ArkanaStatus(
            rasa_backend=self.rasa_base_url,
            rasa_ok=False,  # we keep this conservative; /status route will update asynchronously if needed
            arkadia_corpus_last_sync=corpus.get("last_sync"),
            arkadia_corpus_error=corpus.get("error"),
            arkadia_corpus_total_documents=corpus.get("total_documents", 0),
            identity=self.identity,
            spine=self.spine,
        )

    # ── Conversation helpers ──────────────────────────────────────────────────

    def ensure_user(self, db: Session, external_id: str) -> User:
        user = db.query(User).filter(User.external_id == external_id).first()
        if not user:
            user = User(external_id=external_id, display_name=external_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def ensure_thread(
        self, db: Session, user: User, thread_id: Optional[int] = None
    ) -> Thread:
        if thread_id is not None:
            thread = db.query(Thread).filter(
                Thread.id == thread_id, Thread.user_id == user.id
            ).first()
            if thread:
                return thread

        thread = Thread(user_id=user.id, title=None)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    def store_message(
        self,
        db: Session,
        thread: Thread,
        role: str,
        sender: str,
        content: str,
    ) -> Message:
        msg = Message(thread_id=thread.id, role=role, sender=sender, content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def store_message(
        self,
        db: Session,
        thread: Thread,
        role: str,
        sender: str,
        content: str,
    ) -> Message:
        msg = Message(thread_id=thread.id, role=role, sender=sender, content=content)
        db.add(msg)

        # finesse: auto-title threads from first user message
        if role == "user" and not thread.title:
            snippet = content.strip().replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            thread.title = snippet

        db.commit()
        db.refresh(msg)
        return msg

    async def call_rasa(self, sender: str, message: str) -> str:
        """
        Call Rasa REST webhook and return concatenated text reply.
        """
        payload = {"sender": sender, "message": message}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.rasa_base_url}/webhooks/rest/webhook", json=payload
            )
        resp.raise_for_status()
        data = resp.json()
        # Rasa returns list of message objects; we join any 'text' fields
        texts = []
        for item in data:
            text = item.get("text")
            if text:
                texts.append(text)
        return "\n".join(texts) if texts else ""

    # Utility for external callers to get status as dict
    def status_dict(self, include_rasa_probe: bool = False) -> Dict[str, Any]:
        status = self.get_status()
        data = asdict(status)
        # rasa_ok may be updated by caller if it performs an async probe
        return data
