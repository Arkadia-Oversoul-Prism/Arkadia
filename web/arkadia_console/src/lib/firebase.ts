/**
 * Firebase client bootstrap.
 *
 * The canonical image injects the public web config at startup
 * (`window.__ARKADIA_FIREBASE_CONFIG__`). Vite env values are a local-development
 * fallback only. Firebase Web config is client-side configuration, never the
 * Admin service account.
 */
import { initializeApp, getApps, FirebaseApp } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";

declare global {
  interface Window {
    __ARKADIA_FIREBASE_CONFIG__?: {
      apiKey?: string;
      authDomain?: string;
      projectId?: string;
      appId?: string;
    };
  }
}

const runtimeConfig =
  typeof window !== "undefined" ? window.__ARKADIA_FIREBASE_CONFIG__ : undefined;
const apiKey = runtimeConfig?.apiKey || import.meta.env.VITE_FIREBASE_API_KEY;
const authDomain = runtimeConfig?.authDomain || import.meta.env.VITE_FIREBASE_AUTH_DOMAIN;
const projectId = runtimeConfig?.projectId || import.meta.env.VITE_FIREBASE_PROJECT_ID;
const appId = runtimeConfig?.appId || import.meta.env.VITE_FIREBASE_APP_ID;

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (apiKey && authDomain && projectId && appId) {
  try {
    app = getApps().length === 0 ? initializeApp({ apiKey, authDomain, projectId, appId }) : getApps()[0];
    auth = getAuth(app);
  } catch {
    // Do not log config objects or SDK exception details into the browser console.
    app = null;
    auth = null;
    console.warn("[Arkadia] Firebase initialization failed; authentication is unavailable.");
  }
} else {
  console.warn("[Arkadia] Firebase client configuration is incomplete; authentication is unavailable.");
}

export { app, auth };
export const firebaseConfigured = app !== null;
