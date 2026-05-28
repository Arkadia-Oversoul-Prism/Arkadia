import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  signOut as fbSignOut,
  User,
} from 'firebase/auth';
import { auth } from '../lib/firebase';

export interface ArkadiaUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  idToken: string;
}

export interface NodeProfile {
  uid: string;
  email: string;
  node_key: string | null;
  display_name: string;
  role: string;
  role_sigil: string;
  ims_id: string | null;
  access_level: number;
  status: string;
  access_tools: string[];
}

export interface PersonalCodex {
  node_key: string;
  display_name: string;
  role: string;
  soul_function: string;
  name_decode?: Record<string, string>;
  shadow_states?: string[];
  soul_gifts?: string[];
  open_loops?: Array<{ id: string; loop: string; status: string; priority: number }>;
  access_tools?: string[];
  access_level?: number;
  [key: string]: unknown;
}

interface AuthContextValue {
  user: ArkadiaUser | null;
  profile: NodeProfile | null;
  codex: PersonalCodex | null;
  loading: boolean;
  profileLoading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeMagicLink: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  isAuthenticated: boolean;
  isSovereign: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

const MAGIC_LINK_KEY = 'arkadia_magic_email';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ArkadiaUser | null>(null);
  const [profile, setProfile] = useState<NodeProfile | null>(null);
  const [codex, setCodex] = useState<PersonalCodex | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async (idToken: string) => {
    setProfileLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/me`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data.user ?? null);
      }
    } catch {
      // Backend may be unavailable in dev — not fatal
    }

    try {
      const res2 = await fetch(`${API_BASE}/api/me/codex`, {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (res2.ok) {
        const data2 = await res2.json();
        setCodex(data2.codex ?? null);
      }
    } catch {
      // no codex yet — not fatal
    }
    setProfileLoading(false);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (user?.idToken) await fetchProfile(user.idToken);
  }, [user, fetchProfile]);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }

    // Handle magic link completion on page load
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
        const arkUser: ArkadiaUser = {
          uid: fbUser.uid,
          email: fbUser.email,
          displayName: fbUser.displayName,
          idToken,
        };
        setUser(arkUser);
        await fetchProfile(idToken);
      } else {
        setUser(null);
        setProfile(null);
        setCodex(null);
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

  const sendMagicLink = async (email: string) => {
    if (!auth) throw new Error('Firebase not configured');
    setError(null);
    const actionCodeSettings = {
      url: window.location.href,
      handleCodeInApp: true,
    };
    await sendSignInLinkToEmail(auth, email, actionCodeSettings);
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
    setUser(null);
    setProfile(null);
    setCodex(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      profile,
      codex,
      loading,
      profileLoading,
      error,
      signIn,
      sendMagicLink,
      completeMagicLink,
      signOut,
      refreshProfile,
      isAuthenticated: !!user,
      isSovereign: (profile?.access_level ?? 0) >= 3,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
