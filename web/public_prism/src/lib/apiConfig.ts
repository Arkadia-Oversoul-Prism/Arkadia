/**
 * Centralized API configuration.
 * All components should import from here instead of using their own ORACLE/API_BASE.
 *
 * Dev mode:  uses '' (relative URLs) — Vite proxy forwards /api/* to localhost:8000
 * Prod mode: uses VITE_API_BASE_URL → VITE_API_URL → Render fallback
 */

// The Render backend URL - production fallback only
const RENDER_URL = 'https://arkadia-n26k.onrender.com';

let _safeUrl: string;

if (import.meta.env.DEV) {
  // In development, always use relative URLs so the Vite proxy
  // (vite.config.ts: /api → http://localhost:8000) routes calls to the
  // local Oracle Temple. This ensures settings, key management, and all
  // API calls hit the local backend — not the Render deployment.
  _safeUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? '';
} else {
  // In production, resolve from env vars with Render as final fallback.
  const raw = (
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    RENDER_URL
  ).replace(/\/$/, '');
  _safeUrl = raw.startsWith('http') ? raw : RENDER_URL;
}

// Named exports for the API base URL
export const API_BASE_URL = _safeUrl;
export const API_BASE = _safeUrl;      // Alias for backwards compatibility
export const ORACLE = _safeUrl;
