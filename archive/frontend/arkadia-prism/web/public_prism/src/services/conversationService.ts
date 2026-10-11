import {
  collection,
  addDoc,
  query,
  orderBy,
  limit,
  getDocs,
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
  Timestamp,
} from 'firebase/firestore';
import { db } from '../lib/firebase';

export interface ConversationMessage {
  role: 'user' | 'oracle';
  content: string;
}

const SESSION_TTL_MS = 4 * 60 * 60 * 1000;

export async function saveMessage(
  uid: string,
  sessionId: string,
  role: 'user' | 'oracle',
  content: string
): Promise<void> {
  if (!db || !uid) return;
  try {
    const ref = collection(db, 'users', uid, 'conversations', sessionId, 'messages');
    await addDoc(ref, { role, content, timestamp: serverTimestamp() });
  } catch (e) {
    console.warn('[Arkadia] saveMessage failed silently.', e);
  }
}

export async function getRecentMessages(
  uid: string,
  sessionId: string,
  limitCount = 10
): Promise<ConversationMessage[]> {
  if (!db || !uid) return [];
  try {
    const ref = collection(db, 'users', uid, 'conversations', sessionId, 'messages');
    const q = query(ref, orderBy('timestamp', 'asc'), limit(limitCount));
    const snap = await getDocs(q);
    return snap.docs.map((d) => {
      const data = d.data();
      return { role: data.role as 'user' | 'oracle', content: data.content as string };
    });
  } catch (e) {
    console.warn('[Arkadia] getRecentMessages failed silently.', e);
    return [];
  }
}

export async function getOrCreateSession(uid: string): Promise<string> {
  if (!db || !uid) return `local-${Date.now()}`;
  try {
    const ref = doc(db, 'users', uid, 'currentSession', 'active');
    const snap = await getDoc(ref);
    if (snap.exists()) {
      const data = snap.data();
      const createdAt: Timestamp = data.createdAt;
      const age = Date.now() - createdAt.toMillis();
      if (age < SESSION_TTL_MS) {
        return data.sessionId as string;
      }
    }
    const newSessionId = `session-${Date.now()}`;
    await setDoc(ref, { sessionId: newSessionId, createdAt: serverTimestamp() });
    return newSessionId;
  } catch (e) {
    console.warn('[Arkadia] getOrCreateSession failed silently.', e);
    return `local-${Date.now()}`;
  }
}

export async function saveUserPattern(
  uid: string,
  patternKey: string,
  patternValue: string
): Promise<void> {
  if (!db || !uid) return;
  try {
    const ref = doc(db, 'users', uid, 'profile', patternKey);
    await setDoc(ref, { value: patternValue, updatedAt: serverTimestamp() }, { merge: true });
  } catch (e) {
    console.warn('[Arkadia] saveUserPattern failed silently.', e);
  }
}
