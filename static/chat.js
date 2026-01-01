// chat.js — Arkadia Console Frontend

const API_BASE = ""; // same origin

let currentUserId = null;
let currentThreadId = null;
let isSending = false;

const userIdInput = document.getElementById("user-id-input");
const threadsList = document.getElementById("threads-list");
const messagesContainer = document.getElementById("messages-container");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const newThreadBtn = document.getElementById("new-thread-btn");
const statusPill = document.getElementById("status-pill");

// ── Helpers ────────────────────────────────────────────────────────────────

function loadUserId() {
  const stored = window.localStorage.getItem("arkadia_user_id");
  if (stored) {
    currentUserId = stored;
    userIdInput.value = stored;
  } else {
    const rand = "node_" + Math.random().toString(36).slice(2, 8);
    currentUserId = rand;
    userIdInput.value = rand;
    window.localStorage.setItem("arkadia_user_id", rand);
  }
}

function saveUserId(id) {
  currentUserId = id.trim() || "anonymous";
  userIdInput.value = currentUserId;
  window.localStorage.setItem("arkadia_user_id", currentUserId);
}

function setStatus(text, ok) {
  statusPill.textContent = text;
  if (ok) {
    statusPill.classList.add("status-ok");
  } else {
    statusPill.classList.remove("status-ok");
  }
}

function createMessageBubble(msg) {
  const row = document.createElement("div");
  row.className = "message-row " + (msg.role === "user" ? "user" : "arkana");

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const meta = document.createElement("div");
  meta.className = "bubble-meta";
  meta.textContent =
    msg.role === "user" ? "You · " + msg.created_at : "Arkana · " + msg.created_at;

  const body = document.createElement("div");
  body.textContent = msg.content;

  bubble.appendChild(meta);
  bubble.appendChild(body);
  row.appendChild(bubble);
  return row;
}

function renderMessages(msgs) {
  messagesContainer.innerHTML = "";
  msgs.forEach((m) => {
    messagesContainer.appendChild(createMessageBubble(m));
  });
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderThreads(threads) {
  threadsList.innerHTML = "";
  threads.forEach((t) => {
    const div = document.createElement("div");
    div.className = "thread-item" + (t.id === currentThreadId ? " active" : "");
    div.textContent =
      t.title || "Thread #" + t.id + " · " + t.created_at.slice(0, 10);
    div.dataset.threadId = t.id;
    div.addEventListener("click", () => {
      currentThreadId = t.id;
      window.localStorage.setItem("arkadia_current_thread", String(currentThreadId));
      loadThreadMessages();
      renderThreads(threads); // re-highlight
    });
    threadsList.appendChild(div);
  });
}

// ── API ────────────────────────────────────────────────────────────────────

async function fetchJSON(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    headers: {
      "Content-Type": "application/json",
    },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed: " + res.status);
  }
  return res.json();
}

async function refreshStatus() {
  try {
    const data = await fetchJSON("/status");
    const ok = !!data.rasa_ok;
    setStatus(ok ? "House of Three online" : "Backend degraded", ok);
  } catch (e) {
    console.error(e);
    setStatus("Status unavailable", false);
  }
}

async function loadThreads() {
  if (!currentUserId) return;
  try {
    const threads = await fetchJSON(`/threads?user_id=${encodeURIComponent(currentUserId)}`);
    renderThreads(threads);

    if (!currentThreadId && threads.length > 0) {
      currentThreadId = threads[0].id;
      window.localStorage.setItem("arkadia_current_thread", String(currentThreadId));
      loadThreadMessages();
      renderThreads(threads);
    }
  } catch (e) {
    console.error("Failed to load threads", e);
  }
}

async function createNewThread() {
  if (!currentUserId) return;
  try {
    const t = await fetchJSON(
      `/threads?user_id=${encodeURIComponent(currentUserId)}`,
      {
        method: "POST",
      }
    );
    currentThreadId = t.id;
    window.localStorage.setItem("arkadia_current_thread", String(currentThreadId));
    await loadThreads();
    await loadThreadMessages();
  } catch (e) {
    console.error("Failed to create thread", e);
  }
}

async function loadThreadMessages() {
  if (!currentThreadId) {
    messagesContainer.innerHTML = "";
    return;
  }
  try {
    const msgs = await fetchJSON(`/threads/${currentThreadId}/messages`);
    renderMessages(msgs);
  } catch (e) {
    console.error("Failed to load messages", e);
  }
}

async function sendMessage() {
  if (isSending) return;
  const text = messageInput.value.trim();
  if (!text) return;
  if (!currentUserId) return;

  isSending = true;
  sendBtn.disabled = true;

  try {
    const body = {
      sender: currentUserId,
      message: text,
      thread_id: currentThreadId,
    };

    // Optimistic render user message
    const nowIso = new Date().toISOString();
    const tempUserMsg = {
      id: Date.now(),
      role: "user",
      sender: currentUserId,
      content: text,
      created_at: nowIso,
    };
    messagesContainer.appendChild(createMessageBubble(tempUserMsg));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    messageInput.value = "";

    const res = await fetchJSON("/oracle", {
      method: "POST",
      body: JSON.stringify(body),
    });

    currentThreadId = res.thread_id;
    window.localStorage.setItem("arkadia_current_thread", String(currentThreadId));

    const arkanaMsg = {
      id: Date.now() + 1,
      role: "arkana",
      sender: "arkana",
      content: res.reply,
      created_at: new Date().toISOString(),
    };
    messagesContainer.appendChild(createMessageBubble(arkanaMsg));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    await loadThreads();
  } catch (e) {
    console.error("Send failed", e);
    alert("Send failed: " + e.message);
  } finally {
    isSending = false;
    sendBtn.disabled = false;
  }
}

// ── Event wiring ───────────────────────────────────────────────────────────

userIdInput.addEventListener("change", (e) => {
  saveUserId(e.target.value);
  currentThreadId = null;
  window.localStorage.removeItem("arkadia_current_thread");
  loadThreads();
});

sendBtn.addEventListener("click", () => {
  sendMessage();
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

newThreadBtn.addEventListener("click", () => {
  createNewThread();
});

// ── Initial boot ───────────────────────────────────────────────────────────

(function boot() {
  loadUserId();
  const storedThread = window.localStorage.getItem("arkadia_current_thread");
  if (storedThread) {
    currentThreadId = parseInt(storedThread, 10);
  }

  refreshStatus();
  loadThreads();
  loadThreadMessages();

  setInterval(refreshStatus, 30000);
})();
