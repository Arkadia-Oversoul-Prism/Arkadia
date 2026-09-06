import { API_BASE } from './apiConfig';

export type ApiFailureKind =
  | 'BAD_REQUEST'
  | 'AUTH_REQUIRED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'UNPROCESSABLE'
  | 'RATE_LIMITED'
  | 'SERVER_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN';

export class ApiError extends Error {
  readonly status: number | null;
  readonly kind: ApiFailureKind;
  readonly path: string;

  constructor(message: string, options: { status?: number | null; kind?: ApiFailureKind; path: string }) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status ?? null;
    this.kind = options.kind ?? 'UNKNOWN';
    this.path = options.path;
  }
}

const TOKEN_KEY = 'arkadia_token';
let authToken: string | null = typeof window !== 'undefined' ? window.localStorage.getItem(TOKEN_KEY) : null;

export function setApiAuthToken(token: string | null): void {
  authToken = token;
  if (typeof window === 'undefined') return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export function getApiAuthToken(): string | null { return authToken; }

function classify(status: number): ApiFailureKind {
  if (status === 400) return 'BAD_REQUEST';
  if (status === 401) return 'AUTH_REQUIRED';
  if (status === 403) return 'FORBIDDEN';
  if (status === 404) return 'NOT_FOUND';
  if (status === 409) return 'CONFLICT';
  if (status === 422) return 'UNPROCESSABLE';
  if (status === 429) return 'RATE_LIMITED';
  if (status >= 500) return 'SERVER_ERROR';
  return 'UNKNOWN';
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (authToken && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${authToken}`);
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : 'Oracle network request failed', {
      kind: 'NETWORK_ERROR',
      path,
    });
  }

  const raw = await response.text();
  let payload: unknown = null;
  if (raw) {
    try { payload = JSON.parse(raw); } catch { payload = raw; }
  }

  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
      ? String((payload as { detail?: unknown }).detail ?? '')
      : '';
    throw new ApiError(detail || `${response.status} ${response.statusText}`, {
      status: response.status,
      kind: classify(response.status),
      path,
    });
  }

  // 204 is a successful no-content response and must not be parsed as JSON.
  if (response.status === 204 || !raw) return undefined as T;
  return payload as T;
}

export function apiPath(path: string): string { return `${API_BASE}${path}`; }
