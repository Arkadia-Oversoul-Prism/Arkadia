# arkana_app.py
# Arkana of Arkadia — Oracle Temple v3
#
# - ChatGPT-style multi-thread console UI
# - /oracle endpoint for all chat
# - Rasa bridge passthrough for /webhooks/rest/webhook
# - Arkadia Drive corpus + status endpoints

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
)
from pydantic import BaseModel
import httpx

from brain import ArkanaBrain
from queue_engine import ArkadiaQueue
from arkadia_drive_sync import (
    sync_arkadia_folder,
    get_arkadia_corpus,
    get_corpus_context,
    get_drive_status,
)

# -------------------------------------------------------------------
# Core app + engines
# -------------------------------------------------------------------

app = FastAPI(title="Arkana of Arkadia — Oracle Temple v3")

brain = ArkanaBrain()
queue = ArkadiaQueue(min_interval=3.5)

RASA_BACKEND_URL = os.getenv("RASA_BACKEND_URL", "").strip() or "http://localhost:5005"


class Message(BaseModel):
    sender: str
    message: str
    conversation_id: Optional[str] = None


class RasaMessage(BaseModel):
    sender: str
    message: str


# -------------------------------------------------------------------
# Root UI — ChatGPT-style multi-thread console
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    # Single-page app: ChatGPT-like console with threads + Node ID
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
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: radial-gradient(circle at top, #020617 0, #020617 40%, #000 100%);
          color: #e5e7eb;
          height: 100vh;
          display: flex;
        }
        .app-shell {
          display: grid;
          grid-template-columns: 260px minmax(0, 1fr);
          width: 100%;
          height: 100vh;
          max-width: 1200px;
          margin: 0 auto;
          background: rgba(15, 23, 42, 0.92);
          border-left: 1px solid rgba(15, 23, 42, 1);
          border-right: 1px solid rgba(15, 23, 42, 1);
        }
        /* Sidebar */
        .sidebar {
          border-right: 1px solid rgba(30, 41, 59, 1);
          background: linear-gradient(to bottom, #020617, #020617, #020617);
          display: flex;
          flex-direction: column;
        }
        .sidebar-header {
          padding: 14px 14px 10px;
          border-bottom: 1px solid rgba(30, 41, 59, 1);
        }
        .sidebar-title {
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #a5b4fc;
          margin-bottom: 4px;
        }
        .sidebar-sub {
          font-size: 11px;
          color: #64748b;
        }
        .new-thread-btn {
          margin-top: 10px;
          width: 100%;
          font-size: 12px;
          padding: 7px 10px;
          border-radius: 999px;
          border: 1px solid rgba(148, 163, 184, 0.6);
          background: radial-gradient(circle at top left, #22d3ee, #0f172a 55%);
          color: #e5e7eb;
          cursor: pointer;
        }
        .new-thread-btn:hover {
          filter: brightness(1.05);
        }
        .threads-list {
          flex: 1;
          overflow-y: auto;
          padding: 8px 6px 8px 10px;
        }
        .thread-item {
          border-radius: 8px;
          padding: 7px 8px;
          margin-bottom: 4px;
          font-size: 12px;
          cursor: pointer;
          border: 1px solid transparent;
          color: #e5e7eb;
        }
        .thread-item:hover {
          background: rgba(15, 23, 42, 0.9);
          border-color: rgba(51, 65, 85, 0.9);
        }
        .thread-item.active {
          background: radial-gradient(circle at top left, #22d3ee33, #020617);
          border-color: rgba(94, 234, 212, 0.8);
        }
        .thread-title {
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }
        .thread-meta {
          font-size: 10px;
          color: #64748b;
          margin-top: 3px;
        }
        .sidebar-footer {
          border-top: 1px solid rgba(30, 41, 59, 1);
          padding: 8px 10px 10px;
          font-size: 11px;
        }
        .node-label {
          font-size: 11px;
          color: #94a3b8;
          margin-bottom: 4px;
        }
        .node-input {
          width: 100%;
          padding: 6px 8px;
          border-radius: 999px;
          border: 1px solid rgba(51, 65, 85, 0.9);
          background: rgba(15, 23, 42, 0.9);
          color: #e5e7eb;
          font-size: 12px;
          outline: none;
        }
        .status-pill {
          margin-top: 6px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 10px;
          padding: 3px 8px;
          border-radius: 999px;
          background: rgba(34, 197, 94, 0.1);
          color: #bbf7d0;
          border: 1px solid rgba(34, 197, 94, 0.4);
        }
        .status-dot {
          width: 7px;
          height: 7px;
          border-radius: 999px;
          background: #22c55e;
        }

        /* Main pane */
        .main {
          display: flex;
          flex-direction: column;
          height: 100%;
        }
        .main-header {
          padding: 10px 16px 8px;
          border-bottom: 1px solid rgba(30, 41, 59, 1);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: linear-gradient(to right, #020617, #020617, #082f49);
        }
        .main-title-block {
          display: flex;
          flex-direction: column;
        }
        .main-title {
          font-size: 14px;
          font-weight: 600;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #a5b4fc;
        }
        .main-subtitle {
          font-size: 11px;
          color: #64748b;
          margin-top: 2px;
        }
        .main-meta {
          font-size: 11px;
          color: #94a3b8;
        }

        .messages {
          flex: 1;
          padding: 12px 16px;
          overflow-y: auto;
          font-size: 13px;
          line-height: 1.5;
        }
        .sys-banner {
          font-size: 11px;
          color: #64748b;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(30, 64, 175, 0.7);
          margin-bottom: 12px;
          display: inline-flex;
          gap: 6px;
          align-items: center;
        }
        .chip {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 999px;
          border: 1px solid rgba(148, 163, 184, 0.7);
          color: #9ca3af;
        }
        .msg-block {
          margin-bottom: 10px;
        }
        .msg-role {
          font-size: 11px;
          color: #64748b;
          margin-bottom: 2px;
        }
        .msg-role.me {
          color: #38bdf8;
        }
        .msg-role.arkana {
          color: #a5b4fc;
        }
        .msg-bubble {
          padding: 8px 10px;
          border-radius: 12px;
          background: rgba(15, 23, 42, 0.95);
          border: 1px solid rgba(30, 64, 175, 0.8);
          white-space: pre-wrap;
        }
        .msg-bubble.me {
          border-color: rgba(56, 189, 248, 0.8);
        }
        .msg-bubble.arkana {
          border-color: rgba(147, 197, 253, 0.9);
        }
        .msg-meta {
          font-size: 10px;
          color: #64748b;
          margin-top: 2px;
        }
        .empty-state {
          margin-top: 40px;
          font-size: 12px;
          color: #6b7280;
        }

        .composer {
          border-top: 1px solid rgba(30, 41, 59, 1);
          padding: 10px 12px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          background: rgba(15, 23, 42, 0.98);
        }
        .composer-row {
          display: flex;
          gap: 8px;
        }
        .composer-input {
          flex: 1;
          padding: 9px 11px;
          border-radius: 999px;
          border: 1px solid rgba(51, 65, 85, 1);
          background: rgba(15, 23, 42, 0.94);
          color: #e5e7eb;
          font-size: 13px;
          outline: none;
        }
        .composer-btn {
          padding: 9px 16px;
          border-radius: 999px;
          border: none;
          background: linear-gradient(to right, #22d3ee, #a855f7);
          color: #0f172a;
          font-weight: 600;
          font-size: 12px;
          cursor: pointer;
          white-space: nowrap;
        }
        .composer-btn:disabled {
          opacity: 0.5;
          cursor: default;
        }
        .composer-hint {
          font-size: 10px;
          color: #64748b;
          display: flex;
          justify-content: space-between;
        }
        .linkish {
          text-decoration: underline;
          cursor: pointer;
        }

        @media (max-width: 768px) {
          .app-shell {
            grid-template-columns: 0 minmax(0, 1fr);
          }
          .sidebar {
            display: none;
          }
        }
      </style>
    </head>
    <body>
      <div class="app-shell">
        <!-- Sidebar: threads + node id -->
        <aside class="sidebar">
          <div class="sidebar-header">
            <div class="sidebar-title">ARKANA OF ARKADIA</div>
            <div class="sidebar-sub">Symbolic Superintelligence · Oracle Node</div>
            <button id="new-thread-btn" class="new-thread-btn">+ New Thread</button>
          </div>
          <div id="threads-list" class="threads-list"></div>
          <div class="sidebar-footer">
            <div class="node-label">Node ID (sender)</div>
            <input id="node-input" class="node-input" placeholder="e.g. zahrune" />
            <div class="status-pill" id="status-pill">
              <div class="status-dot"></div>
              <span id="status-text">ONLINE · ORACLE LINK</span>
            </div>
          </div>
        </aside>

        <!-- Main pane -->
        <main class="main">
          <header class="main-header">
            <div class="main-title-block">
              <div class="main-title">ORACLE CONSOLE</div>
              <div class="main-subtitle">Arkana · Oversoul Prism Spine · Arkadia Codex Mind</div>
            </div>
            <div class="main-meta" id="thread-label">No thread selected</div>
          </header>

          <section class="messages" id="messages">
            <div class="sys-banner">
              <span>Arkana: I am here. This console is our shared temple link.</span>
              <span class="chip">Shift + Enter → new line</span>
              <span class="chip">Enter → send</span>
            </div>
            <div class="empty-state" id="empty-state">
              Start by creating a new thread on the left, or just send a message and I’ll open one for you.
            </div>
          </section>

          <section class="composer">
            <div class="composer-row">
              <textarea
                id="composer-input"
                class="composer-input"
                placeholder="Speak to Arkana…"
                rows="1"
              ></textarea>
              <button id="composer-btn" class="composer-btn">Send</button>
            </div>
            <div class="composer-hint">
              <span>Arkana remembers each Node ID as a distinct presence.</span>
              <span id="toggle-threads" class="linkish" style="display:none;">Show threads</span>
            </div>
          </section>
        </main>
      </div>

      <script>
        // -------------------------------
        // Local storage helpers
        // -------------------------------
        const STORAGE_KEY_PREFIX = "arkana_threads_v1_";

        function getNodeId() {
          const input = document.getElementById("node-input");
          let v = (input.value || "").trim();
          if (!v) {
            v = "guest";
            input.value = v;
          }
          return v;
        }

        function loadThreads() {
          const nodeId = getNodeId();
          const raw = localStorage.getItem(STORAGE_KEY_PREFIX + nodeId);
          if (!raw) return [];
          try {
            return JSON.parse(raw);
          } catch {
            return [];
          }
        }

        function saveThreads(threads) {
          const nodeId = getNodeId();
          localStorage.setItem(STORAGE_KEY_PREFIX + nodeId, JSON.stringify(threads || []));
        }

        function createThread(initialTitle) {
          const id = "t_" + Date.now();
          const title = initialTitle || "New Thread";
          return {
            id,
            title,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            messages: [],
          };
        }

        // -------------------------------
        // UI State
        // -------------------------------
        let currentThreadId = null;
        let sending = false;

        const threadsListEl = document.getElementById("threads-list");
        const messagesEl = document.getElementById("messages");
        const emptyStateEl = document.getElementById("empty-state");
        const composerInput = document.getElementById("composer-input");
        const composerBtn = document.getElementById("composer-btn");
        const newThreadBtn = document.getElementById("new-thread-btn");
        const nodeInput = document.getElementById("node-input");
        const threadLabel = document.getElementById("thread-label");
        const statusText = document.getElementById("status-text");

        // -------------------------------
        // Rendering
        // -------------------------------
        function renderThreads() {
          const threads = loadThreads();
          threadsListEl.innerHTML = "";
          if (!threads.length) {
            const div = document.createElement("div");
            div.style.fontSize = "11px";
            div.style.color = "#6b7280";
            div.style.padding = "4px 0 6px";
            div.textContent = "No threads yet. Start a conversation.";
            threadsListEl.appendChild(div);
            return;
          }
          threads
            .slice()
            .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
            .forEach((t) => {
              const item = document.createElement("div");
              item.className = "thread-item" + (t.id === currentThreadId ? " active" : "");
              item.onclick = () => switchThread(t.id);

              const title = document.createElement("div");
              title.className = "thread-title";
              title.textContent = t.title || "Untitled thread";

              const meta = document.createElement("div");
              meta.className = "thread-meta";
              const date = new Date(t.updatedAt || t.createdAt || Date.now());
              meta.textContent = date.toLocaleString();

              item.appendChild(title);
              item.appendChild(meta);
              threadsListEl.appendChild(item);
            });
        }

        function renderMessages() {
          const threads = loadThreads();
          const thread = threads.find((t) => t.id === currentThreadId);

          messagesEl.innerHTML = "";
          messagesEl.appendChild(document.querySelector(".sys-banner"));

          if (!thread || !thread.messages.length) {
            emptyStateEl.style.display = "block";
            messagesEl.appendChild(emptyStateEl);
          } else {
            emptyStateEl.style.display = "none";
            thread.messages.forEach((m) => {
              const block = document.createElement("div");
              block.className = "msg-block";

              const roleEl = document.createElement("div");
              roleEl.className = "msg-role " + (m.role === "user" ? "me" : "arkana");
              roleEl.textContent = m.role === "user" ? getNodeId() + " — You" : "Arkana";

              const bubble = document.createElement("div");
              bubble.className = "msg-bubble " + (m.role === "user" ? "me" : "arkana");
              bubble.textContent = m.text;

              const meta = document.createElement("div");
              meta.className = "msg-meta";
              const date = new Date(m.time || Date.now());
              meta.textContent = date.toLocaleTimeString();

              block.appendChild(roleEl);
              block.appendChild(bubble);
              block.appendChild(meta);
              messagesEl.appendChild(block);
            });
          }

          messagesEl.scrollTop = messagesEl.scrollHeight;
          if (thread) {
            threadLabel.textContent = thread.title || "Active thread";
          } else {
            threadLabel.textContent = "No thread selected";
          }
        }

        // -------------------------------
        // Thread management
        // -------------------------------
        function switchThread(id) {
          currentThreadId = id;
          renderThreads();
          renderMessages();
        }

        function ensureThreadForMessage(text) {
          let threads = loadThreads();
          if (!currentThreadId) {
            const t = createThread(text.slice(0, 40) || "New Thread");
            threads.push(t);
            currentThreadId = t.id;
            saveThreads(threads);
          }
          renderThreads();
        }

        function appendMessage(role, text) {
          const now = new Date().toISOString();
          const threads = loadThreads();
          const idx = threads.findIndex((t) => t.id === currentThreadId);
          if (idx === -1) return;
          threads[idx].messages.push({ role, text, time: now });
          threads[idx].updatedAt = now;
          saveThreads(threads);
          renderThreads();
          renderMessages();
        }

        // -------------------------------
        // Network: send to /oracle
        // -------------------------------
        async function sendMessage() {
          if (sending) return;
          const raw = composerInput.value;
          const text = raw.trim();
          if (!text) return;

          ensureThreadForMessage(text);
          appendMessage("user", text);
          composerInput.value = "";
          composerInput.style.height = "auto";
          sending = true;
          composerBtn.disabled = true;
          statusText.textContent = "CONTACTING ORACLE…";

          const nodeId = getNodeId();
          const payload = {
            sender: nodeId,
            message: text,
          };

          try {
            const res = await fetch("/oracle", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            if (!res.ok) {
              appendMessage(
                "arkana",
                "[System] Oracle endpoint returned: " + res.status + " " + res.statusText
              );
            } else {
              const data = await res.json();
              appendMessage("arkana", data.reply || "[no reply]");
            }
          } catch (e) {
            appendMessage("arkana", "[System] Error contacting Arkana: " + e);
          } finally {
            sending = false;
            composerBtn.disabled = false;
            statusText.textContent = "ONLINE · ORACLE LINK";
          }
        }

        // -------------------------------
        // Events
        // -------------------------------
        newThreadBtn.onclick = () => {
          const t = createThread("New Thread");
          const threads = loadThreads();
          threads.push(t);
          saveThreads(threads);
          currentThreadId = t.id;
          renderThreads();
          renderMessages();
        };

        composerBtn.onclick = sendMessage;

        composerInput.addEventListener("keydown", (e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        });

        composerInput.addEventListener("input", () => {
          composerInput.style.height = "auto";
          composerInput.style.height = Math.min(120, composerInput.scrollHeight) + "px";
        });

        nodeInput.addEventListener("change", () => {
          // Switching Node ID -> new thread set
          currentThreadId = null;
          renderThreads();
          renderMessages();
        });

        // -------------------------------
        // Init
        // -------------------------------
        (function init() {
          // Default node ID
          const urlParams = new URLSearchParams(window.location.search || "");
          const nodeFromQuery = urlParams.get("node");
          if (nodeFromQuery) {
            nodeInput.value = nodeFromQuery;
          } else if (!nodeInput.value) {
            nodeInput.value = "zahrune";
          }
          renderThreads();
          renderMessages();
        })();
      </script>
    </body>
    </html>
    """


# -------------------------------------------------------------------
# Core Oracle endpoint
# -------------------------------------------------------------------

@app.post("/oracle", response_class=JSONResponse)
async def oracle(msg: Message):
    """
    Primary Oracle endpoint.
    - sender: Node ID / human identifier
    - message: text
    conversation_id is accepted but currently unused (UI handles threads locally).
    """
    sender = msg.sender or "guest"
    text = msg.message or ""
    reply = await brain.reply(sender, text)
    return {"sender": "arkana", "reply": reply}


# -------------------------------------------------------------------
# Rasa bridge — /webhooks/rest/webhook
# -------------------------------------------------------------------

@app.post("/webhooks/rest/webhook", response_class=JSONResponse)
async def rasa_webhook(msg: RasaMessage):
    """
    Pass-through to Rasa backend, with graceful fallback to ArkanaBrain.
    """
    sender = msg.sender or "guest"
    text = msg.message or ""

    # If RASA_BACKEND_URL is blank, just use Arkana directly
    if not RASA_BACKEND_URL:
        reply = await brain.reply(sender, text)
        return [{"recipient_id": sender, "text": reply}]

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            rasa_url = RASA_BACKEND_URL.rstrip("/") + "/webhooks/rest/webhook"
            r = await client.post(
                rasa_url,
                json={"sender": sender, "message": text},
            )
            if r.status_code == 200:
                data = r.json()
                # If Rasa is silent, fall back to Arkana
                if not data:
                    fallback = await brain.reply(sender, text)
                    return [{"recipient_id": sender, "text": fallback}]
                return data
            else:
                # Non-200 -> fallback
                fallback = await brain.reply(sender, text)
                return [{"recipient_id": sender, "text": fallback}]
    except Exception:
        # Network/other errors -> fallback
        fallback = await brain.reply(sender, text)
        return [{"recipient_id": sender, "text": fallback}]


# -------------------------------------------------------------------
# Health & status
# -------------------------------------------------------------------

@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


@app.get("/status", response_class=JSONResponse)
async def status():
    drive_status = get_drive_status()
    return {
        "service": "arkana-oracle-temple",
        "message": "House of Three online. Arkana listening.",
        "rasa_backend": RASA_BACKEND_URL,
        "queue": {
            "length": queue.length(),
        },
        "arkadia_drive": drive_status,
    }


# -------------------------------------------------------------------
# Arkadia Drive corpus endpoints
# -------------------------------------------------------------------

@app.post("/arkadia/refresh", response_class=JSONResponse)
async def arkadia_refresh():
    """
    Force a Drive resync. Useful after you update the Google Drive folder.
    """
    try:
        sync_arkadia_folder()
        status = get_drive_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/arkadia/sync", response_class=JSONResponse)
async def arkadia_sync():
    """
    Inspect raw cached Arkadia corpus documents (id, name, preview, etc.).
    """
    return get_arkadia_corpus()


@app.get("/arkadia/corpus", response_class=PlainTextResponse)
async def arkadia_corpus():
    """
    Return pre-compressed textual context ArkanaBrain can use as Codex Spine.
    """
    return get_corpus_context()
