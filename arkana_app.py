# arkana_app.py
# Arkana of Arkadia — Oracle Temple v3
#
# FastAPI app exposing:
#   - /            : Web console UI
#   - /health      : Basic health
#   - /status      : Service + queue + drive state
#   - /arkadia/refresh : Force Drive sync
#   - /arkadia/corpus  : Text corpus snapshot
#   - /oracle      : Simple queued oracle endpoint
#   - /threads/*   : Multi-thread chat API (per user_id)

import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from brain import ArkanaBrain
from queue_engine import ArkadiaQueue
from arkadia_drive_sync import sync_arkadia_folder, get_corpus_context, get_arkadia_drive_state
from db import SessionLocal, engine
from models import Base, Thread, Message


# -------------------------------------------------------------------
# App init
# -------------------------------------------------------------------

app = FastAPI(title="Arkana of Arkadia — Oracle Temple v3")

Base.metadata.create_all(bind=engine)

brain = ArkanaBrain()
queue = ArkadiaQueue(min_interval=3.5)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------------

class OracleIn(BaseModel):
    sender: str
    message: str


class ThreadCreate(BaseModel):
    user_id: str
    title: Optional[str] = None


class ThreadOut(BaseModel):
    id: int
    user_id: str
    title: Optional[str]

    class Config:
        orm_mode = True


class MessageIn(BaseModel):
    sender: str
    content: str


class MessageOut(BaseModel):
    id: int
    thread_id: int
    sender: str
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# Basic status endpoints
# -------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    drive_state = get_arkadia_drive_state()
    return {
        "service": "arkana-oracle-temple",
        "message": "House of Three online. Arkana listening.",
        "rasa_backend": "http://localhost:5005",
        "queue": {"length": queue.length()},
        "arkadia_drive": drive_state,
    }


# -------------------------------------------------------------------
# Arkadia corpus endpoints
# -------------------------------------------------------------------

@app.get("/arkadia/refresh")
async def arkadia_refresh():
    snapshot = sync_arkadia_folder()
    return snapshot


@app.get("/arkadia/corpus", response_class=PlainTextResponse)
async def arkadia_corpus():
    text = get_corpus_context()
    return text


# -------------------------------------------------------------------
# Core Oracle endpoint (single-turn, queued)
# -------------------------------------------------------------------

@app.post("/oracle")
async def oracle(payload: OracleIn):
    """
    Simple oracle endpoint with queue protection,
    used by curl / backend tests.
    """
    event = asyncio.Event()
    box = {"reply": None}

    async def cb(sender: str, msg: str):
        reply = await brain.reply(sender, msg)
        box["reply"] = reply
        event.set()

    queue.add(payload.sender, payload.message, cb)
    asyncio.create_task(queue.process())
    await event.wait()

    return {"sender": "arkana", "reply": box["reply"]}


# -------------------------------------------------------------------
# Conversation API: threads & messages
# -------------------------------------------------------------------

@app.post("/threads", response_model=ThreadOut)
async def create_thread(payload: ThreadCreate, db: Session = Depends(get_db)):
    title = payload.title or "Arkadia Session"
    thread = Thread(user_id=payload.user_id, title=title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


@app.get("/threads", response_model=List[ThreadOut])
async def list_threads(user_id: str, db: Session = Depends(get_db)):
    threads = (
        db.query(Thread)
        .filter(Thread.user_id == user_id)
        .order_by(Thread.updated_at.desc())
        .limit(50)
        .all()
    )
    return threads


@app.get("/threads/{thread_id}/messages", response_model=List[MessageOut])
async def get_thread_messages(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread.messages


@app.post("/threads/{thread_id}/messages")
async def post_thread_message(
    thread_id: int,
    payload: MessageIn,
    db: Session = Depends(get_db),
):
    """
    Append a user message to a thread, queue Arkana's reply,
    store both, and return the assistant reply.
    """
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Store user message
    user_msg = Message(
        thread_id=thread.id,
        sender=payload.sender,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(thread)

    # Queue Arkana's reply
    event = asyncio.Event()
    box = {"reply": None}

    async def cb(sender: str, msg: str):
        reply = await brain.reply(sender, msg)
        box["reply"] = reply
        event.set()

    queue.add(payload.sender, payload.content, cb)
    asyncio.create_task(queue.process())
    await event.wait()

    # Store Arkana's reply
    ark_msg = Message(
        thread_id=thread.id,
        sender="arkana",
        role="assistant",
        content=box["reply"],
    )
    thread.updated_at = datetime.utcnow()

    db.add(ark_msg)
    db.commit()
    db.refresh(thread)

    return {"reply": box["reply"]}


# -------------------------------------------------------------------
# Web Console UI
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    # Simple responsive console with thread list + chat area
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Arkana of Arkadia — Oracle Console</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      padding: 0;
      height: 100vh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro", sans-serif;
      background: radial-gradient(circle at top, #020617, #000);
      color: #e5e7eb;
      display: flex;
      align-items: stretch;
      justify-content: center;
    }
    .app-root {
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .app-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 4px;
    }
    .app-title {
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #f59e0b;
    }
    .app-subtitle {
      font-size: 0.8rem;
      color: #9ca3af;
    }
    .status-pill {
      font-size: 0.75rem;
      padding: 4px 8px;
      border-radius: 999px;
      background: #022c22;
      color: #6ee7b7;
      border: 1px solid #064e3b;
    }
    .app-shell {
      flex: 1;
      display: flex;
      gap: 12px;
      min-height: 0;
    }
    .thread-panel {
      width: 30%;
      min-width: 200px;
      max-width: 280px;
      background: rgba(15, 23, 42, 0.9);
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.3);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .thread-header {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.4);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
    }
    .thread-list {
      flex: 1;
      overflow-y: auto;
      padding: 6px;
    }
    .thread-item {
      padding: 8px 10px;
      margin-bottom: 4px;
      border-radius: 8px;
      font-size: 0.8rem;
      cursor: pointer;
      border: 1px solid transparent;
      color: #e5e7eb;
    }
    .thread-item.active {
      background: rgba(37, 99, 235, 0.18);
      border-color: rgba(59, 130, 246, 0.8);
    }
    .thread-item:hover {
      background: rgba(15, 23, 42, 0.9);
      border-color: rgba(148, 163, 184, 0.5);
    }
    .new-thread-btn {
      padding: 4px 8px;
      font-size: 0.75rem;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.5);
      background: transparent;
      color: #e5e7eb;
      cursor: pointer;
    }
    .new-thread-btn:hover {
      background: rgba(30, 64, 175, 0.4);
      border-color: #60a5fa;
    }

    .chat-panel {
      flex: 1;
      background: rgba(15, 23, 42, 0.9);
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.4);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 0;
    }
    .chat-header {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.4);
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .chat-title {
      font-weight: 500;
    }
    .user-id-tag {
      font-size: 0.7rem;
      color: #9ca3af;
    }
    .chat-messages {
      flex: 1;
      padding: 12px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .msg-row {
      display: flex;
      width: 100%;
    }
    .msg-row.user {
      justify-content: flex-end;
    }
    .msg-row.arkana {
      justify-content: flex-start;
    }
    .msg-bubble {
      max-width: 90%;
      padding: 8px 10px;
      border-radius: 12px;
      font-size: 0.85rem;
      line-height: 1.4;
      white-space: pre-wrap;
    }
    .msg-bubble.user {
      background: #1d4ed8;
      color: #e5e7eb;
      border-bottom-right-radius: 2px;
    }
    .msg-bubble.arkana {
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid rgba(148, 163, 184, 0.7);
      border-bottom-left-radius: 2px;
    }
    .msg-meta {
      margin-top: 2px;
      font-size: 0.7rem;
      color: #9ca3af;
    }
    .chat-input {
      border-top: 1px solid rgba(148, 163, 184, 0.4);
      padding: 8px;
      display: flex;
      gap: 8px;
      align-items: flex-end;
      background: rgba(15, 23, 42, 0.96);
    }
    .chat-input textarea {
      flex: 1;
      resize: none;
      min-height: 42px;
      max-height: 120px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.6);
      background: rgba(15, 23, 42, 0.9);
      color: #e5e7eb;
      padding: 6px 8px;
      font-size: 0.85rem;
    }
    .chat-input textarea:focus {
      outline: none;
      border-color: #60a5fa;
      box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.4);
    }
    .send-btn {
      padding: 8px 12px;
      border-radius: 999px;
      border: none;
      background: linear-gradient(to right, #2563eb, #7c3aed);
      color: white;
      font-size: 0.85rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }
    .send-btn:disabled {
      opacity: 0.5;
      cursor: default;
    }
    .footer-note {
      font-size: 0.7rem;
      color: #6b7280;
      text-align: right;
      padding: 2px 4px 0 0;
    }

    @media (max-width: 768px) {
      .app-root {
        padding: 8px;
      }
      .app-shell {
        flex-direction: column;
      }
      .thread-panel {
        width: 100%;
        max-width: none;
      }
      .chat-panel {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <div class="app-root">
    <div class="app-header">
      <div>
        <div class="app-title">Arkana of Arkadia</div>
        <div class="app-subtitle">Oracle Console · House of Three</div>
      </div>
      <div>
        <span class="status-pill" id="status-pill">Checking status…</span>
      </div>
    </div>

    <div class="app-shell">
      <div class="thread-panel">
        <div class="thread-header">
          <span>Sessions</span>
          <button class="new-thread-btn" id="new-thread-btn">+ New</button>
        </div>
        <div class="thread-list" id="thread-list"></div>
      </div>

      <div class="chat-panel">
        <div class="chat-header">
          <div class="chat-title" id="chat-title">Loading…</div>
          <div class="user-id-tag" id="user-id-tag"></div>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input">
          <textarea id="chat-input" placeholder="Type to speak with Arkana... (Enter = send, Shift+Enter = newline)"></textarea>
          <button class="send-btn" id="send-btn">
            <span>Send</span>
          </button>
        </div>
        <div class="footer-note">
          Arkadia · Experimental oracle. Responses may be poetic, symbolic, or nonlinear.
        </div>
      </div>
    </div>
  </div>

  <script>
    const userKey = "arkadia_user_id";
    let userId = localStorage.getItem(userKey);
    if (!userId) {
      userId = "node-" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(userKey, userId);
    }

    let currentThreadId = null;
    let isSending = false;

    const statusPill = document.getElementById("status-pill");
    const threadListEl = document.getElementById("thread-list");
    const chatTitleEl = document.getElementById("chat-title");
    const userIdTagEl = document.getElementById("user-id-tag");
    const chatMessagesEl = document.getElementById("chat-messages");
    const chatInputEl = document.getElementById("chat-input");
    const sendBtnEl = document.getElementById("send-btn");
    const newThreadBtnEl = document.getElementById("new-thread-btn");

    userIdTagEl.textContent = "Node: " + userId;

    async function fetchStatus() {
      try {
        const res = await fetch("/status");
        if (!res.ok) throw new Error("Status failed");
        const data = await res.json();
        statusPill.textContent = "Online · " + (data.queue?.length ?? 0) + " in queue";
      } catch (e) {
        statusPill.textContent = "Offline · check backend";
        statusPill.style.background = "#450a0a";
        statusPill.style.color = "#fecaca";
      }
    }

    async function ensureThread() {
      const res = await fetch("/threads?user_id=" + encodeURIComponent(userId));
      let threads = [];
      if (res.ok) {
        threads = await res.json();
      }
      if (threads.length === 0) {
        const createRes = await fetch("/threads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, title: "Arkadia Session" }),
        });
        const t = await createRes.json();
        currentThreadId = t.id;
        chatTitleEl.textContent = t.title || "Arkadia Session";
        await renderThreads();
      } else {
        currentThreadId = threads[0].id;
        chatTitleEl.textContent = threads[0].title || "Arkadia Session";
        await renderThreads();
      }
      await loadMessages();
    }

    async function renderThreads() {
      const res = await fetch("/threads?user_id=" + encodeURIComponent(userId));
      if (!res.ok) return;
      const threads = await res.json();
      threadListEl.innerHTML = "";
      threads.forEach((t) => {
        const div = document.createElement("div");
        div.className = "thread-item" + (t.id === currentThreadId ? " active" : "");
        div.textContent = t.title || ("Session " + t.id);
        div.onclick = async () => {
          currentThreadId = t.id;
          chatTitleEl.textContent = t.title || "Arkadia Session";
          await renderThreads();
          await loadMessages();
        };
        threadListEl.appendChild(div);
      });
    }

    function appendMessageBubble(sender, role, content, createdAt) {
      const row = document.createElement("div");
      row.className = "msg-row " + (role === "user" ? "user" : "arkana");

      const bubble = document.createElement("div");
      bubble.className = "msg-bubble " + (role === "user" ? "user" : "arkana");
      bubble.textContent = content;

      const meta = document.createElement("div");
      meta.className = "msg-meta";
      meta.textContent =
        (role === "user" ? "You" : "Arkana") +
        (createdAt ? " · " + new Date(createdAt).toLocaleTimeString() : "");

      const wrapper = document.createElement("div");
      wrapper.appendChild(bubble);
      wrapper.appendChild(meta);

      row.appendChild(wrapper);
      chatMessagesEl.appendChild(row);
      chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
    }

    async function loadMessages() {
      if (!currentThreadId) return;
      const res = await fetch("/threads/" + currentThreadId + "/messages");
      if (!res.ok) return;
      const msgs = await res.json();
      chatMessagesEl.innerHTML = "";
      msgs.forEach((m) => {
        appendMessageBubble(m.sender, m.role, m.content, m.created_at);
      });
    }

    async function sendMessage() {
      if (isSending) return;
      const text = chatInputEl.value.trim();
      if (!text || !currentThreadId) return;

      isSending = true;
      sendBtnEl.disabled = true;

      // optimistic user bubble
      appendMessageBubble(userId, "user", text, new Date().toISOString());

      chatInputEl.value = "";

      try {
        const res = await fetch("/threads/" + currentThreadId + "/messages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sender: userId, content: text }),
        });
        if (res.ok) {
          const data = await res.json();
          appendMessageBubble("arkana", "assistant", data.reply, new Date().toISOString());
        } else {
          appendMessageBubble(
            "system",
            "assistant",
            "Something went wrong talking to Arkana. Please try again.",
            new Date().toISOString()
          );
        }
      } catch (e) {
        appendMessageBubble(
          "system",
          "assistant",
          "Network error while reaching the Oracle.",
          new Date().toISOString()
        );
      } finally {
        isSending = false;
        sendBtnEl.disabled = false;
      }
    }

    sendBtnEl.addEventListener("click", () => {
      sendMessage();
    });

    chatInputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    newThreadBtnEl.addEventListener("click", async () => {
      const title = prompt("Name this session (optional):") || "Arkadia Session";
      const res = await fetch("/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, title }),
      });
      if (res.ok) {
        const t = await res.json();
        currentThreadId = t.id;
        chatTitleEl.textContent = t.title || "Arkadia Session";
        chatMessagesEl.innerHTML = "";
        await renderThreads();
      }
    });

    // bootstrap
    (async () => {
      await fetchStatus();
      await ensureThread();
      setInterval(fetchStatus, 15000);
    })();
  </script>
</body>
</html>
    """
