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
    try { data = JSON.parse(text) } catch { data = text }
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

// ── Job types ─────────────────────────────────────────────────────────────────

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

// ── Corpus / Codex types ──────────────────────────────────────────────────────

export interface HeartbeatResponse {
  status: string
  resonance: number
}

export interface SourceItem {
  name: string
  configured: boolean
  authenticated?: boolean
  live?: boolean
  repo?: string
  branch?: string
}

export interface SourcesResponse {
  sources: SourceItem[]
}

export interface ArkDateSync {
  auto_sync_active: boolean
  refresh_count: number
  last_sync_coordinate: string
  last_scroll_count: number
  cadence_minutes: number
}

export interface ArkDateResponse {
  ark_year: number
  ark_total_years: number
  day_in_year: number
  total_ark_day: number
  pulse: number
  breath: number
  ark_completion_pct: number
  coordinate: string
  display: string
  epoch: string
  linear_utc: string
  linear_note: string
  sync: ArkDateSync
}

export interface CodexScroll {
  id: string
  source: string
  category: string
  priority: number
  label: string
  description: string
  chars: number
  preview: string
  content: string
  fetched_at: string | null
  error: string | null
}

export interface CodexResponse {
  status: string
  total_docs: number
  live_docs: number
  total_chars: number
  scrolls: Record<string, CodexScroll>
}

export interface OpenLoopItem {
  id: string
  name: string
  status?: string
  next_action?: string
  target?: string
}

export interface OpenLoopGroup {
  level: string
  label: string
  color: string
  section_title: string
  loops: OpenLoopItem[]
}

export interface OpenLoopsResponse {
  source: string
  parsed_at: string
  total: number
  groups: OpenLoopGroup[]
  error?: string
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

  // ── Field Intelligence ──────────────────────────────────────────────────
  heartbeat: () => request<HeartbeatResponse>(`/api/heartbeat`),
  sources: () => request<SourcesResponse>(`/api/sources`),
  arkDate: () => request<ArkDateResponse>(`/api/ark-date`),
  codex: () => request<CodexResponse>(`/api/codex`),
  openLoops: () => request<OpenLoopsResponse>(`/api/open-loops`),
  refreshCorpus: () =>
    request<{ status: string }>(`/api/corpus/refresh`, { method: "POST" }),
}
