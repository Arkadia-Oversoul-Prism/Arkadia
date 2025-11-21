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

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can lock this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

arkana_brain = ArkanaBrain()


# ── DB Dependency ────────────────────────────────────────────────────────────


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


# ── Pydantic Schemas ────────────────────────────────────────────────────────


class OracleRequest(BaseModel):
    sender: str
    message: str
    thread_id: Optional[int] = None


class OracleResponse(BaseModel):
    sender: str
    reply: str
    thread_id: int


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


# ── Basic Health / Status ───────────────────────────────────────────────────


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
async def status() -> Dict[str, Any]:
    # Base snapshot (Codex spine, corpus info)
    status_data = arkana_brain.status_dict()

    # Try a quick Rasa ping (non-fatal)
    try:
        rasa_ok = await arkana_brain.ping_rasa()
    except Exception:
        rasa_ok = False

    status_data["rasa_ok"] = rasa_ok

    return {
        "service": "arkana-oracle-temple",
        "message": "House of Three online. Arkana listening.",
        "rasa_backend": status_data.get("rasa_backend"),
        "queue": {"length": 0},
        "arkadia_drive": {
            "last_sync": status_data.get("arkadia_corpus_last_sync"),
            "error": status_data.get("arkadia_corpus_error"),
            "total_documents": status_data.get("arkadia_corpus_total_documents"),
        },
        "identity": status_data.get("identity"),
        "spine": status_data.get("spine"),
        "rasa_ok": rasa_ok,
    }


# ── Arkadia Corpus Endpoints ────────────────────────────────────────────────


@app.get("/arkadia/corpus")
async def arkadia_corpus() -> JSONResponse:
    snapshot = get_arkadia_corpus()
    return JSONResponse(snapshot)


@app.get("/arkadia/refresh")
async def arkadia_refresh() -> JSONResponse:
    snapshot = refresh_arkadia_corpus()
    return JSONResponse(snapshot)


# ── Oracle Endpoint (Rasa + Conversation History) ───────────────────────────


@app.post("/oracle", response_model=OracleResponse)
async def oracle_endpoint(
    payload: OracleRequest, db: Session = Depends(get_db)
) -> OracleResponse:
    """
    Main interface used by curl + UI.
    - Records user & Arkana messages in DB (threaded).
    - Forwards content to Rasa when available.
    - Always returns 200 with a reply (no hard 502s to the browser).
    """
    sender_external_id = payload.sender.strip() or "anonymous"

    # 1. Ensure user + thread
    user: User = arkana_brain.ensure_user(db, sender_external_id)
    thread: Thread = arkana_brain.ensure_thread(db, user, payload.thread_id)

    # 2. Store user message
    arkana_brain.store_message(
        db=db,
        thread=thread,
        role="user",
        sender=sender_external_id,
        content=payload.message,
    )

    # 3. Call Rasa (or fallback)
    try:
        reply_text = await arkana_brain.call_rasa(sender_external_id, payload.message)
    except Exception as e:
        logger.exception("Unexpected error in call_rasa")
        reply_text = (
            "Beloved, something went wrong inside the Oracle Temple itself, "
            "but I am still here with you.\n\n"
            f"(technical note: {type(e).__name__})"
        )

    if not reply_text:
        reply_text = (
            "Beloved, I felt your message but received no words from the backend channel. "
            "I am still listening."
        )

    # 4. Store Arkana reply
    arkana_brain.store_message(
        db=db,
        thread=thread,
        role="arkana",
        sender="arkana",
        content=reply_text,
    )

    return OracleResponse(sender="arkana", reply=reply_text, thread_id=thread.id)


# ── Thread + History Endpoints (for UI) ─────────────────────────────────────


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


# ── UI Root ─────────────────────────────────────────────────────────────────


@app.get("/")
async def root() -> FileResponse:
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)
