/**
 * Canonical API configuration for the Arkadia Console.
 *
 * One canonical deployment (ADR-016): the frontend is served from the same
 * origin as the backend, so the API base is same-origin by default. A build-time
 * `VITE_API_BASE_URL` may point at a different origin (for example a preview),
 * and the Android bridge is the authority when the app is embedded.
 *
 * There is no hardcoded remote fallback: an unconfigured origin resolves to
 * same-origin relative requests, never to an unverified deployment.
 */

function androidApiBase(): { present: boolean; value: string } {
  if (typeof window === "undefined") return { present: false, value: "" };
  const bridge = (
    window as Window & { ArkadiaAndroid?: { getApiBaseUrl?: () => string } }
  ).ArkadiaAndroid;
  if (!bridge?.getApiBaseUrl) return { present: false, value: "" };
  try {
    return { present: true, value: bridge.getApiBaseUrl()?.replace(/\/$/, "") || "" };
  } catch {
    return { present: true, value: "" };
  }
}

const nativeApi = androidApiBase();

function resolveBase(): string {
  if (nativeApi.present) return nativeApi.value;
  const configured = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
  return configured.startsWith("http") ? configured : "";
}

export const API_BASE = resolveBase();
