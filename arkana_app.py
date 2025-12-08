# arkana_app.py
# Arkadia — Arkana Oracle Temple (FastAPI)
"""
Defensive, single-file FastAPI app for Arkadia that:
- Uses refresh_arkadia_cache() + get_corpus_context(...) from arkadia_drive_sync
- Uses ArkanaBrain for oracle replies
- Works even if model class names vary slightly (Conversation vs Thread, Message)
- Provides endpoints:
  - GET /health
  - GET /status
  - GET /arkadia/corpus
  - GET /arkadia/refresh
  - POST /oracle
  - Thread/history endpoints for UI
  - GET /
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Arkadia modules (current names in your repo)
from arkadia_drive_sync import refresh_arkadia_cache, get_corpus_context
from brain import ArkanaBrain
from db import SessionLocal, engine  # engine used for fallback init_db
import models as models_module  # we'll inspect for classes inside models

logger = logging.getLogger("arkadia")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Arkadia — Arkana Oracle Temple")

# Allow CORS (UI hosted elsewhere can call this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Static files (UI)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

arkana_brain = ArkanaBrain()

# -----------------------
# Models compatibility
# -----------------------
# The repo has used several model names historically:
# - Conversation / Message (older)
# - Thread / Message / User / init_db (expected by older arkana_app)
# We'll try to map gracefully.

# Default model fallbacks
ThreadModel = getattr(models_module, "Thread", None) or getattr(models_module, "Conversation", None)
MessageModel = getattr(models_module, "Message", None)
UserModel = getattr(models_module, "User", None)
init_db_fn = getattr(models_module, "init_db", None)

# If init_db is not provided in models, create a fallback using SQLAlchemy metadata if available
if init_db_fn is None:
    try:
        Base = getattr(models_module, "Base", None)
        if Base is not None and engine is not None:
            def _fallback_init_db():
                Base.metadata.create_all(bind=engine)
            init_db_fn = _fallback_init_db
            logger.info("Using fallback init_db to create tables from models.Base")
        else:
            def _no_op_init_db():
                logger.warning("No init_db or Base found in models; DB tables may not be created automatically.")
            init_db_fn = _no_op_init_db
    except Exception:
        def _no_op_init_db():
            logger.exception("Failed to create fallback init_db")
        init_db_fn = _no_op_init_db

# -----------------------
# DB Dependency
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db_fn()
        logger.info("Arkadia DB initialized.")
    except Exception as e:
        logger.exception("Error during DB init: %s", e)
    logger.info("Static UI directory: %s", STATIC_DIR)

# -----------------------
# Pydantic Schemas
# -----------------------
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

# -----------------------
# Health / Status
# -----------------------
@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
async def status() -> Dict[str, Any]:
    base_status = {}
    try:
        # ArkanaBrain.status_dict may exist; fallback to empty dict
        base_status = getattr(arkana_brain, "status_dict", lambda: {})()  # type: ignore
    except Exception:
        logger.exception("Error fetching arkana_brain status_dict")

    # Optional Rasa probe
    rasa_ok = False
    try:
        ping_rasa = getattr(arkana_brain, "ping_rasa", None)
        if ping_rasa:
            # ping_rasa may be async; attempt to call it sensibly
            maybe = ping_rasa()
            if hasattr(maybe, "__await__"):
                import asyncio
                rasa_ok = asyncio.get_event_loop().run_until_complete(maybe)
            else:
                rasa_ok = bool(maybe)
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

# -----------------------
# Arkadia Corpus Endpoints
# -----------------------
@app.get("/arkadia/corpus")
async def arkadia_corpus() -> JSONResponse:
    try:
        snapshot = refresh_arkadia_cache(force=True)
        docs = snapshot.get("documents") or []
        context_summary = get_corpus_context(docs, max_documents=6, max_preview_chars=400)
        return JSONResponse({"snapshot": snapshot, "context_summary": context_summary})
    except Exception as e:
        logger.exception("Error returning arkadia corpus: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/arkadia/refresh")
async def arkadia_refresh() -> JSONResponse:
    try:
        snapshot = refresh_arkadia_cache(force=True)
        docs = snapshot.get("documents") or []
        context_summary = get_corpus_context(docs, max_documents=6, max_preview_chars=400)
        return JSONResponse({"snapshot": snapshot, "context_summary": context_summary})
    except Exception as e:
        logger.exception("Error refreshing arkadia corpus: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# -----------------------
# Oracle Endpoint (Codex Brain + History)
# -----------------------
@app.post("/oracle")
async def oracle_endpoint(payload: OracleRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    - Records user & Arkana messages in DB (best-effort).
    - Routes to Codex Brain (Gemini + Corpus) by default.
    - NEVER throws 500; always returns JSON.
    """
    sender_external_id = (payload.sender or "anonymous").strip() or "anonymous"
    user = None
    thread = None

    # 1) Ensure user + thread + store user message (best effort)
    try:
        # ArkanaBrain may provide ensure_user / ensure_thread / store_message helpers
        ensure_user = getattr(arkana_brain, "ensure_user", None)
        ensure_thread = getattr(arkana_brain, "ensure_thread", None)
        store_message = getattr(arkana_brain, "store_message", None)

        if ensure_user:
            user = ensure_user(db, sender_external_id)
        if ensure_thread:
            thread = ensure_thread(db, user, payload.thread_id)

        if store_message and thread is not None:
            store_message(db=db, thread=thread, role="user", sender=sender_external_id, content=payload.message)
    except Exception as e:
        logger.exception("DB error while storing user message in /oracle: %s", e)

    # 2) Generate reply (Codex Brain or Rasa)
    try:
        # generate_reply on ArkanaBrain is async in your brain.py; call it accordingly.
        gen = getattr(arkana_brain, "generate_reply", None)
        if gen is None:
            reply_text = "Arkana's generative channel is not available."
        else:
            maybe = gen(sender_external_id, payload.message)
            if hasattr(maybe, "__await__"):
                import asyncio
                reply_text = asyncio.get_event_loop().run_until_complete(maybe)
            else:
                reply_text = maybe
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

    # 3) Store Arkana reply (best effort)
    try:
        store_message = getattr(arkana_brain, "store_message", None)
        if store_message and thread is not None:
            store_message(db=db, thread=thread, role="arkana", sender="arkana", content=reply_text)
    except Exception as e:
        logger.exception("DB error while storing Arkana reply in /oracle: %s", e)

    return {"sender": "arkana", "reply": reply_text, "thread_id": getattr(thread, "id", 0) if thread else 0}


# -----------------------
# Thread + History Endpoints
# -----------------------
@app.get("/threads", response_model=List[ThreadInfo])
async def list_threads(user_id: str, db: Session = Depends(get_db)) -> List[ThreadInfo]:
    if UserModel is None or ThreadModel is None:
        return []

    user = db.query(UserModel).filter(getattr(UserModel, "external_id", "external_id") == user_id).first()
    if not user:
        return []

    threads = db.query(ThreadModel).filter(getattr(ThreadModel, "user_id", "user_id") == user.id).order_by(getattr(ThreadModel, "updated_at", "updated_at").desc()).all()

    out: List[ThreadInfo] = []
    for t in threads:
        out.append(ThreadInfo(id=t.id, title=getattr(t, "title", None), created_at=getattr(t, "created_at").isoformat(), updated_at=getattr(t, "updated_at").isoformat()))
    return out


@app.get("/threads/{thread_id}/messages", response_model=List[MessageInfo])
async def get_thread_messages(thread_id: int, db: Session = Depends(get_db)) -> List[MessageInfo]:
    if MessageModel is None:
        return []

    msgs = db.query(MessageModel).filter(getattr(MessageModel, "thread_id", "thread_id") == thread_id).order_by(getattr(MessageModel, "created_at", "created_at").asc()).all()
    out: List[MessageInfo] = []
    for m in msgs:
        out.append(MessageInfo(id=m.id, role=getattr(m, "role", "user"), sender=getattr(m, "sender", "unknown"), content=getattr(m, "content", ""), created_at=getattr(m, "created_at").isoformat()))
    return out


@app.post("/threads", response_model=ThreadInfo)
async def create_thread(user_id: str, title: Optional[str] = None, db: Session = Depends(get_db)) -> ThreadInfo:
    if UserModel is None or ThreadModel is None:
        raise HTTPException(status_code=500, detail="Thread/User models not available")

    user = getattr(arkana_brain, "ensure_user", lambda db, uid: None)(db, user_id)
    thread = ThreadModel(user_id=user.id, title=title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return ThreadInfo(id=thread.id, title=thread.title, created_at=thread.created_at.isoformat(), updated_at=thread.updated_at.isoformat())


# -----------------------
# UI Root
# -----------------------
@app.get("/")
async def root() -> FileResponse:
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)
