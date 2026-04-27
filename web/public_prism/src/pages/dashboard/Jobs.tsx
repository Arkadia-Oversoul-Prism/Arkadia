import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api, Job } from "../../lib/dashboardApi"
import {
  Card, COLORS, Empty, ErrorBox, StatusBadge,
  CollapsibleJSON, Button, fmtTime, fmtDuration,
} from "./ui"

export default function Jobs({
  onOpenTrace,
}: {
  onOpenTrace: (jobId: string) => void
}) {
  const [selected, setSelected] = useState<string | null>(null)

  const list = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(undefined, 100),
    refetchInterval: 3000,
  })

  if (list.isLoading && !list.data) return <Empty>Loading jobs…</Empty>
  if (list.error)   return <ErrorBox>Failed to load jobs: {(list.error as Error).message}</ErrorBox>
  const jobs = list.data?.jobs ?? []

  return (
    <div style={{ display: "grid", gridTemplateColumns: selected ? "minmax(320px, 1fr) minmax(360px, 1fr)" : "1fr", gap: 18 }}>
      <Card title="Jobs" subtitle={`${jobs.length} most recent · auto-refresh 3s`}>
        {jobs.length === 0 ? (
          <Empty>No jobs yet. Submit one via /api/job/create or /api/plan/run.</Empty>
        ) : (
          <Table headers={["job_id", "status", "tool / type", "created", "duration"]}>
            {jobs.map((j) => (
              <Row
                key={j.job_id}
                selected={selected === j.job_id}
                onClick={() => setSelected(j.job_id === selected ? null : j.job_id)}
                testId={`row-job-${j.job_id}`}
              >
                <Cell mono>{shortId(j.job_id)}</Cell>
                <Cell><StatusBadge status={j.status} /></Cell>
                <Cell muted>{j.intent?.type || "—"}</Cell>
                <Cell muted>{fmtTime(j.created_at)}</Cell>
                <Cell mono>{fmtDuration(j.started_at ?? j.created_at, j.completed_at)}</Cell>
              </Row>
            ))}
          </Table>
        )}
      </Card>

      {selected && (
        <JobDetail jobId={selected}
                   onClose={() => setSelected(null)}
                   onOpenTrace={onOpenTrace} />
      )}
    </div>
  )
}

function JobDetail({
  jobId, onClose, onOpenTrace,
}: {
  jobId: string
  onClose: () => void
  onOpenTrace: (id: string) => void
}) {
  const detail = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId),
    refetchInterval: 3000,
  })

  if (detail.isLoading && !detail.data) return <Card title="Job">Loading…</Card>
  if (detail.error) return <Card title="Job"><ErrorBox>{(detail.error as Error).message}</ErrorBox></Card>
  const j: Job | undefined = detail.data
  if (!j) return null

  return (
    <Card
      title="Job detail"
      subtitle={shortId(j.job_id)}
      right={
        <div style={{ display: "flex", gap: 8 }}>
          <Button variant="primary" onClick={() => onOpenTrace(j.job_id)} testId="button-view-trace">
            View Trace
          </Button>
          <Button variant="ghost" onClick={onClose} testId="button-close-detail">Close</Button>
        </div>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <KVRow label="Status">
          <StatusBadge status={j.status} />
        </KVRow>
        <KVRow label="Intent type"><Mono>{j.intent?.type ?? "—"}</Mono></KVRow>
        <KVRow label="Source"><Mono>{j.source ?? "—"}</Mono></KVRow>
        <KVRow label="Created"><Mono>{fmtTime(j.created_at)}</Mono></KVRow>
        <KVRow label="Completed"><Mono>{j.completed_at ? fmtTime(j.completed_at) : "—"}</Mono></KVRow>
        <KVRow label="Retries"><Mono>{j.retries}</Mono></KVRow>
        {j.error && (
          <ErrorBox>{j.error}</ErrorBox>
        )}
        <CollapsibleJSON data={j.intent?.payload ?? {}} label="Intent payload" testId="json-intent" />
        <CollapsibleJSON data={j.result ?? null} label="Result" defaultOpen={!!j.result} testId="json-result" />
      </div>
    </Card>
  )
}

// ── Tiny table primitives (shared across pages) ────────────────────────────

export function Table({
  headers, children,
}: { headers: string[]; children: React.ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "sans-serif" }}>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}
                  style={{
                    textAlign: "left",
                    fontSize: 9,
                    letterSpacing: "0.25em",
                    textTransform: "uppercase",
                    color: COLORS.dim,
                    fontWeight: "normal",
                    padding: "8px 10px",
                    borderBottom: "1px solid rgba(232,232,232,0.06)",
                  }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}
export function Row({
  children, onClick, selected, testId,
}: {
  children: React.ReactNode
  onClick?: () => void
  selected?: boolean
  testId?: string
}) {
  return (
    <tr
      onClick={onClick}
      data-testid={testId}
      style={{
        cursor: onClick ? "pointer" : "default",
        background: selected ? "rgba(0,212,170,0.06)" : "transparent",
        transition: "background .15s",
      }}
    >
      {children}
    </tr>
  )
}
export function Cell({
  children, mono, muted,
}: { children: React.ReactNode; mono?: boolean; muted?: boolean }) {
  return (
    <td
      style={{
        padding: "10px",
        borderBottom: "1px solid rgba(232,232,232,0.04)",
        fontFamily: mono ? "ui-monospace, SFMono-Regular, monospace" : "sans-serif",
        fontSize: mono ? 11.5 : 12.5,
        color: muted ? COLORS.muted : COLORS.text,
        verticalAlign: "middle",
      }}
    >
      {children}
    </td>
  )
}
function KVRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <span style={{ fontFamily: "sans-serif", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: COLORS.dim }}>
        {label}
      </span>
      <span>{children}</span>
    </div>
  )
}
function Mono({ children }: { children: React.ReactNode }) {
  return <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: COLORS.text }}>{children}</span>
}
export function shortId(id: string): string {
  return id.length > 16 ? id.slice(0, 8) + "…" + id.slice(-6) : id
}
