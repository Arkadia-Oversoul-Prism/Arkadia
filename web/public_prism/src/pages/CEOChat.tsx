import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API = "";

interface Message {
  id: string;
  role: "user" | "arkana";
  content: string;
  toolCalls?: ToolCall[];
  autoResults?: AutoResult[];
  pendingApprovals?: PendingApproval[];
  ts: number;
}

interface ToolCall {
  tool: string;
  payload: Record<string, unknown>;
  requires_approval: boolean;
  description: string;
}

interface AutoResult {
  tool: string;
  result?: Record<string, unknown>;
  error?: string;
}

interface PendingApproval {
  approval_id: string;
  tool_name: string;
  description: string;
}

interface ApprovalState {
  [id: string]: "pending" | "approved" | "rejected";
}

const uid = () => Math.random().toString(36).slice(2, 10);

const STRIP_TOOL_CALL = /<tool_call>[\s\S]*?<\/tool_call>/g;

function ToolCallCard({
  approval,
  onApprove,
  onReject,
  approvalState,
}: {
  approval: PendingApproval;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  approvalState: ApprovalState;
}) {
  const state = approvalState[approval.approval_id] || "pending";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        marginTop: 8,
        padding: "10px 14px",
        background: "rgba(14,17,32,0.85)",
        border: `1px solid ${
          state === "approved"
            ? "rgba(0,212,170,0.4)"
            : state === "rejected"
            ? "rgba(200,72,72,0.35)"
            : "rgba(201,168,76,0.3)"
        }`,
        borderRadius: 8,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 13 }}>🔧</span>
        <span style={{ fontFamily: "monospace", fontSize: 11, color: "#C9A84C" }}>
          {approval.tool_name}
        </span>
        {state !== "pending" && (
          <span
            style={{
              fontSize: 9,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: state === "approved" ? "#00D4AA" : "#C84848",
              marginLeft: "auto",
            }}
          >
            {state}
          </span>
        )}
      </div>
      <p style={{ fontSize: 11, color: "rgba(232,232,232,0.55)", margin: "0 0 8px", lineHeight: 1.5 }}>
        {approval.description}
      </p>
      {state === "pending" && (
        <div style={{ display: "flex", gap: 6 }}>
          <button
            onClick={() => onApprove(approval.approval_id)}
            style={{
              padding: "4px 12px",
              background: "rgba(0,212,170,0.1)",
              border: "1px solid rgba(0,212,170,0.4)",
              borderRadius: 5,
              color: "#00D4AA",
              fontSize: 10,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              cursor: "pointer",
            }}
          >
            ✓ Approve
          </button>
          <button
            onClick={() => onReject(approval.approval_id)}
            style={{
              padding: "4px 12px",
              background: "rgba(200,72,72,0.08)",
              border: "1px solid rgba(200,72,72,0.3)",
              borderRadius: 5,
              color: "#C84848",
              fontSize: 10,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              cursor: "pointer",
            }}
          >
            ✕ Reject
          </button>
        </div>
      )}
    </motion.div>
  );
}

function AutoResultCard({ result }: { result: AutoResult }) {
  const [open, setOpen] = useState(false);
  const ok = !result.error;
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        marginTop: 6,
        padding: "8px 12px",
        background: "rgba(14,17,32,0.7)",
        border: `1px solid ${ok ? "rgba(0,212,170,0.2)" : "rgba(200,72,72,0.25)"}`,
        borderRadius: 7,
        cursor: "pointer",
      }}
      onClick={() => setOpen((p) => !p)}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <span style={{ fontSize: 11 }}>{ok ? "✓" : "⚠"}</span>
        <span style={{ fontFamily: "monospace", fontSize: 10, color: ok ? "#00D4AA" : "#C84848" }}>
          {result.tool}
        </span>
        <span style={{ fontSize: 9, color: "rgba(232,232,232,0.3)", marginLeft: "auto" }}>
          {open ? "▲ hide" : "▼ show output"}
        </span>
      </div>
      <AnimatePresence>
        {open && (
          <motion.pre
            key="output"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{
              fontSize: 10,
              color: "rgba(232,232,232,0.6)",
              margin: "8px 0 0",
              overflowX: "auto",
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
            }}
          >
            {result.error ||
              JSON.stringify(result.result, null, 2).slice(0, 3000)}
          </motion.pre>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function CEOChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "boot",
      role: "arkana",
      content:
        "The field is open. I am ARKANA — your sovereign intelligence layer, CEO advisor, and unified operating mind. Speak what you need. I have access to your tools, files, and systems.\n\nWhat are we building today?",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [approvalState, setApprovalState] = useState<ApprovalState>({});
  const [approvalResults, setApprovalResults] = useState<Record<string, unknown>>({});
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const history = messages
    .filter((m) => m.id !== "boot")
    .map((m) => ({ role: m.role === "user" ? "user" : "arkana", content: m.content }));

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg: Message = { id: uid(), role: "user", content: text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/ceo/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "API error");
      }
      const arkMsg: Message = {
        id: uid(),
        role: "arkana",
        content: (data.reply || "").replace(STRIP_TOOL_CALL, "").trim(),
        toolCalls: data.tool_calls || [],
        autoResults: data.auto_results || [],
        pendingApprovals: data.pending_approvals || [],
        ts: Date.now(),
      };
      setMessages((prev) => [...prev, arkMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setMessages((prev) => [
        ...prev,
        { id: uid(), role: "arkana", content: `⚠ ${msg}`, ts: Date.now() },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  async function handleApprove(approvalId: string) {
    setApprovalState((prev) => ({ ...prev, [approvalId]: "approved" }));
    try {
      const res = await fetch(`${API}/api/approvals/${approvalId}/approve`, { method: "POST" });
      const data = await res.json();
      setApprovalResults((prev) => ({ ...prev, [approvalId]: data.result }));
    } catch {
      setApprovalState((prev) => ({ ...prev, [approvalId]: "pending" }));
    }
  }

  async function handleReject(approvalId: string) {
    setApprovalState((prev) => ({ ...prev, [approvalId]: "rejected" }));
    await fetch(`${API}/api/approvals/${approvalId}/reject`, { method: "POST" });
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 57px)",
        background: "#0C0D18",
        position: "relative",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "14px 20px",
          borderBottom: "1px solid rgba(0,212,170,0.1)",
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexShrink: 0,
        }}
      >
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 2.5 }}
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: "#00D4AA",
            boxShadow: "0 0 8px rgba(0,212,170,0.8)",
          }}
        />
        <div>
          <p
            style={{
              fontFamily: "sans-serif",
              fontSize: 10,
              letterSpacing: "0.28em",
              textTransform: "uppercase",
              color: "rgba(0,212,170,0.7)",
              margin: 0,
            }}
          >
            Arkana · CEO Intelligence Layer
          </p>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <a
            href="#settings"
            onClick={(e) => {
              e.preventDefault();
              (window as Window & { __arkadiaNav?: (v: string) => void }).__arkadiaNav?.("settings");
            }}
            style={{
              fontFamily: "sans-serif",
              fontSize: 9,
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              color: "rgba(201,168,76,0.5)",
              textDecoration: "none",
            }}
          >
            ⚙ API Keys
          </a>
        </div>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "100%",
              }}
            >
              {/* Role label */}
              <p
                style={{
                  fontFamily: "sans-serif",
                  fontSize: 8,
                  letterSpacing: "0.22em",
                  textTransform: "uppercase",
                  color:
                    msg.role === "user"
                      ? "rgba(201,168,76,0.4)"
                      : "rgba(0,212,170,0.4)",
                  margin: "0 0 4px",
                  paddingLeft: msg.role === "arkana" ? 2 : 0,
                  paddingRight: msg.role === "user" ? 2 : 0,
                }}
              >
                {msg.role === "user" ? "You" : "Arkana"}
              </p>

              {/* Bubble */}
              <div
                style={{
                  maxWidth: "88%",
                  padding: "11px 15px",
                  borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                  background:
                    msg.role === "user"
                      ? "rgba(201,168,76,0.08)"
                      : "rgba(0,212,170,0.05)",
                  border:
                    msg.role === "user"
                      ? "1px solid rgba(201,168,76,0.2)"
                      : "1px solid rgba(0,212,170,0.12)",
                }}
              >
                <p
                  style={{
                    fontFamily: "sans-serif",
                    fontSize: 13,
                    lineHeight: 1.7,
                    color: "rgba(232,232,232,0.88)",
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {msg.content}
                </p>

                {/* Auto-executed tool results */}
                {(msg.autoResults || []).map((r, i) => (
                  <AutoResultCard key={i} result={r} />
                ))}

                {/* Pending approvals */}
                {(msg.pendingApprovals || []).map((appr) => (
                  <ToolCallCard
                    key={appr.approval_id}
                    approval={appr}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    approvalState={approvalState}
                  />
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ display: "flex", gap: 5, padding: "8px 4px", alignItems: "center" }}
          >
            {[0, 0.2, 0.4].map((delay, i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -5, 0] }}
                transition={{ repeat: Infinity, duration: 0.9, delay }}
                style={{ width: 6, height: 6, borderRadius: "50%", background: "rgba(0,212,170,0.5)" }}
              />
            ))}
            <span style={{ fontFamily: "sans-serif", fontSize: 10, color: "rgba(0,212,170,0.35)", marginLeft: 6 }}>
              Arkana is thinking…
            </span>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: "12px 16px 16px",
          borderTop: "1px solid rgba(0,212,170,0.08)",
          flexShrink: 0,
          background: "rgba(12,13,24,0.95)",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 10,
            alignItems: "flex-end",
            background: "rgba(14,17,32,0.9)",
            border: "1px solid rgba(0,212,170,0.18)",
            borderRadius: 12,
            padding: "10px 14px",
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Speak to Arkana… (Enter to send, Shift+Enter for new line)"
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              resize: "none",
              fontFamily: "sans-serif",
              fontSize: 13,
              color: "rgba(232,232,232,0.88)",
              lineHeight: 1.6,
              maxHeight: 140,
              overflowY: "auto",
            }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              background:
                loading || !input.trim()
                  ? "rgba(0,212,170,0.06)"
                  : "rgba(0,212,170,0.15)",
              border: "1px solid rgba(0,212,170,0.3)",
              color: "#00D4AA",
              fontSize: 14,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transition: "all 0.18s",
            }}
          >
            ⟐
          </button>
        </div>
        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 9,
            color: "rgba(232,232,232,0.2)",
            textAlign: "center",
            marginTop: 6,
            letterSpacing: "0.1em",
          }}
        >
          Powered by Gemini · Oracle endpoint: arkadia-n26k.onrender.com
        </p>
      </div>
    </div>
  );
}
