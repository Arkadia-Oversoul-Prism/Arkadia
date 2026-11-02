/**
 * HTTP client for the Arkadia substrate.
 *
 * Browser actions remain governed by backend authorization. The client does not
 * hold authority; it only forwards the authenticated token. Auth is a bearer token; in dev-mode the substrate
 * decodes an unsigned JWT (see AuthContext). A 401 is a truthful state, not an
 * error to hide.
 */
import { API_BASE } from "../../lib/apiConfig";

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

/**
 * The identity these surfaces present is the canonical application's own bearer
 * token, read at request time from the one storage key the canonical
 * `AuthContext` writes (`setApiAuthToken`). Reading per request means a sign-in
 * or sign-out in another same-origin tab is reflected without copying a
 * credential into this module's state or logs.
 *
 * The retired standalone application minted an unsigned development JWT when no
 * token was stored. That bypass is deliberately NOT carried over: the canonical
 * application has no development identity bypass (`contexts/AuthContext.tsx`),
 * and re-introducing one here would weaken the authorization semantics this
 * migration is required to preserve.
 */
const TOKEN_KEY = "arkadia_token";
type TokenProvider = () => string | null;
let tokenProvider: TokenProvider = () => window.localStorage.getItem(TOKEN_KEY);
export function setTokenProvider(fn: TokenProvider): void {
  tokenProvider = fn;
}

/** Same-origin by default; the canonical `lib/apiConfig.ts` owns origin resolution. */
const BASE = API_BASE;

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
