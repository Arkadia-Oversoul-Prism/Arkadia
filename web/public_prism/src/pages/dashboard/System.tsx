import React from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../../lib/dashboardApi"
import { Card, COLORS, Empty, ErrorBox, fmtAgo, fmtMs } from "./ui"
import { Table, Row, Cell } from "./Jobs"

export default function System() {
  const q = useQuery({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 5000,
  })

  if (q.isLoading && !q.data) return <Empty>Loading system metrics…</Empty>
  if (q.error) return <ErrorBox>{(q.error as Error).message}</ErrorBox>
  if (!q.data) return null
  const m = q.data

  const totalToolCalls = m.tools.reduce((acc, t) => acc + t.calls, 0)
  const totalToolFailures = m.tools.reduce((acc, t) => acc + t.failures, 0)
  const successRate = totalToolCalls
    ? Math.round((1 - totalToolFailures / totalToolCalls) * 1000) / 10
    : null
  const avgP50 = m.tools.length
    ? m.tools.reduce((acc, t) => acc + (t.p50_ms ?? 0), 0) / m.tools.length
    : null

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
        <Mini label="Queue depth"     value={m.jobs.queue_depth} hint={`${m.jobs.pending} pending · ${m.jobs.running} running`} />
        <Mini label="Job success rate"
              value={
                m.jobs.total
                  ? `${Math.round((m.jobs.completed / m.jobs.total) * 1000) / 10}%`
                  : "—"
              }
              hint={`${m.jobs.completed} / ${m.jobs.total}`} />
        <Mini label="Tool success rate" value={successRate != null ? `${successRate}%` : "—"} hint={`${totalToolCalls} calls`} />
        <Mini label="Avg p50 latency" value={avgP50 != null ? fmtMs(avgP50) : "—"} hint="across all tools" />
      </div>

      <Card title="Per-tool metrics" subtitle="Sliding window — last 200 calls per tool">
        {m.tools.length === 0 ? (
          <Empty>No tool calls recorded yet.</Empty>
        ) : (
          <Table headers={["tool", "calls", "success rate", "p50", "p95", "last call"]}>
            {m.tools.map((t) => (
              <Row key={t.tool} testId={`row-toolmetric-${t.tool}`}>
                <Cell mono>{t.tool}</Cell>
                <Cell mono>{t.calls}</Cell>
                <Cell mono>{t.success_rate != null ? `${Math.round(t.success_rate * 1000) / 10}%` : "—"}</Cell>
                <Cell mono>{fmtMs(t.p50_ms)}</Cell>
                <Cell mono>{fmtMs(t.p95_ms)}</Cell>
                <Cell muted>{t.last_at ? fmtAgo(t.last_at) : "never"}</Cell>
              </Row>
            ))}
          </Table>
        )}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Card title="Workers">
          <KV rows={[
            ["Worker threads", m.workers.alive],
            ["Goal scheduler", m.workers.goal_scheduler ? "online" : "offline"],
          ]} />
        </Card>
        <Card title="Pipeline counters">
          <KV rows={[
            ["Plans · total",         m.plans.plans_total],
            ["Plans · LLM",           m.plans.plans_llm],
            ["Plans · deterministic", m.plans.plans_fallback],
            ["Goal runs · success",   m.goals.goal_runs_success],
            ["Goal runs · failed",    m.goals.goal_runs_failed],
          ]} />
        </Card>
      </div>
    </div>
  )
}

function Mini({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <Card>
      <p style={{ fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.3em", textTransform: "uppercase", color: COLORS.dim, margin: 0 }}>
        {label}
      </p>
      <p style={{ fontFamily: "serif", fontSize: 24, color: COLORS.text, margin: "8px 0 0", lineHeight: 1 }}>
        {value}
      </p>
      {hint && (
        <p style={{ fontFamily: "sans-serif", fontSize: 11, color: COLORS.muted, margin: "6px 0 0" }}>{hint}</p>
      )}
    </Card>
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
