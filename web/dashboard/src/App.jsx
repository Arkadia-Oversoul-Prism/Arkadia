import React from "react";
import GlobalStatus from "./components/GlobalStatus";
import ArcState from "./components/ArcState";
import CorpusSync from "./components/CorpusSync";
import OracleQuery from "./components/OracleQuery";
import PatternStream from "./components/PatternStream";

const styles = {
  app: {
    minHeight: "100vh",
    background: "#0A0A0F",
    color: "#e0e0e0",
    fontFamily: "Arial, Helvetica, sans-serif",
  },
  header: {
    borderBottom: "1px solid #1a1a28",
    padding: "18px 32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    background: "#0d0d18",
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
  },
  logo: {
    fontSize: "20px",
    fontWeight: "800",
    letterSpacing: "0.2em",
    color: "#00D4AA",
    textTransform: "uppercase",
  },
  logoSub: {
    fontSize: "11px",
    letterSpacing: "0.15em",
    color: "#444",
    textTransform: "uppercase",
    paddingLeft: "14px",
    borderLeft: "1px solid #2a2a3e",
  },
  headerRight: {
    fontSize: "11px",
    color: "#333",
    letterSpacing: "0.08em",
  },
  main: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "28px 24px 48px",
    display: "grid",
    gap: "20px",
  },
  topRow: {
    display: "grid",
    gridTemplateColumns: "260px 1fr",
    gap: "20px",
  },
  midRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "20px",
  },
  fullRow: {
    display: "grid",
    gridTemplateColumns: "1fr",
  },
};

export default function App() {
  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>Arkadia</div>
          <div style={styles.logoSub}>Nexus Live Dashboard</div>
        </div>
        <div style={styles.headerRight}>CYCLE 15 · IDENTITY ARCHITECTURE</div>
      </header>

      <main style={styles.main}>
        <div style={styles.topRow}>
          <GlobalStatus />
          <ArcState />
        </div>

        <div style={styles.midRow}>
          <CorpusSync />
          <OracleQuery />
        </div>

        <div style={styles.fullRow}>
          <PatternStream />
        </div>
      </main>
    </div>
  );
}
