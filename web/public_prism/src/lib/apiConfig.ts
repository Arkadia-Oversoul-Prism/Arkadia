/**
 * Centralized API configuration.
 * All components should import from here instead of using their own ORACLE/API_BASE.
 */

// The Render backend URL - set in Vercel environment variables
const RENDER_URL = 'https://arkadia-n26k.onrender.com';

// Get from env, fallback to Render URL, fallback to localhost
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  RENDER_URL
).replace(/\/$/, '');

export { API_BASE_URL };
export const ORACLE = API_BASE_URL;
