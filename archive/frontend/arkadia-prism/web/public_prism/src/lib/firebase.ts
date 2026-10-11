import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getFirestore, Firestore } from 'firebase/firestore';
import { getAuth, Auth } from 'firebase/auth';

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

// Prefer the runtime-injected public config for the canonical Render image.
// Vite env values remain a fallback for local development only.
const runtimeConfig = typeof window !== 'undefined' ? window.__ARKADIA_FIREBASE_CONFIG__ : undefined;
const apiKey = runtimeConfig?.apiKey || import.meta.env.VITE_FIREBASE_API_KEY;
const authDomain = runtimeConfig?.authDomain || import.meta.env.VITE_FIREBASE_AUTH_DOMAIN;
const projectId = runtimeConfig?.projectId || import.meta.env.VITE_FIREBASE_PROJECT_ID;
const appId = runtimeConfig?.appId || import.meta.env.VITE_FIREBASE_APP_ID;

let app: FirebaseApp | null = null;
let db: Firestore | null = null;
let auth: Auth | null = null;

if (apiKey && authDomain && projectId && appId) {
  try {
    const firebaseConfig = { apiKey, authDomain, projectId, appId };
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    db = getFirestore(app);
    auth = getAuth(app);
  } catch {
    // Do not log config objects or SDK exception details into browser console.
    app = null;
    db = null;
    auth = null;
    console.warn('[Arkadia] Firebase initialization failed; authentication is unavailable.');
  }
} else {
  console.warn('[Arkadia] Firebase client configuration is incomplete; authentication is unavailable.');
}

export { app, db, auth };
