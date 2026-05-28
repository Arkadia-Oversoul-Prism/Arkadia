/**
 * Backward-compatible hook for anonymous session UID (used by conversationService).
 * Now delegates to the real AuthContext. Authenticated users use their Firebase UID;
 * unauthenticated users get a stable session-scoped anonymous ID.
 */
import { useState, useEffect } from 'react';
import { signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { auth } from '../lib/firebase';

interface ArkadiaAuthState {
  uid: string | null;
  loading: boolean;
}

export function useArkadiaAuth(): ArkadiaAuthState {
  const [uid, setUid] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // Authenticated users (real or anonymous) — use their UID directly
        setUid(user.uid);
        setLoading(false);
      } else {
        // No user at all — sign in anonymously for conversation persistence
        try {
          const result = await signInAnonymously(auth!);
          setUid(result.user.uid);
        } catch (e) {
          console.warn('[Arkadia] Anonymous auth failed — stateless mode.', e);
          setUid(null);
        } finally {
          setLoading(false);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  return { uid, loading };
}
