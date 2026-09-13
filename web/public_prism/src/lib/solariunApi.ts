import { apiRequest } from './apiClient';

/**
 * Typed read/write boundary for the Solariun Home cockpit.
 * These types intentionally describe the existing canonical SolSpire surfaces only.
 * Authorization and provenance semantics remain server-side.
 */
export type SolariunRecord = Record<string, unknown>;

export interface SolariunPulse {
  state_summary?: string;
  summary?: string;
  period?: string;
  open_loops?: string;
  open_loop_summary?: string;
  loops?: string;
  current_signal?: string;
  signal?: string;
  signal_summary?: string;
  created_at?: string | number;
  updated_at?: string | number;
  occurred_at?: string | number;
  [key: string]: unknown;
}

export interface SolariunWorkload {
  title?: string;
  display_name?: string;
  objective?: string;
  status?: string;
  phase?: string;
  workload_type?: string;
  [key: string]: unknown;
}

export interface SolariunWorkEvent {
  work_event_id?: string;
  id?: string;
  event_type?: string;
  type?: string;
  state_after_ref?: string;
  work_ref?: string;
  scope_ref?: string;
  occurred_at?: string | number;
  created_at?: string | number;
  [key: string]: unknown;
}

export interface SolariunSynthesis {
  summary?: string;
  synthesis_summary?: string;
  created_at?: string | number;
  updated_at?: string | number;
  [key: string]: unknown;
}

export interface SolariunProposal {
  proposal_id?: string;
  objective?: string;
  requested_decision?: string;
  proposal_status?: string;
  status?: string;
  decision_ref?: string;
  [key: string]: unknown;
}

export interface SolariunPulseResponse { pulse?: SolariunPulse; }
export interface SolariunWorkloadResponse { workload?: SolariunWorkload; }
export interface SolariunWorkEventsResponse {
  work_events?: SolariunWorkEvent[];
  events?: SolariunWorkEvent[];
}
export interface SolariunSynthesisResponse { synthesis?: SolariunSynthesis; }
export interface SolariunProposalsResponse { proposals?: SolariunProposal[]; }
export interface SolariunWorkEventResponse { work_event?: SolariunWorkEvent; ok?: boolean; }

export interface EmitSolariunWorkEventInput {
  event_type: string;
  occurred_at?: number;
  event_version?: number;
  work_ref?: string;
  parent_event_ref?: string;
  sequence_ref?: string;
  scope_ref?: string;
  actor_ref?: string;
  artifact_refs?: string[];
  state_before_ref?: string;
  state_after_ref?: string;
  decision_ref?: string;
  witness_ref?: string;
  status?: string;
  supersedes_ref?: string;
  reversal_of_ref?: string;
  created_by_event?: string;
  schema_version?: string;
}

export const getSolariunPulse = () =>
  apiRequest<SolariunPulseResponse>('/solspire/pulses/today');

export const getSolariunWorkload = () =>
  apiRequest<SolariunWorkloadResponse>('/solspire/workloads');

export const getSolariunWorkEvents = (limit = 8) =>
  apiRequest<SolariunWorkEventsResponse>(`/solspire/workevents?limit=${limit}`);

export const getSolariunSynthesis = () =>
  apiRequest<SolariunSynthesisResponse>('/solspire/syntheses/current');

export const getSolariunProposals = (limit = 20) =>
  apiRequest<SolariunProposalsResponse>(`/solspire/proposals?limit=${limit}`);

export const emitSolariunWorkEvent = (input: EmitSolariunWorkEventInput) =>
  apiRequest<SolariunWorkEventResponse>('/solspire/workevents', {
    method: 'POST',
    body: JSON.stringify({
      occurred_at: input.occurred_at ?? Date.now() / 1000,
      event_version: input.event_version ?? 1,
      status: input.status ?? 'RECORDED',
      schema_version: input.schema_version ?? '1',
      artifact_refs: input.artifact_refs ?? [],
      ...input,
    }),
  });

export const recordSolariunProposalDecision = (proposalId: string, decision: 'ACCEPTED' | 'DECLINED' | 'WITHDRAWN') =>
  apiRequest<{ ok?: boolean; proposal?: SolariunProposal }>(`/solspire/proposals/${proposalId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });
