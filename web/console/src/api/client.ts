/**
 * HTTP client for the Arkadia substrate.
 *
 * Browser actions remain governed by backend authorization. The client does not
 * hold authority; it only forwards the authenticated token. Auth is a bearer token; in dev-mode the substrate
 * decodes an unsigned JWT (see AuthContext). A 401 is a truthful state, not an
 * error to hide.
 */
export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
  get isAuth(): boolean {
    return this.status === 401;
  }
  get isForbidden(): boolean {
    return this.status === 403;
  }
}

type TokenProvider = () => string | null;
let tokenProvider: TokenProvider = () => null;
export function setTokenProvider(fn: TokenProvider): void {
  tokenProvider = fn;
}

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function get<T>(path: string, opts: { auth?: boolean; signal?: AbortSignal; token?: string } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.auth !== false) {
    const token = opts.token ?? tokenProvider();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}${path}`, { method: "GET", headers, signal: opts.signal });
  const text = await res.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }
  if (!res.ok) {
    const detail =
      parsed && typeof parsed === "object" && "detail" in (parsed as object)
        ? (parsed as { detail: unknown }).detail
        : parsed ?? res.statusText;
    throw new ApiError(res.status, detail);
  }
  return parsed as T;
}

async function post<T>(path: string, body: unknown, opts: { auth?: boolean; token?: string } = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.auth !== false) {
    const token = opts.token ?? tokenProvider();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
  const text = await res.text();
  let parsed: unknown = null;
  if (text) {
    try { parsed = JSON.parse(text); } catch { parsed = text; }
  }
  if (!res.ok) {
    const detail =
      parsed && typeof parsed === "object" && "detail" in (parsed as object)
        ? (parsed as { detail: unknown }).detail
        : parsed ?? res.statusText;
    throw new ApiError(res.status, detail);
  }
  return parsed as T;
}

export const api = { get, post };
