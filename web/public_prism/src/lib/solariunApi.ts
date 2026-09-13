import { apiRequest } from './apiClient';

/**
 * Typed read boundary for the Solariun Home cockpit.
 * These types intentionally describe the existing canonical read surfaces only.
 * No authorization, provenance, or mutation semantics live here.
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
