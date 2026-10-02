/** Response types for the read-only surfaces the console consumes. */

export interface Approval {
  id: string;
  tool_name: string;
  payload: Record<string, unknown>;
  description: string;
  status: string;
  created_at: string;
  decided_at: string | null;
  subject_ref: string | null;
  decided_by: string | null;
  consumed_at: string | null;
  consumed_by: string | null;
}

export interface JobExecution {
  task_id?: string;
  state?: string;
  checkpoints?: unknown[];
  artifacts?: unknown[];
  events?: unknown[];
}

export interface Job {
  job_id: string;
  status: string;
  intent: Record<string, unknown>;
  result?: unknown;
  error?: string | null;
  retries?: number;
  source?: string;
  created_at?: number;
  updated_at?: number;
  started_at?: number | null;
  ended_at?: number | null;
  execution?: JobExecution;
}

export interface JobTrace {
  job_id: string;
  status: string;
  trace: unknown;
}

export interface ToolManifest {
  name: string;
  description?: string;
  requires_approval?: boolean;
  payload_schema?: Record<string, string>;
}
