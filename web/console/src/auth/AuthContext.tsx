/**
 * Read-only operator session identity.
 *
 * The canonical Arkadia client stores its Firebase ID token in same-origin
 * storage. Treat that value as untrusted input: the production API must verify
 * it. Read at request time so sign-in/sign-out in another same-origin tab is
 * reflected without copying credentials into this console's state or logs.
 */
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { setTokenProvider } from "../api/client";

const DEV_UID = "console-operator";
const TOKEN_KEY = "arkadia_token";

function b64url(obj: unknown): string {
  return btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** An unsigned JWT for local development only. Never used in production builds. */
export function mintDevToken(uid = DEV_UID): string {
  const header = { alg: "none", typ: "JWT" };
  const payload = { sub: uid, user_id: uid, email: `${uid}@local` };
  return `${b64url(header)}.${b64url(payload)}.`;
}

function readToken(): string | null {
  const stored = window.localStorage.getItem(TOKEN_KEY);
  return stored || (import.meta.env.DEV ? mintDevToken() : null);
}

interface AuthState {
  uid: string;
  token: string | null;
}

const AuthContext = createContext<AuthState>({ uid: DEV_UID, token: null });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readToken());

  useEffect(() => {
    const sync = () => setToken(readToken());
    const syncOnVisibility = () => {
      if (document.visibilityState === "visible") sync();
    };
    setTokenProvider(readToken);
    window.addEventListener("storage", sync);
    window.addEventListener("focus", sync);
    document.addEventListener("visibilitychange", syncOnVisibility);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("focus", sync);
      document.removeEventListener("visibilitychange", syncOnVisibility);
      setTokenProvider(() => null);
    };
  }, []);

  const value = useMemo(() => ({ uid: DEV_UID, token }), [token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}
