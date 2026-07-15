/**
 * Centralized API configuration.
 * All components should import from here instead of using their own ORACLE/API_BASE.
 */

// The Render backend URL - this is the production backend
const RENDER_URL = 'https://arkadia-n26k.onrender.com';

// Get from env, fallback to Render URL, fallback to localhost
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  RENDER_URL
).replace(/\/$/, '');

// Ensure we always have a valid URL
const safeUrl = API_BASE_URL.startsWith('http') ? API_BASE_URL : RENDER_URL;

// Named exports for the API base URL
export const API_BASE_URL = safeUrl;
export const API_BASE = safeUrl;      // Alias for backwards compatibility
export const ORACLE = safeUrl;
