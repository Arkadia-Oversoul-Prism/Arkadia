/** Read-only endpoint bindings. Paths copied verbatim from the substrate routes. */
import { api } from "./client";
import type { Approval, Job, JobTrace, ToolManifest } from "./types";

export const heartbeat = () => api.get<{ status: string }>("/api/heartbeat", { auth: false });

export const approvals = () => api.get<{ approvals: Approval[] }>("/api/approvals");

export const jobs = () => api.get<{ jobs: Job[]; stats?: Record<string, number> }>("/api/jobs");

export const jobTrace = (jobId: string) =>
  api.get<JobTrace>(`/api/job/${encodeURIComponent(jobId)}/trace`);

export const tools = () => api.get<{ tools: ToolManifest[] }>("/api/tools");
