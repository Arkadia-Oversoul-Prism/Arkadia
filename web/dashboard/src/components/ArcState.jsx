import React, { useState, useEffect } from "react";
import { fetchCorpus } from "../api/arkadia";

const BIRTHDAY_SEAL = new Date("2026-03-31T00:00:00");
const ARC_TOTAL_DAYS = 43;

function getDaysRemaining() {
  const now = new Date();
  const diff = BIRTHDAY_SEAL - now;
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function extractOpenLoops(doc2Content) {
  if (!doc2Content) return [];
  const lines = doc2Content.split("\n");
  const loops = [];
  let inSection = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (/open.loop/i.test(trimmed)) inSection = true;
    if (inSection && (trimmed.startsWith("-") || trimmed.startsWith("*") || trimmed.match(/^\d+\./))) {
      const cleaned = trimmed.replace(/^[-*\d.]\s*/, "").trim();
      if (cleaned.length > 4 && loops.length < 8) loops.push(cleaned);
    }
  }
  return loops.length ? loops : ["No active loops detected in DOC2."];
}

function extractDayX(doc1Content) {
  if (!doc1Content) return null;
  const match = doc1Content.match(/Day\s+(\d+)/i);
  return match ? parseInt(match[1]) : null;
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
    marginBottom: "14px",
  },
  dayRow: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#00D4AA",
    marginBottom: "8px",
  },
  sealRow: {
    fontSize: "14px",
    color: "#C9A84C",
    fontWeight: "600",
    marginBottom: "18px",
  },
  loopsLabel: {
    fontSize: "11px",
    letterSpacing: "0.12em",
    color: "#555",
    textTransform: "uppercase",
    marginBottom: "10px",
  },
  loopList: {
    listStyle: "none",
    maxHeight: "160px",
    overflowY: "auto",
    paddingRight: "4px",
  },
  loopItem: {
    fontSize: "13px",
    color: "#b0b0c0",
    padding: "5px 0",
    borderBottom: "1px solid #1a1a28",
    display: "flex",
    gap: "8px",
    alignItems: "flex-start",
  },
  bullet: {
    color: "#00D4AA",
    flexShrink: 0,
    marginTop: "1px",
  },
  loading: { color: "#555", fontSize: "13px" },
  error: { color: "#ff6b6b", fontSize: "13px" },
};

export default function ArcState() {
  const [doc1, setDoc1] = useState(null);
  const [doc2, setDoc2] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCorpus()
      .then((res) => {
        const corpus = res.docs || res;
        setDoc1(corpus.DOC1_MASTER_WEIGHTS?.content || null);
        setDoc2(corpus.DOC2_OPEN_LOOPS?.content || null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const daysLeft = getDaysRemaining();
  const dayX = extractDayX(doc1);
  const loops = extractOpenLoops(doc2);

  return (
    <div style={styles.card}>
      <div style={styles.title}>Arc State & Chronological Flow</div>

      {loading && <div style={styles.loading}>Loading corpus...</div>}
      {error && <div style={styles.error}>{error}</div>}

      {!loading && (
        <>
          <div style={styles.dayRow}>
            Day {dayX !== null ? dayX : "—"} of {ARC_TOTAL_DAYS}
          </div>
          <div style={styles.sealRow}>
            ◈ {daysLeft} Day{daysLeft !== 1 ? "s" : ""} to Birthday Seal — March 31, 2026
          </div>

          <div style={styles.loopsLabel}>Active Open Loops</div>
          <ul style={styles.loopList}>
            {loops.map((loop, i) => (
              <li key={i} style={styles.loopItem}>
                <span style={styles.bullet}>›</span>
                <span>{loop}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
