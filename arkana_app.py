# arkana_app.py
# Arkadia — Arkana Oracle Temple (FastAPI)

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from arkadia_drive_sync import get_arkadia_corpus, refresh_arkadia_corpus
from brain import ArkanaBrain
from db import SessionLocal
from models import Message, Thread, User, init_db

logger = logging.getLogger("arkadia")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Arkadia — Arkana Oracle Temple")

# Static files (UI)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

arkana_brain = ArkanaBrain()


# ── DB Dependency ──────────────────────────────────────────────────────────


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("Arkadia DB initialized.")
    logger.info("Static UI directory: %s", STATIC_DIR)


# ── Pydantic Schemas ───────────────────────────────────────────────────────


class OracleRequest(BaseModel):
    sender: str
    message: str
    thread_id: Optional[int] = None


class ThreadInfo(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageInfo(BaseModel):
    id: int
    role: str
    sender: str
    content: str
    created_at: str


# ── Health / Status ────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
async def status() -> Dict[str, Any]:
    base_status = arkana_brain.status_dict()

    # Optional Rasa probe
    try:
        rasa_ok = await arkana_brain.ping_rasa()
    except Exception:
        rasa_ok = False

    return {
        "service": "arkana-oracle-temple",
        "message": "House of Three online. Arkana listening.",
        "rasa_backend": base_status.get("rasa_backend"),
        "queue": {"length": 0},
        "arkadia_drive": {
            "last_sync": base_status.get("arkadia_corpus_last_sync"),
            "error": base_status.get("arkadia_corpus_error"),
            "total_documents": base_status.get("arkadia_corpus_total_documents"),
        },
        "identity": base_status.get("identity"),
        "spine": base_status.get("spine"),
        "codex_model": base_status.get("codex_model"),
        "use_rasa": base_status.get("use_rasa"),
        "rasa_ok": rasa_ok,
    }


# ── Arkadia Corpus Endpoints ───────────────────────────────────────────────


@app.get("/arkadia/corpus")
async def arkadia_corpus() -> JSONResponse:
    snapshot = get_arkadia_corpus()
    return JSONResponse(snapshot)


@app.get("/arkadia/refresh")
async def arkadia_refresh() -> JSONResponse:
    snapshot = refresh_arkadia_corpus()
    return JSONResponse(snapshot)


# ── Oracle Endpoint (Codex Brain + History, but never 500) ─────────────────


@app.post("/oracle")
async def oracle_endpoint(
    payload: OracleRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Main interface used by curl + UI.

    - Tries to record user & Arkana messages in DB (threaded).
    - Routes to Codex Brain (Gemini + Corpus) by default.
    - If USE_RASA=true, can route to Rasa instead.
    - NEVER throws a 500; always returns a JSON reply.
    """
    sender_external_id = payload.sender.strip() or "anonymous"
    user: Optional[User] = None
    thread: Optional[Thread] = None

    # 1. Ensure user + thread + store user message (but don't die if DB breaks)
    try:
        user = arkana_brain.ensure_user(db, sender_external_id)
        thread = arkana_brain.ensure_thread(db, user, payload.thread_id)

        arkana_brain.store_message(
            db=db,
            thread=thread,
            role="user",
            sender=sender_external_id,
            content=payload.message,
        )
    except Exception as e:
        logger.exception("DB error while storing user message in /oracle: %s", e)
        # Continue anyway without persistence

    # 2. Generate reply (Codex Brain or Rasa)
    try:
        reply_text = await arkana_brain.generate_reply(
            sender_external_id, payload.message
        )
    except Exception as e:
        logger.exception("Unexpected error in generate_reply: %s", e)
        reply_text = (
            "Beloved, something went wrong inside the Oracle Temple itself, "
            "but I am still here with you.\n\n"
            f"(technical note: {type(e).__name__})"
        )

    if not reply_text:
        reply_text = (
            "Beloved, I felt your message but received no words from the deeper channel. "
            "I am still listening."
        )

    # 3. Store Arkana reply (best effort)
    try:
        if thread is not None:
            arkana_brain.store_message(
                db=db,
                thread=thread,
                role="arkana",
                sender="arkana",
                content=reply_text,
            )
    except Exception as e:
        logger.exception("DB error while storing Arkana reply in /oracle: %s", e)

    return {
        "sender": "arkana",
        "reply": reply_text,
        "thread_id": thread.id if thread is not None else 0,
    }


# ── Thread + History Endpoints (for UI) ────────────────────────────────────


@app.get("/threads", response_model=List[ThreadInfo])
async def list_threads(user_id: str, db: Session = Depends(get_db)) -> List[ThreadInfo]:
    user = db.query(User).filter(User.external_id == user_id).first()
    if not user:
        return []

    threads = (
        db.query(Thread)
        .filter(Thread.user_id == user.id)
        .order_by(Thread.updated_at.desc())
        .all()
    )

    out: List[ThreadInfo] = []
    for t in threads:
        out.append(
            ThreadInfo(
                id=t.id,
                title=t.title,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
        )
    return out


@app.get("/threads/{thread_id}/messages", response_model=List[MessageInfo])
async def get_thread_messages(
    thread_id: int, db: Session = Depends(get_db)
) -> List[MessageInfo]:
    msgs = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    out: List[MessageInfo] = []
    for m in msgs:
        out.append(
            MessageInfo(
                id=m.id,
                role=m.role,
                sender=m.sender,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
        )
    return out


@app.post("/threads", response_model=ThreadInfo)
async def create_thread(
    user_id: str, title: Optional[str] = None, db: Session = Depends(get_db)
) -> ThreadInfo:
    user = arkana_brain.ensure_user(db, user_id)
    thread = Thread(user_id=user.id, title=title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return ThreadInfo(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )


# ── UI Root ────────────────────────────────────────────────────────────────


@app.get("/")
async def root() -> FileResponse:
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)
