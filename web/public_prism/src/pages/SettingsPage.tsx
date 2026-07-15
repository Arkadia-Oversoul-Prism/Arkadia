import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

interface ApiKey {
  id: string;
  label: string;
  masked: string;
  added_at: string | null;
  last_used: string | null;
  quota_hit: boolean;
  active: boolean;
}

function KeyRow({
  k,
  onActivate,
  onRemove,
  onResetQuota,
}: {
  k: ApiKey;
  onActivate: (id: string) => void;
  onRemove: (id: string) => void;
  onResetQuota: (id: string) => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      style={{
        padding: "12px 16px",
        background: k.active ? "rgba(0,212,170,0.04)" : "rgba(14,17,32,0.6)",
        border: `1px solid ${
          k.active
            ? "rgba(0,212,170,0.3)"
            : k.quota_hit
            ? "rgba(200,72,72,0.25)"
            : "rgba(255,255,255,0.07)"
        }`,
        borderRadius: 10,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      {/* Status dot */}
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          flexShrink: 0,
          background: k.active
            ? "#00D4AA"
            : k.quota_hit
            ? "#C84848"
            : "rgba(255,255,255,0.2)",
          boxShadow: k.active ? "0 0 6px rgba(0,212,170,0.7)" : "none",
        }}
      />

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <span
            style={{
              fontFamily: "sans-serif",
              fontSize: 12,
              color: k.active ? "#00D4AA" : "rgba(232,232,232,0.75)",
              fontWeight: k.active ? 600 : 400,
            }}
          >
            {k.label}
          </span>
          {k.active && (
            <span
              style={{
                fontSize: 8,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "#00D4AA",
                background: "rgba(0,212,170,0.1)",
                padding: "1px 6px",
                borderRadius: 3,
              }}
            >
              Active
            </span>
          )}
          {k.quota_hit && (
            <span
              style={{
                fontSize: 8,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "#C84848",
                background: "rgba(200,72,72,0.1)",
                padding: "1px 6px",
                borderRadius: 3,
              }}
            >
              Quota hit
            </span>
          )}
        </div>
        <span
          style={{
            fontFamily: "monospace",
            fontSize: 11,
            color: "rgba(232,232,232,0.35)",
          }}
        >
          {k.masked}
        </span>
        {k.last_used && (
          <p style={{ fontFamily: "sans-serif", fontSize: 9, color: "rgba(232,232,232,0.22)", margin: "2px 0 0" }}>
            Last used: {new Date(k.last_used).toLocaleString()}
          </p>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {!k.active && (
          <button
            onClick={() => onActivate(k.id)}
            style={{
              padding: "4px 10px",
              background: "rgba(0,212,170,0.08)",
              border: "1px solid rgba(0,212,170,0.25)",
              borderRadius: 5,
              color: "#00D4AA",
              fontSize: 9,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              cursor: "pointer",
            }}
          >
            Use
          </button>
        )}
        {k.quota_hit && (
          <button
            onClick={() => onResetQuota(k.id)}
            style={{
              padding: "4px 10px",
              background: "rgba(201,168,76,0.08)",
              border: "1px solid rgba(201,168,76,0.25)",
              borderRadius: 5,
              color: "#C9A84C",
              fontSize: 9,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              cursor: "pointer",
            }}
          >
            Reset
          </button>
        )}
        <button
          onClick={() => onRemove(k.id)}
          style={{
            padding: "4px 8px",
            background: "rgba(200,72,72,0.06)",
            border: "1px solid rgba(200,72,72,0.2)",
            borderRadius: 5,
            color: "#C84848",
            fontSize: 10,
            cursor: "pointer",
          }}
        >
          ✕
        </button>
      </div>
    </motion.div>
  );
}

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadKeys() {
    try {
      const res = await fetch(`${API_BASE}/api/keys`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to load keys: ${res.status} ${text.slice(0, 100)}`);
      }
      const data = await res.json();
      setKeys(data.keys || []);
    } catch (e) {
      console.error('loadKeys error:', e);
      setError(e instanceof Error ? e.message : "Could not load keys");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadKeys();
  }, []);

  async function addKey() {
    if (!newKey.trim()) return;
    setAdding(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: newKey.trim(), label: newLabel.trim() || undefined }),
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Server returned non-JSON: ${res.status} ${text.slice(0, 100)}`);
      }
      if (!res.ok) throw new Error(data.detail || "Failed to add key");
      setNewKey("");
      setNewLabel("");
      setSuccess(`Key "${data.label}" added.`);
      await loadKeys();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error adding key");
    } finally {
      setAdding(false);
    }
  }

  async function activateKey(id: string) {
    setError("");
    await fetch(`${API_BASE}/api/keys/${id}/activate`, { method: "PATCH" });
    await loadKeys();
    setSuccess("Active key switched.");
  }

  async function removeKey(id: string) {
    setError("");
    await fetch(`${API_BASE}/api/keys/${id}`, { method: "DELETE" });
    await loadKeys();
    setSuccess("Key removed.");
  }

  async function resetQuota(id: string) {
    await fetch(`${API_BASE}/api/keys/${id}/reset-quota`, { method: "PATCH" });
    await loadKeys();
    setSuccess("Quota reset — key is active again.");
  }

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "24px 16px 60px" }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 18 }}>⚙</span>
          <h2
            style={{
              fontFamily: "sans-serif",
              fontSize: 16,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: "#C9A84C",
              margin: 0,
            }}
          >
            Settings
          </h2>
        </div>
        <p style={{ fontFamily: "sans-serif", fontSize: 12, color: "rgba(232,232,232,0.4)", margin: "0 0 28px" }}>
          Manage Gemini API keys. When a key hits its quota limit, Arkana automatically
          rotates to the next available key.
        </p>
      </motion.div>

      {/* Feedback */}
      <AnimatePresence>
        {(error || success) && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              padding: "10px 14px",
              borderRadius: 8,
              marginBottom: 16,
              background: error ? "rgba(200,72,72,0.08)" : "rgba(0,212,170,0.07)",
              border: `1px solid ${error ? "rgba(200,72,72,0.3)" : "rgba(0,212,170,0.25)"}`,
              color: error ? "#C84848" : "#00D4AA",
              fontFamily: "sans-serif",
              fontSize: 12,
            }}
          >
            {error || success}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add key form */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        style={{
          padding: "16px",
          background: "rgba(14,17,32,0.7)",
          border: "1px solid rgba(201,168,76,0.15)",
          borderRadius: 12,
          marginBottom: 20,
        }}
      >
        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 9,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "rgba(201,168,76,0.55)",
            margin: "0 0 12px",
          }}
        >
          Add Gemini API Key
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <input
            type="text"
            placeholder="Label (e.g. Key 2, Backup)"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            style={{
              padding: "9px 12px",
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 7,
              color: "rgba(232,232,232,0.8)",
              fontFamily: "sans-serif",
              fontSize: 12,
              outline: "none",
            }}
          />
          <input
            type="password"
            placeholder="AIza… (paste your Gemini API key)"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addKey()}
            style={{
              padding: "9px 12px",
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 7,
              color: "rgba(232,232,232,0.8)",
              fontFamily: "monospace",
              fontSize: 12,
              outline: "none",
            }}
          />
          <button
            onClick={addKey}
            disabled={adding || !newKey.trim()}
            style={{
              padding: "10px",
              background:
                adding || !newKey.trim()
                  ? "rgba(201,168,76,0.05)"
                  : "rgba(201,168,76,0.1)",
              border: "1px solid rgba(201,168,76,0.3)",
              borderRadius: 7,
              color: "#C9A84C",
              fontFamily: "sans-serif",
              fontSize: 10,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              cursor: adding || !newKey.trim() ? "not-allowed" : "pointer",
            }}
          >
            {adding ? "Adding…" : "+ Add Key"}
          </button>
        </div>
      </motion.div>

      {/* Key list */}
      <div>
        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 9,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "rgba(0,212,170,0.45)",
            margin: "0 0 10px",
          }}
        >
          Stored Keys ({keys.length})
        </p>
        {loading ? (
          <p style={{ fontFamily: "sans-serif", fontSize: 11, color: "rgba(232,232,232,0.3)" }}>
            Loading…
          </p>
        ) : keys.length === 0 ? (
          <p style={{ fontFamily: "sans-serif", fontSize: 11, color: "rgba(232,232,232,0.3)" }}>
            No keys stored yet. Add your Gemini API key above.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <AnimatePresence>
              {keys.map((k) => (
                <KeyRow
                  key={k.id}
                  k={k}
                  onActivate={activateKey}
                  onRemove={removeKey}
                  onResetQuota={resetQuota}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{
          marginTop: 28,
          padding: "14px 16px",
          background: "rgba(14,17,32,0.5)",
          border: "1px solid rgba(255,255,255,0.05)",
          borderRadius: 10,
        }}
      >
        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 9,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "rgba(232,232,232,0.25)",
            margin: "0 0 8px",
          }}
        >
          How it works
        </p>
        {[
          "Keys are stored locally in data/api_keys.json — never sent to third parties.",
          "When a key returns a 429 quota error, Arkana auto-rotates to the next key.",
          "You can add up to any number of keys and switch manually at any time.",
          "Get keys at aistudio.google.com/app/apikey",
        ].map((line, i) => (
          <p
            key={i}
            style={{
              fontFamily: "sans-serif",
              fontSize: 11,
              color: "rgba(232,232,232,0.35)",
              margin: i < 3 ? "0 0 5px" : 0,
              lineHeight: 1.6,
            }}
          >
            · {line}
          </p>
        ))}
      </motion.div>
    </div>
  );
}
