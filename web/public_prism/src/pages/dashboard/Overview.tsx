import React, { useEffect, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts"
import { api, MetricsSnapshot } from "../../lib/dashboardApi"
import { Card, COLORS, Empty, ErrorBox, Stat, fmtAgo } from "./ui"

type Sample = {
  t: number
  completed: number
  failed: number
  pending: number
  running: number
}

const SERIES_CAP = 60

export default function Overview() {
  const seriesRef = useRef<Sample[]>([])
  const { data, isLoading, error } = useQuery<MetricsSnapshot>({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 5000,
  })

  // Maintain a small client-side time series so we can chart "jobs over time"
  // without storing it server-side. Cheap, bounded, restarts with the page.
  useEffect(() => {
    if (!data) return
    seriesRef.current = [
      ...seriesRef.current,
      {
        t: data.ts,
        completed: data.jobs.completed,
        failed:    data.jobs.failed,
        pending:   data.jobs.pending,
        running:   data.jobs.running,
      },
    ].slice(-SERIES_CAP)
  }, [data])

  if (isLoading && !data) return <Empty>Loading system snapshot…</Empty>
  if (error) return <ErrorBox>Failed to load metrics: {(error as Error).message}</ErrorBox>
  if (!data) return null

  const successRate =
    data.plans.plans_total > 0
      ? Math.round((data.plans.plans_success / data.plans.plans_total) * 1000) / 10
      : null

  const series = seriesRef.current.map((s) => ({
    time: new Date(s.t * 1000).toLocaleTimeString(undefined, {
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    }),
    completed: s.completed,
    failed:    s.failed,
    pending:   s.pending,
    running:   s.running,
  }))

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="grid gap-4" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <Stat label="Active Jobs" value={data.jobs.pending + data.jobs.running}
              hint={`${data.jobs.queue_depth} queued`}
              tone={data.jobs.running > 0 ? "warn" : "default"}
              testId="stat-active-jobs" />
        <Stat label="Completed" value={data.jobs.completed} tone="success" testId="stat-completed" />
        <Stat label="Failed" value={data.jobs.failed}
              tone={data.jobs.failed > 0 ? "fail" : "default"}
              testId="stat-failed" />
        <Stat label="Active Goals" value={data.goals_active}
              hint={`${data.goals.goal_runs_total} runs total`}
              tone={data.goals_active > 0 ? "success" : "default"}
              testId="stat-active-goals" />
      </div>

      <Card title="Jobs over time" subtitle={`Live · refresh every 5s · ${series.length} samples`}>
        {series.length < 2 ? (
          <Empty>Collecting samples… chart appears after the second tick.</Empty>
        ) : (
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={series} margin={{ top: 10, right: 16, bottom: 0, left: -16 }}>
                <CartesianGrid stroke="rgba(232,232,232,0.06)" strokeDasharray="3 3" />
                <XAxis dataKey="time" tick={{ fill: COLORS.muted, fontSize: 10 }} />
                <YAxis tick={{ fill: COLORS.muted, fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "rgba(10,10,15,0.95)",
                    border: "1px solid rgba(0,212,170,0.3)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: COLORS.gold }}
                />
                <Line type="monotone" dataKey="completed" stroke={COLORS.teal} strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="failed"    stroke="#EF6C6C"      strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="running"   stroke={COLORS.gold}  strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="pending"   stroke="rgba(232,232,232,0.4)" strokeWidth={1} dot={false} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <div className="grid gap-4" style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
        <Card title="Planner" subtitle={`Last update ${fmtAgo(data.ts)}`}>
          <KV rows={[
            ["Total plans",        data.plans.plans_total],
            ["Success",            data.plans.plans_success],
            ["Failed",             data.plans.plans_failed],
            ["LLM-generated",      data.plans.plans_llm],
            ["Deterministic",      data.plans.plans_fallback],
            ["Success rate",       successRate != null ? `${successRate}%` : "—"],
          ]} />
        </Card>
        <Card title="Workers" subtitle="Background runtime">
          <KV rows={[
            ["Workers alive",    data.workers.alive],
            ["Goal scheduler",   data.workers.goal_scheduler ? "online" : "offline"],
            ["Goal runs total",  data.goals.goal_runs_total],
            ["Goal runs failed", data.goals.goal_runs_failed],
          ]} />
        </Card>
      </div>
    </div>
  )
}

function KV({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {rows.map(([k, v]) => (
        <div key={k} className="flex items-center justify-between"
             style={{ borderBottom: "1px dashed rgba(232,232,232,0.06)", paddingBottom: 6 }}>
          <span style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, letterSpacing: "0.1em" }}>{k}</span>
          <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 13, color: COLORS.text }}>{v}</span>
        </div>
      ))}
    </div>
  )
}
