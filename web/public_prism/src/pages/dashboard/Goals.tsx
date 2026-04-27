import React, { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api, Goal } from "../../lib/dashboardApi"
import {
  Card, COLORS, Empty, ErrorBox, StatusBadge, Button, Input,
  fmtTime, fmtAgo,
} from "./ui"
import { Table, Row, Cell, shortId } from "./Jobs"

export default function Goals() {
  const qc = useQueryClient()
  const list = useQuery({
    queryKey: ["goals"],
    queryFn: () => api.listGoals(),
    refetchInterval: 5000,
  })

  const create = useMutation({
    mutationFn: api.createGoal,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  })
  const update = useMutation({
    mutationFn: (args: { id: string; fields: Parameters<typeof api.updateGoal>[1] }) =>
      api.updateGoal(args.id, args.fields),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  })
  const remove = useMutation({
    mutationFn: api.deleteGoal,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  })

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <NewGoalForm
        onSubmit={(payload) => create.mutate(payload)}
        loading={create.isPending}
        error={create.error ? (create.error as Error).message : null}
      />

      <Card title="Goals" subtitle={`${list.data?.count ?? 0} total · refresh 5s`}>
        {list.isLoading && !list.data ? (
          <Empty>Loading…</Empty>
        ) : list.error ? (
          <ErrorBox>{(list.error as Error).message}</ErrorBox>
        ) : (list.data?.goals?.length ?? 0) === 0 ? (
          <Empty>No goals yet. Create one above to begin a long-running loop.</Empty>
        ) : (
          <Table headers={["goal_id", "description", "status", "cadence", "last run", "runs", ""]}>
            {list.data!.goals.map((g) => (
              <GoalRow key={g.goal_id} goal={g}
                       updating={update.isPending}
                       removing={remove.isPending}
                       onPause={() => update.mutate({ id: g.goal_id, fields: { status: "paused" } })}
                       onResume={() => update.mutate({ id: g.goal_id, fields: { status: "active" } })}
                       onComplete={() => update.mutate({ id: g.goal_id, fields: { status: "completed" } })}
                       onDelete={() => {
                         if (confirm(`Delete goal "${g.description}"?`)) remove.mutate(g.goal_id)
                       }} />
            ))}
          </Table>
        )}
        {update.error && <div style={{ marginTop: 10 }}><ErrorBox>{(update.error as Error).message}</ErrorBox></div>}
        {remove.error && <div style={{ marginTop: 10 }}><ErrorBox>{(remove.error as Error).message}</ErrorBox></div>}
      </Card>
    </div>
  )
}

function GoalRow({
  goal: g, onPause, onResume, onComplete, onDelete, updating, removing,
}: {
  goal: Goal
  onPause: () => void
  onResume: () => void
  onComplete: () => void
  onDelete: () => void
  updating: boolean
  removing: boolean
}) {
  const isActive = g.status === "active"
  const isPaused = g.status === "paused"
  return (
    <Row testId={`row-goal-${g.goal_id}`}>
      <Cell mono>{shortId(g.goal_id)}</Cell>
      <Cell>
        <span style={{ fontFamily: "serif", fontSize: 13, color: COLORS.text }}>
          {g.description}
        </span>
      </Cell>
      <Cell><StatusBadge status={g.status} /></Cell>
      <Cell muted>{Math.round(g.cadence_seconds)}s · max {g.max_runs_per_hour}/hr</Cell>
      <Cell muted>{g.last_run ? fmtAgo(g.last_run) : "never"}</Cell>
      <Cell mono>{g.run_count}</Cell>
      <Cell>
        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
          {isActive && (
            <Button variant="default" onClick={onPause} disabled={updating}
                    testId={`button-pause-${g.goal_id}`}>Pause</Button>
          )}
          {isPaused && (
            <Button variant="primary" onClick={onResume} disabled={updating}
                    testId={`button-resume-${g.goal_id}`}>Resume</Button>
          )}
          {g.status !== "completed" && (
            <Button variant="ghost" onClick={onComplete} disabled={updating}
                    testId={`button-complete-${g.goal_id}`}>Complete</Button>
          )}
          <Button variant="danger" onClick={onDelete} disabled={removing}
                  testId={`button-delete-${g.goal_id}`}>Delete</Button>
        </div>
      </Cell>
    </Row>
  )
}

function NewGoalForm({
  onSubmit, loading, error,
}: {
  onSubmit: (p: { description: string; cadence_seconds: number; max_runs_per_hour: number }) => void
  loading: boolean
  error: string | null
}) {
  const [desc, setDesc] = useState("")
  const [cadence, setCadence] = useState("300")
  const [cap, setCap] = useState("6")

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!desc.trim()) return
    onSubmit({
      description:       desc.trim(),
      cadence_seconds:   Math.max(30, Number(cadence) || 300),
      max_runs_per_hour: Math.max(1, Math.min(60, Number(cap) || 6)),
    })
    setDesc("")
  }

  return (
    <Card title="New goal" subtitle="Min cadence 30s · max 60 runs/hr (hard cap)">
      <form onSubmit={submit} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr auto", gap: 10, alignItems: "end" }}>
        <div>
          <Label>Description</Label>
          <Input value={desc} onChange={setDesc}
                 placeholder='e.g. "generate a verse"' testId="input-goal-description" />
        </div>
        <div>
          <Label>Cadence (sec)</Label>
          <Input value={cadence} onChange={setCadence} type="number" testId="input-goal-cadence" />
        </div>
        <div>
          <Label>Max runs / hour</Label>
          <Input value={cap} onChange={setCap} type="number" testId="input-goal-cap" />
        </div>
        <Button type="submit" variant="primary" disabled={loading || !desc.trim()} testId="button-create-goal">
          {loading ? "Creating…" : "Create"}
        </Button>
      </form>
      {error && <div style={{ marginTop: 10 }}><ErrorBox>{error}</ErrorBox></div>}
    </Card>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontFamily: "sans-serif", fontSize: 9, letterSpacing: "0.3em",
      textTransform: "uppercase", color: COLORS.dim, margin: "0 0 6px",
    }}>
      {children}
    </div>
  )
}
