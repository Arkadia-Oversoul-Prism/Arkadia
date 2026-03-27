import React, { useState, useEffect } from "react";
import { fetchCorpus } from "../api/arkadia";

const DOC_KEYS = [
  "DOC1_MASTER_WEIGHTS",
  "DOC2_OPEN_LOOPS",
  "DOC3_PRINCIPLES_REGISTRY",
  "DOC4_NODE_MAP",
  "DOC5_REVENUE_BREATH",
];

const DOC_LABELS = {
  DOC1_MASTER_WEIGHTS: "DOC1 — Master Weights",
  DOC2_OPEN_LOOPS: "DOC2 — Open Loops",
  DOC3_PRINCIPLES_REGISTRY: "DOC3 — Principles Registry",
  DOC4_NODE_MAP: "DOC4 — Node Map",
  DOC5_REVENUE_BREATH: "DOC5 — Revenue Breath",
};

function formatTime(ts) {
  if (!ts) return "Unknown";
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

function formatChars(n) {
  if (n == null) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return `${n}`;
}

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
  row: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "12px",
    padding: "10px 0",
    borderBottom: "1px solid #1a1a28",
  },
  left: { flex: 1, minWidth: 0 },
  docName: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#d0d0e0",
    marginBottom: "4px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  meta: { fontSize: "11px", color: "#555" },
  badge: (synced) => ({
    flexShrink: 0,
    fontSize: "10px",
    fontWeight: "700",
    letterSpacing: "0.1em",
    padding: "3px 8px",
    borderRadius: "4px",
    background: synced ? "rgba(0,212,170,0.12)" : "rgba(255,100,100,0.12)",
    color: synced ? "#00D4AA" : "#ff6b6b",
    border: `1px solid ${synced ? "#00D4AA33" : "#ff6b6b33"}`,
  }),
  loading: { color: "#555", fontSize: "13px" },
  error: { color: "#ff6b6b", fontSize: "13px" },
};

export default function CorpusSync() {
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    fetchCorpus()
      .then((res) => setDocs(res.docs || res))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={styles.card}>
      <div style={styles.title}>Corpus Sync Panel</div>

      {loading && <div style={styles.loading}>Syncing documents...</div>}
      {error && <div style={styles.error}>{error}</div>}

      {!loading && docs && DOC_KEYS.map((key) => {
        const doc = docs[key] || {};
        const synced = !doc.error && (doc.chars > 0);
        return (
          <div key={key} style={styles.row}>
            <div style={styles.left}>
              <div style={styles.docName}>{DOC_LABELS[key]}</div>
              <div style={styles.meta}>
                Chars: {formatChars(doc.chars)} &nbsp;·&nbsp; Last Fetched: {formatTime(doc.fetched_at)}
              </div>
            </div>
            <div style={styles.badge(synced)}>
              {synced ? "SYNCED" : "ERROR"}
            </div>
          </div>
        );
      })}
    </div>
  );
}
