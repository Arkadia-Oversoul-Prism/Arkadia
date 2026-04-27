import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { api, TraceResponse, TraceStep } from "../../lib/dashboardApi"
import {
  Card, COLORS, Empty, ErrorBox, StatusBadge,
  CollapsibleJSON, Button, fmtTime, fmtMs,
} from "./ui"
import { Table, Row, Cell, shortId } from "./Jobs"
import { useMediaQuery } from "../../hooks/useMediaQuery"

export default function Traces({ openJobId }: { openJobId?: string | null }) {
  const [selected, setSelected] = useState<string | null>(openJobId ?? null)
  const isNarrow = useMediaQuery("(max-width: 960px)")

  // External nav (from Jobs page) opens a specific trace.
  useEffect(() => {
    if (openJobId) setSelected(openJobId)
  }, [openJobId])

  const list = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(undefined, 100),
    refetchInterval: 5000,
  })

  if (list.isLoading && !list.data) return <Empty>Loading traces…</Empty>
  if (list.error) return <ErrorBox>Failed to load: {(list.error as Error).message}</ErrorBox>
  const jobs = (list.data?.jobs ?? []).filter((j) => j.trace || j.status === "completed" || j.status === "failed")

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: selected && !isNarrow ? "minmax(280px, 1fr) minmax(420px, 2fr)" : "1fr",
      gap: 18,
    }}>
      <Card title="Traces" subtitle={`${jobs.length} traceable jobs`}>
        {jobs.length === 0 ? (
          <Empty>No completed jobs yet.</Empty>
        ) : (
          <Table headers={["job_id", "status", "steps", "completed"]}>
            {jobs.map((j) => {
              const stepCount = j.trace?.steps?.length ?? 0
              return (
                <Row
                  key={j.job_id}
                  selected={selected === j.job_id}
                  onClick={() => setSelected(j.job_id === selected ? null : j.job_id)}
                  testId={`row-trace-${j.job_id}`}
                >
                  <Cell mono>{shortId(j.job_id)}</Cell>
                  <Cell><StatusBadge status={j.status} /></Cell>
                  <Cell mono>{stepCount}</Cell>
                  <Cell muted>{fmtTime(j.completed_at)}</Cell>
                </Row>
              )
            })}
          </Table>
        )}
      </Card>

      {selected && (
        <TraceDetail jobId={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}

function TraceDetail({ jobId, onClose }: { jobId: string; onClose: () => void }) {
  const q = useQuery({
    queryKey: ["trace", jobId],
    queryFn: () => api.getTrace(jobId),
    refetchInterval: (query) => {
      const data = query.state.data as TraceResponse | undefined
      return data?.status === "completed" || data?.status === "failed" ? false : 3000
    },
  })

  if (q.isLoading && !q.data) return <Card title="Trace">Loading…</Card>
  if (q.error)   return <Card title="Trace"><ErrorBox>{(q.error as Error).message}</ErrorBox></Card>
  const t = q.data
  if (!t) return null
  const tr = t.trace

  return (
    <Card
      title="Execution trace"
      subtitle={`${shortId(jobId)} · ${tr.intent_type ?? "—"}`}
      right={<Button variant="ghost" onClick={onClose} testId="button-close-trace">Close</Button>}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <StatusBadge status={t.status} />
          {tr.plan_source && <StatusBadge status={tr.plan_source} />}
          {tr.success ? <StatusBadge status="success" /> : <StatusBadge status="failed" />}
        </div>

        <Section label="Input">
          <Mono block>{typeof tr.input === "string" ? tr.input : JSON.stringify(tr.input)}</Mono>
        </Section>

        <Section label="Plan">
          <CollapsibleJSON data={tr.plan ?? null} label="Plan JSON" defaultOpen testId="json-plan" />
        </Section>

        <Section label="Retrieved context (memory)">
          <CollapsibleJSON data={tr.context ?? null} label="Context JSON" testId="json-context" />
        </Section>

        <Section label={`Steps (${tr.steps?.length ?? 0})`}>
          {tr.steps?.length ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {tr.steps.map((s) => <StepRow key={s.step_id} step={s} />)}
            </div>
          ) : (
            <Empty>No step trace recorded.</Empty>
          )}
        </Section>

        {tr.summary && (
          <Section label="Final result">
            <pre
              style={{
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(0,212,170,0.10)",
                borderRadius: 8,
                padding: "12px 14px",
                fontFamily: "serif",
                fontSize: 13,
                color: COLORS.text,
                whiteSpace: "pre-wrap",
                margin: 0,
              }}
            >
              {tr.summary}
            </pre>
          </Section>
        )}
      </div>
    </Card>
  )
}

function StepRow({ step }: { step: TraceStep }) {
  return (
    <div
      style={{
        border: "1px solid rgba(232,232,232,0.06)",
        borderRadius: 10,
        padding: "10px 12px",
        background: "rgba(0,0,0,0.2)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: COLORS.gold }}>
            {step.step_id}
          </span>
          <span style={{ fontFamily: "sans-serif", fontSize: 13, color: COLORS.text }}>
            {step.tool}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: COLORS.muted }}>
            {fmtMs(step.duration_ms)}
          </span>
          <StatusBadge status={step.success ? "success" : "failed"} />
        </div>
      </div>
      {step.summary && (
        <p style={{ margin: "8px 0 0", fontFamily: "serif", fontSize: 12.5, color: COLORS.text, lineHeight: 1.55 }}>
          {step.summary}
        </p>
      )}
      <div style={{ marginTop: 8 }}>
        <CollapsibleJSON data={step.input} label="Input" />
      </div>
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p style={{
        fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.3em",
        textTransform: "uppercase", color: COLORS.dim, margin: "0 0 6px",
      }}>{label}</p>
      {children}
    </div>
  )
}

function Mono({ children, block }: { children: React.ReactNode; block?: boolean }) {
  return (
    <code style={{
      display: block ? "block" : "inline",
      fontFamily: "ui-monospace, monospace",
      fontSize: 12.5, color: COLORS.text,
      background: "rgba(0,0,0,0.35)",
      border: "1px solid rgba(0,212,170,0.08)",
      borderRadius: 6, padding: block ? "10px 12px" : "2px 6px",
      wordBreak: "break-word",
    }}>{children}</code>
  )
}
