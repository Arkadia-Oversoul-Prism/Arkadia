/**
 * Arkadia Operational Dashboard.
 *
 * Self-contained module mounted as a top-level View in the existing
 * navigation. Internal sub-page state is managed locally so URL routing
 * matches the parent app's existing pattern (state-driven, not URL-driven).
 */
import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  LayoutDashboard, ListChecks, Target, Waypoints, Wrench, Activity,
} from "lucide-react"

import Overview from "./Overview"
import Jobs from "./Jobs"
import Goals from "./Goals"
import Traces from "./Traces"
import Tools from "./Tools"
import System from "./System"
import { COLORS } from "./ui"

type DashView =
  | "overview" | "jobs" | "goals" | "traces" | "tools" | "system"

const NAV: { id: DashView; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "jobs",     label: "Jobs",     icon: ListChecks },
  { id: "goals",    label: "Goals",    icon: Target },
  { id: "traces",   label: "Traces",   icon: Waypoints },
  { id: "tools",    label: "Tools",    icon: Wrench },
  { id: "system",   label: "System",   icon: Activity },
]

export default function Dashboard() {
  const [view, setView] = useState<DashView>("overview")
  const [traceJobId, setTraceJobId] = useState<string | null>(null)

  const openTrace = (jobId: string) => {
    setTraceJobId(jobId)
    setView("traces")
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", minHeight: "calc(100vh - 57px)" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: 220,
          borderRight: "1px solid rgba(201,168,76,0.08)",
          background: "rgba(13,13,26,0.55)",
          backdropFilter: "blur(16px)",
          padding: "24px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        <div style={{ padding: "0 8px 18px" }}>
          <p style={{
            fontFamily: "serif", fontSize: 11, letterSpacing: "0.3em",
            textTransform: "uppercase", color: COLORS.gold, margin: 0,
          }}>
            Operational Console
          </p>
          <p style={{
            fontFamily: "sans-serif", fontSize: 10, color: COLORS.muted,
            margin: "4px 0 0", letterSpacing: "0.1em",
          }}>
            Phases 4 → 8
          </p>
        </div>
        {NAV.map((item) => {
          const Icon = item.icon
          const active = view === item.id
          return (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              data-testid={`link-dashboard-${item.id}`}
              style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "10px 12px",
                background: active ? "rgba(0,212,170,0.08)" : "transparent",
                border: active ? "1px solid rgba(0,212,170,0.3)" : "1px solid transparent",
                borderRadius: 10,
                color: active ? COLORS.teal : COLORS.muted,
                fontFamily: "sans-serif",
                fontSize: 11,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                cursor: "pointer",
                transition: "all .15s",
              }}
            >
              <Icon size={14} />
              {item.label}
            </button>
          )
        })}
      </aside>

      {/* Content */}
      <main style={{ padding: "28px 32px 60px", overflow: "auto" }}>
        <header style={{ marginBottom: 22 }}>
          <p style={{
            fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.35em",
            textTransform: "uppercase", color: COLORS.dim, margin: 0,
          }}>
            Arkadia / Dashboard
          </p>
          <h1 style={{
            fontFamily: "serif", fontSize: 26, color: COLORS.text,
            margin: "6px 0 0", letterSpacing: "0.05em",
          }}>
            {NAV.find((n) => n.id === view)?.label}
          </h1>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            {view === "overview" && <Overview />}
            {view === "jobs"     && <Jobs onOpenTrace={openTrace} />}
            {view === "goals"    && <Goals />}
            {view === "traces"   && <Traces openJobId={traceJobId} />}
            {view === "tools"    && <Tools />}
            {view === "system"   && <System />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
