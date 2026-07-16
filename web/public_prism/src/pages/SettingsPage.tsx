import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE } from "../lib/apiConfig";

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

interface ProviderKey {
  provider: string;
  label: string | null;
  masked: string | null;
  added_at: string | null;
  source: "stored" | "env" | "none";
}

const PROVIDER_META: Record<string, { label: string; color: string; placeholder: string; hint: string }> = {
  gemini:   { label: "Google Gemini",  color: "#4A90D9", placeholder: "AIza…",        hint: "aistudio.google.com/app/apikey" },
  openai:   { label: "OpenAI GPT",     color: "#19C37D", placeholder: "sk-…",          hint: "platform.openai.com/api-keys" },
  claude:   { label: "Anthropic Claude", color: "#D4875F", placeholder: "sk-ant-…",    hint: "console.anthropic.com/settings/keys" },
  deepseek: { label: "DeepSeek",       color: "#7B8CDE", placeholder: "…",             hint: "platform.deepseek.com" },
};

export default function SettingsPage() {
  const [providerKeys, setProviderKeys] = useState<ProviderKey[]>([]);
  const [ttsKeys, setTtsKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [newProviderKey, setNewProviderKey] = useState("");
  const [newProviderLabel, setNewProviderLabel] = useState("");
  const [newTtsKey, setNewTtsKey] = useState("");
  const [newTtsLabel, setNewTtsLabel] = useState("");
  const [adding, setAdding] = useState(false);
  const [addingTts, setAddingTts] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [ttsError, setTtsError] = useState("");
  const [ttsSuccess, setTtsSuccess] = useState("");

  async function loadProviderKeys() {
    try {
      const res = await fetch(`${API_BASE}/api/provider-keys`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setProviderKeys(data.keys || []);
    } catch (e) {
      console.error('loadProviderKeys error:', e);
      setError(e instanceof Error ? e.message : "Could not load provider keys");
    } finally {
      setLoading(false);
    }
  }

  async function loadTtsKeys() {
    try {
      const res = await fetch(`${API_BASE}/api/tts/keys`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to load TTS keys: ${res.status} ${text.slice(0, 100)}`);
      }
      const data = await res.json();
      setTtsKeys(data.keys || []);
    } catch (e) {
      console.error('loadTtsKeys error:', e);
      setTtsError(e instanceof Error ? e.message : "Could not load TTS keys");
    }
  }

  useEffect(() => {
    loadProviderKeys();
    loadTtsKeys();
  }, []);

  async function addProviderKey() {
    if (!newProviderKey.trim()) return;
    setAdding(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/provider-keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: selectedProvider,
          key: newProviderKey.trim(),
          label: newProviderLabel.trim() || undefined,
        }),
      });
      const text = await res.text();
      let data: { label?: string; detail?: string };
      try { data = JSON.parse(text); } catch { throw new Error(`Server returned non-JSON: ${res.status} ${text.slice(0, 100)}`); }
      if (!res.ok) throw new Error(data.detail || "Failed to add key");
      setNewProviderKey("");
      setNewProviderLabel("");
      setSuccess(`${PROVIDER_META[selectedProvider]?.label ?? selectedProvider} key saved.`);
      await loadProviderKeys();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error adding key");
    } finally {
      setAdding(false);
    }
  }

  async function removeProviderKey(provider: string) {
    setError("");
    await fetch(`${API_BASE}/api/provider-keys/${provider}`, { method: "DELETE" });
    setSuccess(`${PROVIDER_META[provider]?.label ?? provider} key removed.`);
    await loadProviderKeys();
  }

  async function resetProviderQuota(provider: string) {
    setError("");
    await fetch(`${API_BASE}/api/provider-keys/${provider}/reset-quota`, { method: "PATCH" });
    setSuccess(`${PROVIDER_META[provider]?.label ?? provider} quota reset — key is active again.`);
    await loadProviderKeys();
  }

  async function addTtsKey() {
    if (!newTtsKey.trim()) return;
    setAddingTts(true);
    setTtsError("");
    setTtsSuccess("");
    try {
      const res = await fetch(`${API_BASE}/api/tts/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: newTtsKey.trim(), label: newTtsLabel.trim() || undefined }),
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Server returned non-JSON: ${res.status} ${text.slice(0, 100)}`);
      }
      if (!res.ok) throw new Error(data.detail || "Failed to add TTS key");
      setNewTtsKey("");
      setNewTtsLabel("");
      setTtsSuccess(`TTS Key "${data.label}" added.`);
      await loadTtsKeys();
    } catch (e: unknown) {
      setTtsError(e instanceof Error ? e.message : "Error adding TTS key");
    } finally {
      setAddingTts(false);
    }
  }

  async function activateTtsKey(id: string) {
    setTtsError("");
    await fetch(`${API_BASE}/api/tts/keys/${id}/activate`, { method: "PATCH" });
    await loadTtsKeys();
    setTtsSuccess("Active TTS key switched.");
  }

  async function removeTtsKey(id: string) {
    setTtsError("");
    await fetch(`${API_BASE}/api/tts/keys/${id}`, { method: "DELETE" });
    await loadTtsKeys();
    setTtsSuccess("TTS Key removed.");
  }

  async function resetTtsQuota(id: string) {
    await fetch(`${API_BASE}/api/tts/keys/${id}/reset-quota`, { method: "PATCH" });
    await loadTtsKeys();
    setTtsSuccess("TTS Quota reset — key is active again.");
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
          Add API keys for any AI provider — Arkana will use the first one that's configured.
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

      {/* Provider key status grid */}
      {!loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
          {providerKeys.map((pk) => {
            const meta = PROVIDER_META[pk.provider];
            const hasKey = pk.source !== "none";
            const isQuotaHit = pk.quota_hit;
            return (
              <motion.div
                key={pk.provider}
                layout
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 14px",
                  background: isQuotaHit ? "rgba(200,72,72,0.08)" : (hasKey ? "rgba(14,17,32,0.7)" : "rgba(14,17,32,0.4)"),
                  border: `1px solid ${isQuotaHit ? "rgba(200,72,72,0.4)" : (hasKey ? `${meta?.color}28` : "rgba(255,255,255,0.05)")}`,
                  borderRadius: 10,
                }}
              >
                <div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                  background: isQuotaHit ? "#C84848" : (hasKey ? (meta?.color ?? "#00D4AA") : "rgba(255,255,255,0.12)"),
                  boxShadow: isQuotaHit ? "0 0 6px #C8484888" : (hasKey ? `0 0 6px ${meta?.color ?? "#00D4AA"}88` : "none") }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: "sans-serif", fontSize: 12,
                    color: isQuotaHit ? "rgba(200,72,72,0.9)" : (hasKey ? "rgba(232,232,232,0.85)" : "rgba(232,232,232,0.35)"),
                    fontWeight: hasKey ? 500 : 400 }}>
                    {meta?.label ?? pk.provider}
                    {pk.source === "env" && (
                      <span style={{ marginLeft: 8, fontSize: 9, letterSpacing: "0.2em",
                        color: meta?.color ?? "#00D4AA", opacity: 0.7,
                        textTransform: "uppercase" }}>env</span>
                    )}
                    {isQuotaHit && (
                      <span style={{ marginLeft: 8, fontSize: 9, letterSpacing: "0.2em",
                        color: "#C84848", textTransform: "uppercase" }}>quota hit</span>
                    )}
                  </div>
                  {hasKey && pk.masked && (
                    <div style={{ fontFamily: "monospace", fontSize: 10,
                      color: "rgba(232,232,232,0.28)", marginTop: 2 }}>
                      {pk.masked}
                    </div>
                  )}
                </div>
                {pk.source === "stored" && (
                  <div style={{ display: "flex", gap: 6 }}>
                    {isQuotaHit && (
                      <button onClick={() => resetProviderQuota(pk.provider)}
                        style={{ padding: "3px 8px", background: "rgba(201,168,76,0.08)",
                          border: "1px solid rgba(201,168,76,0.25)", borderRadius: 5,
                          color: "#C9A84C", fontSize: 9, letterSpacing: "0.1em",
                          textTransform: "uppercase", cursor: "pointer" }}>
                        Reset
                      </button>
                    )}
                    <button onClick={() => removeProviderKey(pk.provider)}
                      style={{ padding: "3px 8px", background: "rgba(200,72,72,0.06)",
                        border: "1px solid rgba(200,72,72,0.2)", borderRadius: 5,
                        color: "#C84848", fontSize: 10, cursor: "pointer" }}>
                      ✕
                    </button>
                  </div>
                )}
                {!hasKey && (
                  <span style={{ fontSize: 10, color: "rgba(232,232,232,0.2)",
                    fontFamily: "sans-serif" }}>not set</span>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Add provider key form */}
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
        <p style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.22em",
          textTransform: "uppercase", color: "rgba(201,168,76,0.55)", margin: "0 0 12px" }}>
          Add / Replace Provider Key
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Provider selector */}
          <select
            value={selectedProvider}
            onChange={(e) => { setSelectedProvider(e.target.value); setNewProviderKey(""); }}
            style={{
              padding: "9px 12px",
              background: "rgba(0,0,0,0.4)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 7,
              color: "rgba(232,232,232,0.85)",
              fontFamily: "sans-serif",
              fontSize: 12,
              outline: "none",
              cursor: "pointer",
            }}
          >
            {Object.entries(PROVIDER_META).map(([val, m]) => (
              <option key={val} value={val} style={{ background: "#0E1120" }}>{m.label}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Label (optional)"
            value={newProviderLabel}
            onChange={(e) => setNewProviderLabel(e.target.value)}
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
            placeholder={PROVIDER_META[selectedProvider]?.placeholder ?? "API key…"}
            value={newProviderKey}
            onChange={(e) => setNewProviderKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addProviderKey()}
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
          {PROVIDER_META[selectedProvider]?.hint && (
            <p style={{ margin: 0, fontFamily: "sans-serif", fontSize: 10,
              color: "rgba(232,232,232,0.25)" }}>
              Get key → {PROVIDER_META[selectedProvider].hint}
            </p>
          )}
          <button
            onClick={addProviderKey}
            disabled={adding || !newProviderKey.trim()}
            style={{
              padding: "10px",
              background: adding || !newProviderKey.trim() ? "rgba(201,168,76,0.05)" : "rgba(201,168,76,0.1)",
              border: "1px solid rgba(201,168,76,0.3)",
              borderRadius: 7,
              color: "#C9A84C",
              fontFamily: "sans-serif",
              fontSize: 10,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              cursor: adding || !newProviderKey.trim() ? "not-allowed" : "pointer",
            }}
          >
            {adding ? "Saving…" : `+ Save ${PROVIDER_META[selectedProvider]?.label ?? "Key"}`}
          </button>
        </div>
      </motion.div>

      {/* TTS Keys Section */}
      <div style={{ marginTop: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
          <span style={{ fontSize: 18 }}>🔊</span>
          <h3 style={{ fontFamily: "sans-serif", fontSize: 14, letterSpacing: "0.18em", textTransform: "uppercase", color: "#B08DE8", margin: 0 }}>
            TTS API Keys
          </h3>
        </div>
        <p style={{ fontFamily: "sans-serif", fontSize: 12, color: "rgba(232,232,232,0.4)", margin: "0 0 20px" }}>
          Text-to-Speech API keys for voice synthesis. When a key hits quota, it auto-switches to the next available key.
        </p>

        {/* TTS Feedback */}
        <AnimatePresence>
          {(ttsError || ttsSuccess) && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                marginBottom: 16,
                background: ttsError ? "rgba(200,72,72,0.08)" : "rgba(0,212,170,0.07)",
                border: `1px solid ${ttsError ? "rgba(200,72,72,0.3)" : "rgba(0,212,170,0.25)"}`,
                color: ttsError ? "#C84848" : "#00D4AA",
                fontFamily: "sans-serif",
                fontSize: 12,
              }}
            >
              {ttsError || ttsSuccess}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Add TTS key form */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          style={{
            padding: "16px",
            background: "rgba(14,17,32,0.7)",
            border: "1px solid rgba(176,141,232,0.15)",
            borderRadius: 12,
            marginBottom: 20,
          }}
        >
          <p style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase", color: "rgba(176,141,232,0.55)", margin: "0 0 12px" }}>
            Add TTS API Key
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <input
              type="text"
              placeholder="Label (e.g. ElevenLabs, Google TTS)"
              value={newTtsLabel}
              onChange={(e) => setNewTtsLabel(e.target.value)}
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
              placeholder="TTS API key…"
              value={newTtsKey}
              onChange={(e) => setNewTtsKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addTtsKey()}
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
              onClick={addTtsKey}
              disabled={addingTts || !newTtsKey.trim()}
              style={{
                padding: "10px",
                background: addingTts || !newTtsKey.trim() ? "rgba(176,141,232,0.05)" : "rgba(176,141,232,0.1)",
                border: "1px solid rgba(176,141,232,0.3)",
                borderRadius: 7,
                color: "#B08DE8",
                fontFamily: "sans-serif",
                fontSize: 10,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                cursor: addingTts || !newTtsKey.trim() ? "not-allowed" : "pointer",
              }}
            >
              {addingTts ? "Adding…" : "+ Add TTS Key"}
            </button>
          </div>
        </motion.div>

        {/* TTS Key list */}
        <div>
          <p style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.22em", textTransform: "uppercase", color: "rgba(176,141,232,0.45)", margin: "0 0 10px" }}>
            Stored TTS Keys ({ttsKeys.length})
          </p>
          {ttsKeys.length === 0 ? (
            <p style={{ fontFamily: "sans-serif", fontSize: 11, color: "rgba(232,232,232,0.3)" }}>
              No TTS keys stored yet. Add your TTS API key above.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <AnimatePresence>
                {ttsKeys.map((k) => (
                  <KeyRow
                    key={k.id}
                    k={k}
                    onActivate={activateTtsKey}
                    onRemove={removeTtsKey}
                    onResetQuota={resetTtsQuota}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
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
          "Keys are stored locally in data/provider_keys.json — never sent to third parties.",
          "Arkana checks providers in priority order: Gemini → OpenAI → Claude → DeepSeek.",
          "You only need one key. Adding more providers gives Arkana fallback options.",
          "Gemini: aistudio.google.com/app/apikey · OpenAI: platform.openai.com/api-keys",
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
