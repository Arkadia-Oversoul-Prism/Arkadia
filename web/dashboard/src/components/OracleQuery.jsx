import React, { useState } from "react";
import { postOracleQuery } from "../api/arkadia";

const styles = {
  card: {
    background: "#12121A",
    border: "1px solid #1e1e2e",
    borderRadius: "8px",
    padding: "20px 24px",
  },
  title: {
    fontSize: "11px",
    letterSpacing: "0.15em",
    color: "#666",
    textTransform: "uppercase",
    marginBottom: "16px",
  },
  textarea: {
    width: "100%",
    minHeight: "80px",
    background: "#0d0d18",
    border: "1px solid #2a2a3e",
    borderRadius: "6px",
    color: "#d0d0e0",
    fontSize: "14px",
    padding: "12px",
    resize: "vertical",
    fontFamily: "Arial, Helvetica, sans-serif",
    outline: "none",
    lineHeight: "1.5",
    marginBottom: "12px",
    transition: "border-color 0.2s",
  },
  button: (loading) => ({
    background: loading ? "#0a3d30" : "#00D4AA",
    color: loading ? "#00D4AA" : "#0A0A0F",
    border: "none",
    borderRadius: "6px",
    padding: "10px 22px",
    fontSize: "13px",
    fontWeight: "700",
    letterSpacing: "0.08em",
    cursor: loading ? "not-allowed" : "pointer",
    transition: "all 0.2s",
    opacity: loading ? 0.7 : 1,
  }),
  resultBox: {
    marginTop: "18px",
    background: "#0d0d18",
    border: "1px solid #2a2a3e",
    borderRadius: "6px",
    padding: "14px 16px",
  },
  replyText: {
    fontSize: "14px",
    color: "#c8c8d8",
    lineHeight: "1.7",
    whiteSpace: "pre-wrap",
    marginBottom: "12px",
  },
  metaRow: {
    display: "flex",
    gap: "16px",
    flexWrap: "wrap",
    marginTop: "10px",
    paddingTop: "10px",
    borderTop: "1px solid #1e1e2e",
  },
  metaItem: { fontSize: "12px", color: "#555" },
  metaValue: { color: "#00D4AA", fontWeight: "600" },
  patternTag: {
    display: "inline-block",
    background: "rgba(201,168,76,0.12)",
    border: "1px solid rgba(201,168,76,0.3)",
    color: "#C9A84C",
    borderRadius: "4px",
    fontSize: "11px",
    padding: "2px 8px",
    margin: "3px 3px 0 0",
  },
  error: { color: "#ff6b6b", fontSize: "13px", marginTop: "10px" },
};

export default function OracleQuery() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    const trimmed = message.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await postOracleQuery(trimmed);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit();
  };

  const patterns = result?.patterns || [];

  return (
    <div style={styles.card}>
      <div style={styles.title}>Oracle Query Interface</div>

      <textarea
        style={styles.textarea}
        placeholder="Speak your query to the Oracle... (Ctrl+Enter to send)"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKey}
        data-testid="input-oracle-query"
      />

      <button
        style={styles.button(loading)}
        onClick={handleSubmit}
        disabled={loading || !message.trim()}
        data-testid="button-send-oracle"
      >
        {loading ? "Consulting..." : "Send to Oracle"}
      </button>

      {error && <div style={styles.error}>{error}</div>}

      {result && (
        <div style={styles.resultBox}>
          <div style={styles.replyText}>
            {result.reply || result.response || result.message || JSON.stringify(result)}
          </div>

          <div style={styles.metaRow}>
            {result.resonance != null && (
              <div style={styles.metaItem}>
                Resonance: <span style={styles.metaValue}>{(result.resonance * 100).toFixed(0)}%</span>
              </div>
            )}
            {result.status && (
              <div style={styles.metaItem}>
                Status: <span style={styles.metaValue}>{result.status}</span>
              </div>
            )}
          </div>

          {patterns.length > 0 && (
            <div style={{ marginTop: "10px" }}>
              {patterns.map((p, i) => (
                <span key={i} style={styles.patternTag}>{p}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
