import React from "react";

const styles = {
  card: {
    background: "#12121A",
    border: "1px dashed #1e1e2e",
    borderRadius: "8px",
    padding: "20px 24px",
    opacity: 0.7,
  },
  title: {
    fontSize: "11px",
    letterSpacing: "0.15em",
    color: "#555",
    textTransform: "uppercase",
    marginBottom: "14px",
  },
  heading: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#555",
    marginBottom: "10px",
  },
  placeholder: {
    fontSize: "13px",
    color: "#3a3a4e",
    fontStyle: "italic",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  pulse: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#2a2a3e",
    flexShrink: 0,
  },
};

export default function PatternStream() {
  return (
    <div style={styles.card}>
      <div style={styles.title}>Pattern / Session Stream</div>
      <div style={styles.heading}>Live Field Data</div>
      <div style={styles.placeholder}>
        <div style={styles.pulse} />
        Awaiting live field data...
      </div>
    </div>
  );
}
