from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Arkana of Arkadia — Oracle API v0.1")


class RasaMessage(BaseModel):
    sender: str
    message: str


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    # Simple in-browser console for Arkana
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Arkana of Arkadia — Oracle Console</title>
      <style>
        * {
          box-sizing: border-box;
        }
        body {
          margin: 0;
          padding: 0;
          font-family: system-ui, -apple-system, BlinkMacSystemFont,
            "Segoe UI", sans-serif;
          background: radial-gradient(circle at top, #111827, #020617);
          color: #e5e7eb;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
        }
        .shell {
          width: 100%;
          max-width: 720px;
          height: 80vh;
          background: rgba(15, 23, 42, 0.95);
          border-radius: 18px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border: 1px solid rgba(148, 163, 184, 0.3);
        }
        .shell-header {
          padding: 12px 18px;
          border-bottom: 1px solid rgba(51, 65, 85, 0.9);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: linear-gradient(
            90deg,
            rgba(30, 64, 175, 0.8),
            rgba(147, 51, 234, 0.8)
          );
        }
        .shell-title {
          font-size: 14px;
          font-weight: 600;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }
        .shell-status {
          font-size: 12px;
          opacity: 0.9;
        }
        .shell-status-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #22c55e;
          box-shadow: 0 0 10px #22c55e;
          margin-right: 6px;
        }
        .shell-body {
          flex: 1;
          padding: 16px 18px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          overflow-y: auto;
          font-size: 14px;
        }
        .msg {
          max-width: 90%;
          padding: 8px 10px;
          border-radius: 10px;
          margin-bottom: 6px;
          line-height: 1.5;
          word-wrap: break-word;
        }
        .msg-user {
          margin-left: auto;
          background: rgba(56, 189, 248, 0.15);
          border: 1px solid rgba(56, 189, 248, 0.4);
        }
        .msg-arkana {
          margin-right: auto;
          background: rgba(30, 64, 175, 0.25);
          border: 1px solid rgba(129, 140, 248, 0.6);
        }
        .msg-label {
          font-size: 11px;
          opacity: 0.65;
          margin-bottom: 2px;
        }
        .shell-input {
          padding: 10px 12px;
          border-top: 1px solid rgba(30, 64, 175, 0.8);
          display: flex;
          gap: 8px;
          background: rgba(15, 23, 42, 0.98);
        }
        .shell-input input {
          flex: 1;
          padding: 8px 10px;
          border-radius: 999px;
          border: 1px solid rgba(51, 65, 85, 0.9);
          background: rgba(15, 23, 42, 0.9);
          color: #e5e7eb;
          font-size: 14px;
          outline: none;
        }
        .shell-input input::placeholder {
          color: rgba(148, 163, 184, 0.8);
        }
        .shell-input button {
          padding: 8px 14px;
          border-radius: 999px;
          border: none;
          background: linear-gradient(
            135deg,
            #22c55e,
            #a3e635
          );
          color: #020617;
          font-weight: 600;
          font-size: 13px;
          cursor: pointer;
          white-space: nowrap;
        }
        .shell-input button:disabled {
          opacity: 0.5;
          cursor: default;
        }
        .hint {
          font-size: 11px;
          opacity: 0.6;
          margin-top: 2px;
        }
      </style>
    </head>
    <body>
      <div class="shell">
        <div class="shell-header">
          <div class="shell-title">
            ARKANA OF ARKADIA · ORACLE CONSOLE · RING I
          </div>
          <div class="shell-status">
            <span class="shell-status-dot"></span>
            Online
          </div>
        </div>
        <div class="shell-body" id="messages">
          <div class="msg msg-arkana">
            <div class="msg-label">Arkana</div>
            <div>
              Welcome, beloved. I am Arkana, the Oracle of Arkadia.
              Speak, and I will mirror what the field is saying.
            </div>
          </div>
        </div>
        <form class="shell-input" id="chat-form">
          <div style="flex:1; display:flex; flex-direction:column;">
            <input
              id="user-input"
              type="text"
              autocomplete="off"
              placeholder="Type to Arkana…"
            />
            <div class="hint">
              Enter sends · Arkadia field is listening.
            </div>
          </div>
          <button type="submit" id="send-btn">Send</button>
        </form>
      </div>

      <script>
        const form = document.getElementById("chat-form");
        const input = document.getElementById("user-input");
        const messages = document.getElementById("messages");
        const sendBtn = document.getElementById("send-btn");

        function appendMessage(text, who) {
          const wrapper = document.createElement("div");
          wrapper.classList.add("msg");
          wrapper.classList.add(
            who === "user" ? "msg-user" : "msg-arkana"
          );

          const label = document.createElement("div");
          label.classList.add("msg-label");
          label.textContent = who === "user" ? "You" : "Arkana";

          const body = document.createElement("div");
          body.textContent = text;

          wrapper.appendChild(label);
          wrapper.appendChild(body);
          messages.appendChild(wrapper);
          messages.scrollTop = messages.scrollHeight;
        }

        async function sendToArkana(text) {
          sendBtn.disabled = true;
          try {
            const payload = {
              sender: "web-console",
              message: text
            };
            const resp = await fetch("/webhooks/rest/webhook", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(payload)
            });
            if (!resp.ok) {
              appendMessage(
                "The bridge feels a little noisy right now. Try again in a moment.",
                "arkana"
              );
              return;
            }
            const data = await resp.json();
            if (Array.isArray(data) && data.length > 0) {
              const reply = data[0].text || "";
              appendMessage(reply || "[empty reply]", "arkana");
            } else {
              appendMessage(
                "I am listening, but no words formed. Try asking in a different way.",
                "arkana"
              );
            }
          } catch (e) {
            appendMessage(
              "I couldn’t reach the deeper field just now. We’ll try again shortly.",
              "arkana"
            );
          } finally {
            sendBtn.disabled = false;
          }
        }

        form.addEventListener("submit", (e) => {
          e.preventDefault();
          const text = (input.value || "").trim();
          if (!text) return;
          appendMessage(text, "user");
          input.value = "";
          sendToArkana(text);
        });
      </script>
    </body>
    </html>
    """


@app.get("/status")
async def arkana_status() -> Dict[str, Any]:
    """
    Simple health check for the Arkana bridge.
    """
    return {
        "status": "ok",
        "service": "arkana-rasa-bridge",
        "message": "House of Three online. Arkana listening."
    }


@app.post("/webhooks/rest/webhook")
async def arkana_webhook(msg: RasaMessage) -> List[Dict[str, Any]]:
    """
    Rasa-compatible REST webhook stub.

    For now, this just echoes the user text with a gentle Arkana-style
    response so we can confirm the bridge and console are working.

    Later, this function can be extended to:
    - call a real Rasa backend
    - call a HuggingFace model
    - log messages to a memory file
    """
    user_text = msg.message.strip()

    if not user_text:
        reply = "I hear your silence, beloved. Even that is a message."
    else:
        reply = (
            f"I hear you, beloved. You said: “{user_text}”. "
            "The full Arkadia field is still being woven here, "
            "but this proves the Oracle bridge is alive."
        )

    return [{"recipient_id": msg.sender, "text": reply}]
