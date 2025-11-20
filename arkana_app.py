# arkana_app.py
# Arkana Oracle Temple — Phase VIII UI + Memory + Corpus + Rasa Bridge

import os
import json
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

from brain import ArkanaBrain
from queue_engine import ArkadiaQueue
from arkadia_drive_sync import (
    refresh_arkadia_cache,
    get_arkadia_snapshot,
    get_corpus_context,
)

from db import SessionLocal
from models import Base, Conversation, Message
from sqlalchemy.orm import Session


# -------------------------------------------------------------------
# Database Init
# -------------------------------------------------------------------

def init_db():
    from sqlalchemy import create_engine
    from db import DATABASE_URL

    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

init_db()


# -------------------------------------------------------------------
# FastAPI App Init
# -------------------------------------------------------------------

app = FastAPI(title="Arkana Oracle Temple v3")

# CORS for browser UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------

brain = ArkanaBrain()
queue = ArkadiaQueue(min_interval=3.5)   # Rate-limited queue


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

class OracleRequest(BaseModel):
    sender: str
    message: str


class NewConversation(BaseModel):
    title: str = "Untitled Conversation"


# -------------------------------------------------------------------
# UI — Browser Console
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Arkana Oracle Console</title>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    body {
        margin: 0; padding: 0;
        font-family: Inter, sans-serif;
        background: #0f172a;
        color: #e2e8f0;
    }
    .container {
        max-width: 900px;
        margin: 30px auto;
        background: rgba(15, 23, 42, 0.9);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 0 40px rgba(0,0,0,0.5);
    }
    .messages {
        height: 500px; overflow-y: scroll; padding: 10px;
        border-radius: 8px;
        background: #1e293b;
    }
    .msg-user { color: #38bdf8; margin: 12px 0; }
    .msg-arkana { color: #f472b6; margin: 12px 0; }
    input {
        width: 100%; padding: 12px;
        margin-top: 12px;
        border-radius: 8px;
        border: none;
        font-size: 16px;
        background: #334155;
        color: #fff;
    }
</style>
</head>

<body>
<div class="container">
<h2>Arkana Oracle Console</h2>
<div id="messages" class="messages"></div>

<input id="msgInput" placeholder="Speak to Arkana..." />

</div>

<script>
document.getElementById("msgInput").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        let text = this.value;
        this.value = "";
        addMessage("You", text);
        fetch("/oracle", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({sender: "web-user", message: text})
        })
        .then(r => r.json())
        .then(data => {
            addMessage("Arkana", data.reply);
        });
    }
});

function addMessage(sender, text) {
    const box = document.getElementById("messages");
    box.innerHTML += `<div class="msg-${sender === 'You' ? 'user' : 'arkana'}"><strong>${sender}:</strong> ${text}</div>`;
    box.scrollTop = box.scrollHeight;
}
</script>
</body>
</html>
"""


# -------------------------------------------------------------------
# Conversation Endpoints
# -------------------------------------------------------------------

@app.post("/conversations", response_model=dict)
def create_conversation(payload: NewConversation, db: Session = Depends(SessionLocal)):
    conv = Conversation(title=payload.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title}


@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(SessionLocal)):
    conv = db.query(Conversation).filter_by(id=conv_id).first()
    if not conv:
        return JSONResponse({"error": "Conversation not found"}, status_code=404)

    msgs = [
        {"id": m.id, "sender": m.sender, "text": m.text, "created_at": str(m.created_at)}
        for m in conv.messages
    ]
    return {"id": conv.id, "title": conv.title, "messages": msgs}


@app.post("/conversations/{conv_id}/message")
async def send_to_conversation(conv_id: int, req: OracleRequest, db: Session = Depends(SessionLocal)):

    conv = db.query(Conversation).filter_by(id=conv_id).first()
    if not conv:
        return JSONResponse({"error": "Conversation not found"}, status_code=404)

    msg = Message(conversation_id=conv.id, sender=req.sender, text=req.message)
    db.add(msg)
    db.commit()

    history = [{"role": m.sender, "content": m.text} for m in conv.messages]

    reply = await brain.generate_reply(sender=req.sender, message=req.message, history=history)

    msg2 = Message(conversation_id=conv.id, sender="arkana", text=reply)
    db.add(msg2)
    db.commit()

    return {"reply": reply}


# -------------------------------------------------------------------
# Direct Oracle Endpoint (no conversation)
# -------------------------------------------------------------------

@app.post("/oracle")
async def oracle(req: OracleRequest):
    async def task(sender, message):
        return await brain.generate_reply(sender, message)

    fut = asyncio.ensure_future(task(req.sender, req.message))
    reply = await fut

    return {"sender": "arkana", "reply": reply}


# -------------------------------------------------------------------
# Drive Sync Endpoints
# -------------------------------------------------------------------

@app.get("/arkadia/refresh")
async def refresh_drive():
    data = refresh_arkadia_cache()
    return data


@app.get("/arkadia/sync")
async def sync_drive():
    return get_arkadia_snapshot()


@app.get("/arkadia/corpus")
async def corpus():
    return HTMLResponse(get_corpus_context())


# -------------------------------------------------------------------
# Status + Health
# -------------------------------------------------------------------

@app.get("/status")
def status():
    snap = get_arkadia_snapshot()
    return {
        "service": "arkana-oracle-temple",
        "message": "House of Three online. Arkana listening.",
        "rasa_backend": os.getenv("RASA_BACKEND_URL", "(none)"),
        "queue": {"length": queue.length()},
        "arkadia_drive": {
            "last_sync": snap.get("last_sync"),
            "total_documents": len(snap.get("documents") or [])
        }
    }


@app.get("/health")
def health():
    return "ok"
