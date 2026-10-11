/**
 * Authentication context.
 *
 * Firebase is the identity provider; the backend verifies the Firebase ID token.
 * There is no development bypass: when Firebase is not configured the app runs
 * in an explicit unauthenticated state and protected surfaces say so.
 */
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { onAuthStateChanged, signInWithEmailAndPassword, signOut, User } from "firebase/auth";
import { auth, firebaseConfigured } from "../lib/firebase";
import { apiRequest, ApiError, setApiAuthToken } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { NodeProfile } from "../lib/types";

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
}

export type IdentityState =
  | "unconfigured"
  | "unauthenticated"
  | "loading"
  | "ready"
  | "auth-error"
  | "backend-unavailable";

interface AuthContextValue {
  user: AuthUser | null;
  profile: NodeProfile | null;
  loading: boolean;
  identityState: IdentityState;
  identityError: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOutNow: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  isAuthenticated: boolean;
  firebaseConfigured: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readable(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.kind === "AUTH_REQUIRED") return "Your session is no longer accepted by Arkadia.";
    if (error.kind === "NETWORK_ERROR") return "Arkadia is temporarily unreachable.";
    if (error.kind === "SERVER_ERROR") return "Arkadia could not resolve your identity right now.";
    return error.message;
  }
  return error instanceof Error ? error.message : "Identity hydration failed.";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<NodeProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [identityState, setIdentityState] = useState<IdentityState>(
    firebaseConfigured ? "loading" : "unconfigured",
  );
  const [identityError, setIdentityError] = useState<string | null>(null);

  const fetchProfile = useCallback(async (idToken: string) => {
    setApiAuthToken(idToken);
    setIdentityState("loading");
    setIdentityError(null);
    try {
      const data = await apiRequest<{ user?: NodeProfile }>(endpoints.me);
      setProfile(data.user ?? null);
      setIdentityState("ready");
    } catch (error) {
      setProfile(null);
      setIdentityError(readable(error));
      setIdentityState(
        error instanceof ApiError && error.kind === "AUTH_REQUIRED" ? "auth-error" : "backend-unavailable",
      );
    }
  }, []);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      setIdentityState("unconfigured");
      return;
    }
    return onAuthStateChanged(auth, async (fbUser: User | null) => {
      if (!fbUser) {
        setUser(null);
        setProfile(null);
        setApiAuthToken(null);
        setIdentityState("unauthenticated");
        setLoading(false);
        return;
      }
      setUser({ uid: fbUser.uid, email: fbUser.email, displayName: fbUser.displayName });
      try {
        const token = await fbUser.getIdToken();
        await fetchProfile(token);
      } catch (error) {
        setIdentityError(readable(error));
        setIdentityState("auth-error");
      } finally {
        setLoading(false);
      }
    });
  }, [fetchProfile]);

  const signIn = useCallback(async (email: string, password: string) => {
    if (!auth) throw new Error("Authentication is not configured on this deployment.");
    setIdentityError(null);
    await signInWithEmailAndPassword(auth, email, password);
  }, []);

  const signOutNow = useCallback(async () => {
    setApiAuthToken(null);
    setProfile(null);
    if (auth) await signOut(auth);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!auth?.currentUser) return;
    const token = await auth.currentUser.getIdToken(true);
    await fetchProfile(token);
  }, [fetchProfile]);

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        identityState,
        identityError,
        signIn,
        signOutNow,
        refreshProfile,
        isAuthenticated: user !== null && identityState === "ready",
        firebaseConfigured,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
