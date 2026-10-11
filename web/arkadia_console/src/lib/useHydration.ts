/**
 * Hydration-state hook for authenticated reads.
 *
 * A surface that fetches a protected contract must distinguish "still loading",
 * "this identity cannot see it", and "the backend is down". Collapsing them into
 * a single `error` string is how a 401 gets presented as a network outage.
 */
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./apiClient";

export type HydrationState = "idle" | "loading" | "ready" | "auth-required" | "unavailable" | "error";

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

function stateFor(error: ApiError): HydrationState {
  if (error.kind === "AUTH_REQUIRED") return "auth-required";
  if (error.kind === "FORBIDDEN") return "auth-required";
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
