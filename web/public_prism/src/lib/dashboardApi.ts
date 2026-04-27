/**
 * Arkadia Dashboard — typed REST client for the FastAPI backend.
 *
 * In dev: calls flow through Vite's proxy (/api → :8000).
 * In prod: set VITE_API_BASE_URL in Vercel to your Render URL.
 */

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")

async function request<T>(
  path: string,
  init?: RequestInit & { json?: unknown }
): Promise<T> {
  const url = `${BASE}${path}`
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  }
  let body = init?.body
  if (init?.json !== undefined) {
    headers["Content-Type"] = "application/json"
    body = JSON.stringify(init.json)
  }
  const res = await fetch(url, { ...init, headers, body })
  const text = await res.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }
  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && "detail" in (data as object) &&
        (data as { detail: unknown }).detail) ||
      `${res.status} ${res.statusText}`
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail))
  }
  return data as T
}

// ── Domain types ───────────────────────────────────────────────────────────

export type JobStatus = "pending" | "running" | "completed" | "failed"

export interface Job {
  job_id: string
  status: JobStatus
  intent: { type: string; payload?: Record<string, unknown>; source?: string }
  result?: Record<string, unknown> | null
  error?: string | null
  retries: number
  created_at: number
  started_at?: number | null
  completed_at?: number | null
  source?: string
  trace?: TraceRecord | null
}

export interface JobsList {
  jobs: Job[]
  stats: {
    pending: number
    running: number
    completed: number
    failed: number
    total: number
    queue_depth: number
  }
}

export interface TraceStep {
  step_id: string
  tool: string
  input: Record<string, unknown>
  duration_ms?: number
  success: boolean
  summary?: string
}

export interface TraceRecord {
  job_id: string
  intent_type: string
  input: unknown
  plan?: { steps: { tool: string; input: Record<string, unknown> }[]; fallback?: boolean } | null
  plan_source?: string | null
  context?: Record<string, unknown> | null
  steps: TraceStep[]
  success: boolean
  summary?: string
}

export interface TraceResponse {
  job_id: string
  status: JobStatus
  trace: TraceRecord
}

export type GoalStatus = "active" | "paused" | "completed"

export interface Goal {
  goal_id: string
  description: string
  status: GoalStatus
  cadence_seconds: number
  max_runs_per_hour: number
  next_run: number | null
  last_run: number | null
  run_count: number
  history: string[]
  created_at: number
  updated_at: number
}

export interface Tool {
  name: string
  description: string
  payload_schema?: Record<string, string>
}

export interface MetricsSnapshot {
  ts: number
  tools: Array<{
    tool: string
    calls: number
    successes: number
    failures: number
    success_rate: number | null
    p50_ms: number | null
    p95_ms: number | null
    last_at: number | null
  }>
  plans: {
    plans_total: number
    plans_success: number
    plans_failed: number
    plans_llm: number
    plans_fallback: number
  }
  goals: {
    goal_runs_total: number
    goal_runs_success: number
    goal_runs_failed: number
    goal_runs_skipped: number
  }
  workers: { alive: number; goal_scheduler: boolean }
  jobs: JobsList["stats"]
  goals_active: number
}

// ── Endpoints ──────────────────────────────────────────────────────────────

export const api = {
  // Jobs
  listJobs: (status?: JobStatus, limit = 50) => {
    const q = new URLSearchParams()
    if (status) q.set("status", status)
    q.set("limit", String(limit))
    return request<JobsList>(`/api/jobs?${q.toString()}`)
  },
  getJob: (id: string) => request<Job>(`/api/job/${encodeURIComponent(id)}`),
  getTrace: (id: string) =>
    request<TraceResponse>(`/api/job/${encodeURIComponent(id)}/trace`),

  // Goals
  listGoals: (status?: GoalStatus) => {
    const q = status ? `?status=${status}` : ""
    return request<{ goals: Goal[]; count: number }>(`/api/goals${q}`)
  },
  createGoal: (payload: {
    description: string
    cadence_seconds?: number
    max_runs_per_hour?: number
    start_now?: boolean
  }) =>
    request<{ message: string; goal: Goal }>(`/api/goals`, {
      method: "POST",
      json: payload,
    }),
  updateGoal: (id: string, fields: Partial<Pick<Goal, "description" | "status" | "cadence_seconds" | "max_runs_per_hour">>) =>
    request<{ message: string; goal: Goal }>(`/api/goals/${encodeURIComponent(id)}`, {
      method: "PATCH",
      json: fields,
    }),
  deleteGoal: (id: string) =>
    request<{ message: string; goal_id: string }>(`/api/goals/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  // Tools
  listTools: () => request<{ tools: Tool[]; count: number }>(`/api/tools`),

  // Metrics / system
  metrics: () => request<MetricsSnapshot>(`/api/metrics`),

  // Plan (used in Tools playground)
  runPlan: (input: string) =>
    request<{ success: boolean; summary: string; steps?: unknown[] }>(`/api/plan/run`, {
      method: "POST",
      json: { input },
    }),
}
