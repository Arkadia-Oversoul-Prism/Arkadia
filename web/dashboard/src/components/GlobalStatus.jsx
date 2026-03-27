import React, { useState, useEffect } from "react";
import { fetchHeartbeat } from "../api/arkadia";

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
  row: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  dot: (live) => ({
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    background: live ? "#00D4AA" : "#ff4444",
    boxShadow: live ? "0 0 8px #00D4AA" : "0 0 8px #ff4444",
    flexShrink: 0,
  }),
  status: (live) => ({
    fontSize: "16px",
    fontWeight: "700",
    color: live ? "#00D4AA" : "#ff4444",
    letterSpacing: "0.05em",
  }),
  sub: {
    fontSize: "12px",
    color: "#555",
    marginTop: "8px",
  },
  error: {
    fontSize: "13px",
    color: "#ff6b6b",
    marginTop: "4px",
  },
};

export default function GlobalStatus() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const check = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchHeartbeat();
      setData(result);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const isLive = !error && data;

  return (
    <div style={styles.card}>
      <div style={styles.title}>System Pulse</div>

      {loading && !data && (
        <div style={{ color: "#555", fontSize: "14px" }}>Pinging backend...</div>
      )}

      {!loading || data ? (
        <div style={styles.row}>
          <div style={styles.dot(isLive)} />
          <div style={styles.status(isLive)}>
            Backend: {isLive ? "LIVE" : "OFFLINE"}
          </div>
        </div>
      ) : null}

      {error && <div style={styles.error}>{error}</div>}

      {lastChecked && (
        <div style={styles.sub}>Last checked: {lastChecked}</div>
      )}
    </div>
  );
}
