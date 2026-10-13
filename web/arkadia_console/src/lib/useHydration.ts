/**
 * Hydration-state hook for authenticated reads.
 *
 * A surface that fetches a protected contract must distinguish "still loading",
 * "no identity is present", "this identity is not entitled to the answer", and
 * "the backend is down". Collapsing them into a single `error` string is how a
 * 401 gets presented as a network outage.
 *
 * Authentication and authorization are separate layers and are kept separate
 * here. `AUTH_REQUIRED` (401) means *no usable identity* — signing in can change
 * the answer. `FORBIDDEN` (403) means the identity **is** known and the backend
 * refused the act: the authoritative example is `api/approval_routes.py`, where
 * a signed-in principal without the `Govern` authority receives 403 (pinned by
 * `tests/test_authority_boundary.py`). Reporting that as "sign in to load it" is
 * false — the viewer is already signed in — and invites a retry that can never
 * succeed. The two states must not be conflated.
 */
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./apiClient";

export type HydrationState =
  | "idle"
  | "loading"
  | "ready"
  | "auth-required"
  | "forbidden"
  | "unavailable"
  | "error";

export interface Hydration<T> {
  state: HydrationState;
  data: T | null;
  error: ApiError | null;
  reload: () => void;
}

function classify(error: unknown, path: string): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError(error instanceof Error ? error.message : "Request failed", {
    kind: "UNKNOWN",
    path,
  });
}

export function stateFor(error: ApiError): HydrationState {
  if (error.kind === "AUTH_REQUIRED") return "auth-required";
  // 403 is an authorization refusal by a *known* identity, not a missing one.
  // `FORBIDDEN` is therefore its own state; mapping it to `auth-required` would
  // tell an already-signed-in viewer to sign in.
  if (error.kind === "FORBIDDEN") return "forbidden";
  if (error.kind === "NETWORK_ERROR" || error.kind === "SERVER_ERROR") return "unavailable";
  return "error";
}

export function useHydration<T>(
  path: string,
  fetcher: (path: string) => Promise<T>,
  deps: unknown[] = [],
): Hydration<T> {
  const [state, setState] = useState<HydrationState>("idle");
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    setError(null);
    fetcher(path)
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setState("ready");
      })
      .catch((caught) => {
        if (cancelled) return;
        const apiError = classify(caught, path);
        setError(apiError);
        setData(null);
        setState(stateFor(apiError));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, nonce, ...deps]);

  return { state, data, error, reload };
}
