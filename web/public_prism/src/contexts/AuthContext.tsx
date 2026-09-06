import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendSignInLinkToEmail, isSignInWithEmailLink, signInWithEmailLink, signOut as fbSignOut, User } from 'firebase/auth';
import { auth } from '../lib/firebase';
import { apiRequest, ApiError, setApiAuthToken } from '../lib/apiClient';

export interface ArkadiaUser { uid: string; email: string | null; displayName: string | null; idToken: string; }
export interface NodeProfile { uid: string; email: string; node_key: string | null; display_name: string; username?: string | null; bio?: string | null; avatar_url?: string | null; role: string; role_sigil: string; ims_id: string | null; access_level: number; status: string; access_tools: string[]; profile_complete?: boolean; }
export interface PersonalCodex { node_key: string; display_name: string; role: string; soul_function: string; name_decode?: Record<string, string>; shadow_states?: string[]; soul_gifts?: string[]; open_loops?: Array<{ id: string; loop: string; status: string; priority: number }>; access_tools?: string[]; access_level?: number; [key: string]: unknown; }
export interface IdentitySpine { version: number; identity: { uid: string; canonical_name: string; preferred_name: string; username?: string | null; role: string; role_sigil: string; ims_id?: string | null }; seed: { created_at?: string | null; sigil?: string; phrase?: string | null; symbols?: string[]; source?: string | null }; orientation: { current_intent?: string; direction?: string; interests?: string[]; values?: string[] }; capability: { baseline: Record<string, unknown>; evidence_count: number; development_events: Array<Record<string, unknown>>; last_assessed_at?: string | null }; relationship: { preferred_ai_role?: string | null; communication_preference?: string | null; collaboration_preference?: string | null }; relational_index: { version: number; status: string; score?: number | null; confidence: number; dimensions: Record<string, number | null>; observations: string[]; last_evaluated_at?: string | null }; symbolic: { seed_phrase?: string | null; seed_symbols: string[]; sigil_seed: string; resonance_signature?: string | null }; continuity: { projections: string[]; ims?: string | null; encyclopedia?: string; codex?: string; echofield?: string }; provenance: { ais_version?: number | null; seed_created_at?: string | null; last_reconciled_at?: string | null; schema_version: number }; }

export type IdentityHydrationState = 'unauthenticated' | 'loading' | 'ready' | 'degraded' | 'auth-error' | 'backend-unavailable';

interface AuthContextValue {
  user: ArkadiaUser | null;
  profile: NodeProfile | null;
  codex: PersonalCodex | null;
  identitySpine: IdentitySpine | null;
  loading: boolean;
  profileLoading: boolean;
  identityState: IdentityHydrationState;
  identityError: string | null;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeMagicLink: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  isAuthenticated: boolean;
  isSovereign: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const MAGIC_LINK_KEY = 'arkadia_magic_email';

function readableIdentityError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.kind === 'AUTH_REQUIRED') return 'Your Firebase session is no longer accepted by Oracle.';
    if (error.kind === 'NETWORK_ERROR') return 'Oracle is temporarily unreachable.';
    if (error.kind === 'SERVER_ERROR') return 'Oracle could not resolve your identity right now.';
    return error.message;
  }
  return error instanceof Error ? error.message : 'Identity hydration failed.';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ArkadiaUser | null>(null);
  const [profile, setProfile] = useState<NodeProfile | null>(null);
  const [codex, setCodex] = useState<PersonalCodex | null>(null);
  const [identitySpine, setIdentitySpine] = useState<IdentitySpine | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [identityState, setIdentityState] = useState<IdentityHydrationState>('unauthenticated');
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async (idToken: string) => {
    setProfileLoading(true);
    setIdentityState('loading');
    setIdentityError(null);
    setError(null);
    setApiAuthToken(idToken);

    try {
      const data = await apiRequest<{ user?: NodeProfile }>('/api/me');
      setProfile(data.user ?? null);
    } catch (profileError) {
      const message = readableIdentityError(profileError);
      setProfile(null);
      setIdentityError(message);
      setIdentityState(profileError instanceof ApiError && profileError.kind === 'AUTH_REQUIRED' ? 'auth-error' : 'backend-unavailable');
      setCodex(null);
      setIdentitySpine(null);
      setProfileLoading(false);
      return;
    }

    let degraded = false;
    let lastError: unknown = null;

    try {
      const data = await apiRequest<{ codex?: PersonalCodex }>('/api/me/codex');
      setCodex(data.codex ?? null);
    } catch (codexError) {
      // A missing Codex is a valid state for authenticated users without an IMS node.
      if (codexError instanceof ApiError && codexError.status === 404) {
        setCodex(null);
      } else {
        degraded = true;
        lastError = codexError;
        setCodex(null);
      }
    }

    try {
      const data = await apiRequest<{ identity_spine?: IdentitySpine }>('/api/me/identity-spine');
      setIdentitySpine(data.identity_spine ?? null);
      if (!data.identity_spine) degraded = true;
    } catch (spineError) {
      degraded = true;
      lastError = spineError;
      setIdentitySpine(null);
    }

    if (degraded) {
      setIdentityState(lastError instanceof ApiError && lastError.kind === 'NETWORK_ERROR' ? 'backend-unavailable' : 'degraded');
      setIdentityError(readableIdentityError(lastError));
    } else {
      setIdentityState('ready');
      setIdentityError(null);
    }
    setProfileLoading(false);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (user?.idToken) await fetchProfile(user.idToken);
  }, [user, fetchProfile]);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      setIdentityState('unauthenticated');
      return;
    }
    if (isSignInWithEmailLink(auth, window.location.href)) {
      const savedEmail = localStorage.getItem(MAGIC_LINK_KEY) || '';
      if (savedEmail) {
        signInWithEmailLink(auth, savedEmail, window.location.href)
          .then(() => localStorage.removeItem(MAGIC_LINK_KEY))
          .catch(e => setError(e.message));
      }
    }
    const unsub = onAuthStateChanged(auth, async (fbUser: User | null) => {
      if (fbUser) {
        const idToken = await fbUser.getIdToken();
        setApiAuthToken(idToken);
        setUser({ uid: fbUser.uid, email: fbUser.email, displayName: fbUser.displayName, idToken });
        await fetchProfile(idToken);
      } else {
        setApiAuthToken(null);
        setUser(null);
        setProfile(null);
        setCodex(null);
        setIdentitySpine(null);
        setIdentityError(null);
        setIdentityState('unauthenticated');
      }
      setLoading(false);
    });
    return () => unsub();
  }, [fetchProfile]);

  const signIn = async (email: string, password: string) => {
    if (!auth) throw new Error('Firebase not configured');
    setError(null);
    await signInWithEmailAndPassword(auth, email, password);
  };

  const register = async (email: string, password: string, displayName?: string) => {
    if (!auth) throw new Error('Firebase not configured');
    setError(null);
    if (password.length < 8) throw new Error('Password must be at least 8 characters');
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    const name = (displayName || '').trim();
    if (name && cred.user) {
      const idToken = await cred.user.getIdToken();
      setApiAuthToken(idToken);
      try {
        await apiRequest('/api/me', { method: 'PATCH', body: JSON.stringify({ display_name: name }) });
      } catch (e) {
        setError(readableIdentityError(e));
      }
    }
  };

  const sendMagicLink = async (email: string) => {
    if (!auth) throw new Error('Firebase not configured');
    setError(null);
    await sendSignInLinkToEmail(auth, email, { url: window.location.href, handleCodeInApp: true });
    localStorage.setItem(MAGIC_LINK_KEY, email);
  };

  const completeMagicLink = async (email: string) => {
    if (!auth) throw new Error('Firebase not configured');
    setError(null);
    await signInWithEmailLink(auth, email, window.location.href);
    localStorage.removeItem(MAGIC_LINK_KEY);
  };

  const signOut = async () => {
    if (!auth) return;
    await fbSignOut(auth);
    setApiAuthToken(null);
    setUser(null);
    setProfile(null);
    setCodex(null);
    setIdentitySpine(null);
    setIdentityError(null);
    setIdentityState('unauthenticated');
  };

  return <AuthContext.Provider value={{
    user, profile, codex, identitySpine, loading, profileLoading, identityState, identityError, error,
    signIn, register, sendMagicLink, completeMagicLink, signOut, refreshProfile,
    isAuthenticated: !!user,
    isSovereign: (profile?.access_level ?? 0) >= 3,
  }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
