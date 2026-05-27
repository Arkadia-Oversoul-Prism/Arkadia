/**
 * Arkadia Intelligence Overview
 * Pulls live data from all available backend endpoints and surfaces
 * real-time insights routed through the Oracle weighting system.
 */
import React, { useEffect, useRef, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useQuery } from "@tanstack/react-query"
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, Cell,
  ResponsiveContainer, CartesianGrid,
} from "recharts"
import {
  api,
  MetricsSnapshot, ArkDateResponse, CodexResponse,
  OpenLoopsResponse, SourcesResponse, HeartbeatResponse,
} from "../../lib/dashboardApi"
import { Card, COLORS, Empty, ErrorBox, Stat, fmtAgo } from "./ui"

// ── Category oracle-weight metadata ─────────────────────────────────────────

const CAT_META: Record<string, { label: string; color: string; weight: string }> = {
  NEURAL_SPINE: { label: "Neural Spine",  color: "#00D4AA", weight: "Highest — always injected into Oracle context" },
  CREATIVE_OS:  { label: "Creative OS",   color: "#C9A84C", weight: "High — scored on query relevance" },
  COLLECTIVE:   { label: "Collective",    color: "#B08DE8", weight: "Medium — community pattern matching" },
  GOVERNANCE:   { label: "Governance",    color: "#6A9FD8", weight: "Medium — structural reference layer" },
  ARCHIVE:      { label: "Archive",       color: "#8B7355", weight: "Low — historical context only" },
  CODEX:        { label: "Codex",         color: "#D4AF37", weight: "Variable — symbolic resonance scoring" },
}

function catColor(cat: string) {
  return CAT_META[cat]?.color ?? "#888"
}
function catLabel(cat: string) {
  return CAT_META[cat]?.label ?? cat.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

// ── Time-series ring buffer ──────────────────────────────────────────────────

type Sample = { t: number; completed: number; failed: number; running: number; pending: number }
const SERIES_CAP = 60

// ── Small helpers ────────────────────────────────────────────────────────────

function pct(n: number, d: number) {
  return d > 0 ? Math.round((n / d) * 1000) / 10 : null
}

function fmtChars(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1000)      return `${(n / 1000).toFixed(1)}k`
  return `${n}`
}

function ResonanceDot({ value }: { value: number }) {
  const hue = value > 0.95 ? 160 : value > 0.7 ? 45 : 0
  const col = `hsl(${hue}, 80%, 55%)`
  return (
    <div style={{ position: "relative", width: 10, height: 10 }}>
      <motion.div
        animate={{ scale: [1, 1.9, 1], opacity: [0.7, 0, 0.7] }}
        transition={{ duration: 2.2, repeat: Infinity }}
        style={{ position: "absolute", inset: 0, borderRadius: "50%", background: col }}
      />
      <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: col }} />
    </div>
  )
}

// ── Main component ───────────────────────────────────────────────────────────

export default function Overview() {
  const seriesRef = useRef<Sample[]>([])

  const { data: metrics, isLoading: mLoad } = useQuery<MetricsSnapshot>({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 5000,
  })
  const { data: heartbeat } = useQuery<HeartbeatResponse>({
    queryKey: ["heartbeat"],
    queryFn: api.heartbeat,
    refetchInterval: 8000,
  })
  const { data: arkDate } = useQuery<ArkDateResponse>({
    queryKey: ["ark-date"],
    queryFn: api.arkDate,
    refetchInterval: 30000,
  })
  const { data: sources } = useQuery<SourcesResponse>({
    queryKey: ["sources"],
    queryFn: api.sources,
    refetchInterval: 60000,
  })
  const { data: codex } = useQuery<CodexResponse>({
    queryKey: ["codex-overview"],
    queryFn: api.codex,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  })
  const { data: loops } = useQuery<OpenLoopsResponse>({
    queryKey: ["open-loops"],
    queryFn: api.openLoops,
    refetchInterval: 60000,
  })

  // Maintain rolling time-series for chart
  useEffect(() => {
    if (!metrics) return
    seriesRef.current = [
      ...seriesRef.current,
      { t: metrics.ts, completed: metrics.jobs.completed, failed: metrics.jobs.failed, pending: metrics.jobs.pending, running: metrics.jobs.running },
    ].slice(-SERIES_CAP)
  }, [metrics])

  // Derive corpus intelligence from codex scrolls
  const corpusIntel = useMemo(() => {
    if (!codex?.scrolls) return null
    const scrolls = Object.values(codex.scrolls)
    const byCategory: Record<string, { count: number; chars: number; label: string; color: string }> = {}
    for (const s of scrolls) {
      if (!byCategory[s.category]) {
        byCategory[s.category] = { count: 0, chars: 0, label: catLabel(s.category), color: catColor(s.category) }
      }
      byCategory[s.category].count++
      byCategory[s.category].chars += s.chars ?? 0
    }
    const sorted = Object.entries(byCategory)
      .map(([cat, v]) => ({ cat, ...v }))
      .sort((a, b) => b.chars - a.chars)

    const topScrolls = scrolls
      .filter(s => !s.error && s.chars > 0)
      .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0) || b.chars - a.chars)
      .slice(0, 5)

    return { sorted, topScrolls, total: scrolls.length, totalChars: codex.total_chars }
  }, [codex])

  // Derive open loops digest
  const loopDigest = useMemo(() => {
    if (!loops?.groups) return null
    const urgent = loops.groups
      .filter(g => g.level === "critical" || g.level === "high")
      .flatMap(g => g.loops.map(l => ({ ...l, level: g.level, color: g.color })))
      .slice(0, 4)
    return { urgent, total: loops.total, groups: loops.groups.length }
  }, [loops])

  const series = seriesRef.current.map(s => ({
    time: new Date(s.t * 1000).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    completed: s.completed, failed: s.failed, running: s.running, pending: s.pending,
  }))

  const liveSources = sources?.sources.filter(s => s.live) ?? []
  const configuredSources = sources?.sources.filter(s => s.configured) ?? []

  if (mLoad && !metrics) return <Empty>Initialising intelligence feed…</Empty>

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* ── ARK CHRONOMETER ─────────────────────────────────────────────── */}
      {arkDate && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ padding: "16px 20px", background: "rgba(201,168,76,0.04)", border: "1px solid rgba(201,168,76,0.14)", borderRadius: 14, display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
            <div>
              <p style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.3em", textTransform: "uppercase", color: COLORS.dim, margin: 0 }}>
                Arkadia Time Frame
              </p>
              <p style={{ fontFamily: "serif", fontSize: 22, color: COLORS.gold, margin: "4px 0 0", letterSpacing: "0.08em" }}>
                {arkDate.display}
              </p>
              <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: "3px 0 0" }}>
                {arkDate.epoch}
              </p>
            </div>
            <div style={{ textAlign: "right" }}>
              <p style={{ fontFamily: "sans-serif", fontSize: 9, color: COLORS.dim, margin: 0, letterSpacing: "0.15em" }}>
                Arc Completion
              </p>
              <p style={{ fontFamily: "ui-monospace, monospace", fontSize: 18, color: COLORS.gold, margin: "4px 0 0" }}>
                {arkDate.ark_completion_pct.toFixed(2)}%
              </p>
              <p style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.muted, margin: "2px 0 0" }}>
                Year {arkDate.ark_year} of {arkDate.ark_total_years}
              </p>
            </div>
          </div>

          {/* Arc progress bar */}
          <div style={{ height: 4, background: "rgba(201,168,76,0.1)", borderRadius: 999, overflow: "hidden" }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${arkDate.ark_completion_pct}%` }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              style={{ height: "100%", background: "linear-gradient(90deg, rgba(201,168,76,0.6), #C9A84C)", borderRadius: 999 }}
            />
          </div>

          <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
            {[
              ["Ark Day", `${arkDate.total_ark_day}`],
              ["Auto-sync", arkDate.sync.auto_sync_active ? "active" : "off"],
              ["Sync count", `${arkDate.sync.refresh_count}`],
              ["Last sync", arkDate.sync.last_sync_coordinate],
              ["Scrolls synced", `${arkDate.sync.last_scroll_count}`],
            ].map(([k, v]) => (
              <div key={k}>
                <p style={{ fontFamily: "sans-serif", fontSize: 8.5, color: COLORS.dim, margin: 0, letterSpacing: "0.15em", textTransform: "uppercase" }}>{k}</p>
                <p style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: COLORS.text, margin: "2px 0 0" }}>{v}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── SYSTEM HEALTH ROW ────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
        <HealthStat
          label="Field Resonance"
          value={heartbeat ? `${(heartbeat.resonance * 100).toFixed(0)}%` : "—"}
          sub={heartbeat?.status ?? "…"}
          color={heartbeat && heartbeat.resonance > 0.9 ? "#00D4AA" : "#C9A84C"}
          pulse
        />
        <HealthStat
          label="Corpus Scrolls"
          value={codex ? `${codex.live_docs}` : "—"}
          sub={codex ? `${fmtChars(codex.total_chars)} chars indexed` : "loading"}
          color={COLORS.gold}
        />
        <HealthStat
          label="Live Sources"
          value={`${liveSources.length} / ${(sources?.sources ?? []).length}`}
          sub={liveSources.map(s => s.name).join(", ") || "none"}
          color={liveSources.length > 0 ? "#00D4AA" : "#ef6c6c"}
        />
        <HealthStat
          label="Active Jobs"
          value={metrics ? `${metrics.jobs.pending + metrics.jobs.running}` : "—"}
          sub={metrics ? `${metrics.jobs.completed} completed · ${metrics.jobs.failed} failed` : ""}
          color={metrics && (metrics.jobs.pending + metrics.jobs.running) > 0 ? COLORS.gold : COLORS.muted}
        />
        <HealthStat
          label="Active Goals"
          value={metrics ? `${metrics.goals_active}` : "—"}
          sub={metrics ? `${metrics.goals.goal_runs_total} total runs` : ""}
          color={metrics && metrics.goals_active > 0 ? "#B08DE8" : COLORS.muted}
        />
      </div>

      {/* ── ORACLE WEIGHTING INTELLIGENCE ────────────────────────────────── */}
      {corpusIntel && (
        <Card
          title="Oracle Weighting Intelligence"
          subtitle="Corpus char density per category — heavier categories carry more semantic weight in Oracle responses"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {corpusIntel.sorted.map(({ cat, label, color, chars, count }) => {
              const pctVal = corpusIntel.totalChars > 0 ? (chars / corpusIntel.totalChars) * 100 : 0
              const weightNote = CAT_META[cat]?.weight
              return (
                <div key={cat}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontFamily: "sans-serif", fontSize: 11, color, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                      {label}
                    </span>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: COLORS.text }}>
                        {fmtChars(chars)} · {count} scroll{count !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                  <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 999, overflow: "hidden", marginBottom: 3 }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pctVal}%` }}
                      transition={{ duration: 0.9, ease: "easeOut", delay: 0.1 }}
                      style={{ height: "100%", background: `linear-gradient(90deg, ${color}55, ${color})`, borderRadius: 999 }}
                    />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontFamily: "sans-serif", fontSize: 9, color: COLORS.dim }}>
                      {weightNote}
                    </span>
                    <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 9, color: `${color}90` }}>
                      {pctVal.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* ── TOP PRIORITY SCROLLS ─────────────────────────────────────────── */}
      {corpusIntel && corpusIntel.topScrolls.length > 0 && (
        <Card title="Highest-Priority Oracle Context Scrolls" subtitle="Documents most likely to be injected into active Oracle queries">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {corpusIntel.topScrolls.map((scroll, i) => (
              <div key={scroll.id} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "8px 10px", background: "rgba(255,255,255,0.02)", borderRadius: 8, border: "1px solid rgba(255,255,255,0.04)" }}>
                <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 10, color: catColor(scroll.category), minWidth: 20, flexShrink: 0, paddingTop: 1 }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontFamily: "sans-serif", fontSize: 12, color: COLORS.text, margin: "0 0 2px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {scroll.label}
                  </p>
                  <p style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.muted, margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {scroll.preview?.slice(0, 100)}
                  </p>
                </div>
                <div style={{ flexShrink: 0, textAlign: "right" }}>
                  <span style={{ fontFamily: "sans-serif", fontSize: 9, color: catColor(scroll.category), letterSpacing: "0.1em", textTransform: "uppercase", display: "block" }}>
                    {catLabel(scroll.category)}
                  </span>
                  <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 9, color: COLORS.dim }}>
                    {fmtChars(scroll.chars)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── CRITICAL OPEN LOOPS ──────────────────────────────────────────── */}
      {loopDigest && (
        <Card
          title="Critical & High-Priority Open Loops"
          subtitle={`${loopDigest.total} total loops · ${loops?.groups?.length ?? 0} categories · live from DOC2`}
        >
          {loopDigest.urgent.length === 0 ? (
            <Empty>No critical or high-priority loops active.</Empty>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {loopDigest.urgent.map(loop => {
                const levelMeta = loop.level === "critical"
                  ? { bg: "rgba(239,68,68,0.06)", border: "rgba(239,68,68,0.22)", badge: "rgba(239,68,68,0.15)", text: "#ef4444" }
                  : { bg: "rgba(249,115,22,0.06)", border: "rgba(249,115,22,0.22)", badge: "rgba(249,115,22,0.15)", text: "#f97316" }
                return (
                  <div key={loop.id} style={{ padding: "10px 12px", background: levelMeta.bg, border: `1px solid ${levelMeta.border}`, borderRadius: 10 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: loop.next_action ? 5 : 0 }}>
                      <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 9, padding: "1px 6px", borderRadius: 4, background: levelMeta.badge, color: levelMeta.text }}>
                        #{loop.id}
                      </span>
                      <span style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", color: levelMeta.text }}>
                        {loop.level}
                      </span>
                      <span style={{ fontFamily: "sans-serif", fontSize: 12, color: COLORS.text, flex: 1 }}>
                        {loop.name}
                      </span>
                    </div>
                    {loop.next_action && (
                      <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: "0 0 0 28px", lineHeight: 1.5 }}>
                        → {loop.next_action}
                      </p>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      )}

      {/* ── EXECUTION ENGINE LIVE CHART ──────────────────────────────────── */}
      {metrics && (
        <Card title="Execution Engine — Live" subtitle={`Refresh every 5s · ${series.length} samples · last update ${fmtAgo(metrics.ts)}`}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10, marginBottom: 14 }}>
            {[
              { k: "Completed", v: metrics.jobs.completed, c: "#00D4AA" },
              { k: "Running",   v: metrics.jobs.running,   c: COLORS.gold },
              { k: "Pending",   v: metrics.jobs.pending,   c: "rgba(232,232,232,0.5)" },
              { k: "Failed",    v: metrics.jobs.failed,    c: "#ef6c6c" },
            ].map(({ k, v, c }) => (
              <div key={k} style={{ padding: "8px 10px", background: "rgba(255,255,255,0.02)", borderRadius: 8, borderLeft: `3px solid ${c}` }}>
                <p style={{ fontFamily: "sans-serif", fontSize: 9, color: COLORS.dim, margin: 0, letterSpacing: "0.18em", textTransform: "uppercase" }}>{k}</p>
                <p style={{ fontFamily: "serif", fontSize: 20, color: c, margin: "4px 0 0", lineHeight: 1 }}>{v}</p>
              </div>
            ))}
          </div>
          {series.length < 2 ? (
            <Empty>Collecting samples — chart appears after the second tick.</Empty>
          ) : (
            <div style={{ width: "100%", height: 200 }}>
              <ResponsiveContainer>
                <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
                  <CartesianGrid stroke="rgba(232,232,232,0.05)" strokeDasharray="3 3" />
                  <XAxis dataKey="time" tick={{ fill: COLORS.dim, fontSize: 9 }} />
                  <YAxis tick={{ fill: COLORS.dim, fontSize: 9 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: "rgba(10,10,15,0.95)", border: "1px solid rgba(0,212,170,0.3)", borderRadius: 8, fontSize: 11 }}
                    labelStyle={{ color: COLORS.gold }}
                  />
                  <Line type="monotone" dataKey="completed" stroke="#00D4AA" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="failed"    stroke="#ef6c6c" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="running"   stroke={COLORS.gold} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="pending"   stroke="rgba(232,232,232,0.35)" strokeWidth={1} dot={false} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      )}

      {/* ── PLANNER + WORKER INTELLIGENCE ───────────────────────────────── */}
      {metrics && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <Card title="Planner Intelligence" subtitle="LLM vs deterministic routing">
            {metrics.plans.plans_total === 0 ? (
              <Empty>No plans executed yet.</Empty>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 999, overflow: "hidden", display: "flex" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct(metrics.plans.plans_llm, metrics.plans.plans_total) ?? 0}%` }}
                    transition={{ duration: 0.9 }}
                    style={{ height: "100%", background: "#B08DE8" }}
                  />
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct(metrics.plans.plans_fallback, metrics.plans.plans_total) ?? 0}%` }}
                    transition={{ duration: 0.9, delay: 0.1 }}
                    style={{ height: "100%", background: "#6A9FD8" }}
                  />
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                  <span style={{ fontSize: 9, color: "#B08DE8", fontFamily: "sans-serif", letterSpacing: "0.1em" }}>● LLM {pct(metrics.plans.plans_llm, metrics.plans.plans_total) ?? 0}%</span>
                  <span style={{ fontSize: 9, color: "#6A9FD8", fontFamily: "sans-serif", letterSpacing: "0.1em" }}>● Deterministic {pct(metrics.plans.plans_fallback, metrics.plans.plans_total) ?? 0}%</span>
                </div>
                {[
                  ["Total plans",    metrics.plans.plans_total],
                  ["Successful",     metrics.plans.plans_success],
                  ["Failed",         metrics.plans.plans_failed],
                  ["Success rate",   pct(metrics.plans.plans_success, metrics.plans.plans_total) != null ? `${pct(metrics.plans.plans_success, metrics.plans.plans_total)}%` : "—"],
                ].map(([k, v]) => (
                  <div key={String(k)} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed rgba(232,232,232,0.05)", paddingBottom: 4 }}>
                    <span style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted }}>{k}</span>
                    <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: COLORS.text }}>{v}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Worker & Goal Engine" subtitle="Background runtime status">
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: metrics.workers.alive > 0 ? "rgba(0,212,170,0.05)" : "rgba(239,68,68,0.05)", border: `1px solid ${metrics.workers.alive > 0 ? "rgba(0,212,170,0.2)" : "rgba(239,68,68,0.2)"}`, borderRadius: 8 }}>
                <motion.div
                  animate={metrics.workers.alive > 0 ? { opacity: [0.4, 1, 0.4] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                  style={{ width: 8, height: 8, borderRadius: "50%", background: metrics.workers.alive > 0 ? "#00D4AA" : "#ef4444", flexShrink: 0 }}
                />
                <span style={{ fontFamily: "sans-serif", fontSize: 11, color: metrics.workers.alive > 0 ? "#00D4AA" : "#ef4444" }}>
                  {metrics.workers.alive} worker thread{metrics.workers.alive !== 1 ? "s" : ""} alive
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: metrics.workers.goal_scheduler ? "rgba(176,141,232,0.05)" : "rgba(255,255,255,0.02)", border: `1px solid ${metrics.workers.goal_scheduler ? "rgba(176,141,232,0.25)" : "rgba(255,255,255,0.06)"}`, borderRadius: 8 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: metrics.workers.goal_scheduler ? "#B08DE8" : "rgba(232,232,232,0.2)", flexShrink: 0 }} />
                <span style={{ fontFamily: "sans-serif", fontSize: 11, color: metrics.workers.goal_scheduler ? "#B08DE8" : COLORS.muted }}>
                  Goal scheduler {metrics.workers.goal_scheduler ? "online" : "offline"}
                </span>
              </div>
              {[
                ["Active goals",    metrics.goals_active],
                ["Goal runs total", metrics.goals.goal_runs_total],
                ["Goal runs ok",    metrics.goals.goal_runs_success],
                ["Goal runs failed",metrics.goals.goal_runs_failed],
                ["Goal runs skipped",metrics.goals.goal_runs_skipped],
              ].map(([k, v]) => (
                <div key={String(k)} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px dashed rgba(232,232,232,0.05)", paddingBottom: 4 }}>
                  <span style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted }}>{k}</span>
                  <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: COLORS.text }}>{v}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ── CORPUS SOURCE STATUS ─────────────────────────────────────────── */}
      {sources && (
        <Card title="Corpus Source Status" subtitle="Data origin health across all configured feeds">
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {sources.sources.map(src => (
              <div key={src.name} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", background: "rgba(255,255,255,0.02)", border: `1px solid ${src.live ? "rgba(0,212,170,0.15)" : src.configured ? "rgba(201,168,76,0.15)" : "rgba(255,255,255,0.05)"}`, borderRadius: 10 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: src.live ? "#00D4AA" : src.configured ? "#C9A84C" : "rgba(232,232,232,0.15)", flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <span style={{ fontFamily: "sans-serif", fontSize: 12, color: src.live ? COLORS.text : COLORS.muted, textTransform: "capitalize" }}>
                    {src.name}
                  </span>
                  {src.repo && (
                    <span style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.dim, marginLeft: 8 }}>
                      {src.repo} @ {src.branch}
                    </span>
                  )}
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                  <span style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", color: src.live ? "#00D4AA" : src.configured ? "#C9A84C" : COLORS.dim }}>
                    {src.live ? "live" : src.configured ? "configured" : "not configured"}
                  </span>
                  {src.authenticated === false && src.configured && (
                    <span style={{ fontFamily: "sans-serif", fontSize: 9, color: "rgba(249,115,22,0.7)", letterSpacing: "0.1em" }}>
                      unauthenticated
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// ── HealthStat component ─────────────────────────────────────────────────────

function HealthStat({ label, value, sub, color, pulse }: {
  label: string; value: string; sub: string; color: string; pulse?: boolean
}) {
  return (
    <div style={{ padding: "14px 16px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        {pulse && <ResonanceDot value={1} />}
        <p style={{ fontFamily: "sans-serif", fontSize: 9, color: COLORS.dim, margin: 0, letterSpacing: "0.22em", textTransform: "uppercase" }}>
          {label}
        </p>
      </div>
      <p style={{ fontFamily: "serif", fontSize: 24, color, margin: "0 0 4px", lineHeight: 1 }}>{value}</p>
      <p style={{ fontFamily: "sans-serif", fontSize: 10, color: COLORS.muted, margin: 0 }}>{sub}</p>
    </div>
  )
}
