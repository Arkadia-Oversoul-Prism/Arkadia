import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getFirestore, Firestore } from 'firebase/firestore';
import { getAuth, Auth } from 'firebase/auth';

const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
const authDomain = import.meta.env.VITE_FIREBASE_AUTH_DOMAIN;
const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;
const appId = import.meta.env.VITE_FIREBASE_APP_ID;

let app: FirebaseApp | null = null;
let db: Firestore | null = null;
let auth: Auth | null = null;

if (apiKey && authDomain && projectId && appId) {
  try {
    const firebaseConfig = { apiKey, authDomain, projectId, appId };
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    db = getFirestore(app);
    auth = getAuth(app);
  } catch (e) {
    console.warn('[Arkadia] Firebase init failed — memory layer offline.', e);
    app = null;
    db = null;
    auth = null;
  }
} else {
  console.warn('[Arkadia] Firebase env vars absent — memory layer offline. Oracle still operational.');
}

export { app, db, auth };
