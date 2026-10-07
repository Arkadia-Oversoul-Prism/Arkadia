import { NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { STANDING_STATES } from "../lib/standing";
import { StandingBanner } from "./ui";

const SURFACES = [
  { to: "/", label: "Spine", index: "01", sub: "causal system" },
  { to: "/inspector", label: "Boundary Inspector", index: "02", sub: "forensic" },
  { to: "/work", label: "Work / Consequence", index: "03", sub: "operational" },
  { to: "/authority", label: "Authority", index: "04", sub: "sovereign control" },
  { to: "/mie-lab", label: "Musical Intention Engine", index: "05", sub: "Gate 05 · visual lab" },
  { to: "/n-atlas-lab", label: "N-ATLAS Developer Lab", index: "06", sub: "PS1 · integration proof" },
];

const TITLES: Record<string, string> = {
  "/": "01 · Spine",
  "/inspector": "02 · Boundary Inspector",
  "/work": "03 · Work / Consequence",
  "/authority": "04 · Authority",
  "/mie-lab": "05 · Musical Intention Engine · Web Lab",
  "/n-atlas-lab": "06 · N-ATLAS Developer Lab",
};

function titleFor(path: string): string {
  if (TITLES[path]) return TITLES[path];
  if (path.startsWith("/boundary/")) return "Boundary Instance";
  return "Arkadia";
}

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">🜂</div>
          <div className="brand-text">
            <span className="brand-title">Arkadia</span>
            <span className="brand-sub">reconciled console</span>
          </div>
        </div>
        <nav className="nav-group">
          <div className="nav-group-title">Surfaces</div>
          {SURFACES.map((s) => (
            <NavLink
              key={s.to}
              to={s.to}
              end={s.to === "/"}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              <span className="nav-index mono">{s.index}</span>
              <span className="nav-label">
                {s.label}
                <span className="nav-sub">{s.sub}</span>
              </span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot tiny faint">
          Derived from existing UI + derived backend console + RECONCILED-BOUNDARY-MAP-01.
          Implementation Gate: foundation only.
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <h1>{titleFor(location.pathname)}</h1>
          <div className="spacer" />
          <span className="topbar-meta tiny mono">ae847dd · reconciled</span>
        </header>

        {/* Standing non-claims: first-class, persistent, never dismissed. */}
        <div className="standing-bar">
          {STANDING_STATES.map((s) => (
            <StandingBanner key={s.id} state={s} />
          ))}
        </div>

        <div className="page">{children}</div>
      </main>
    </div>
  );
}
