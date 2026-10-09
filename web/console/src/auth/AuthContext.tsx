/**
 * Read-only operator session identity. Reuse the signed-in Arkadia Firebase
 * ID token from same-origin storage. Unsigned development tokens are created
 * only in a Vite development build.
 */
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { setTokenProvider } from "../api/client";

const DEV_UID = "console-operator";

function b64url(obj: unknown): string {
  return btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** An unsigned JWT: header.payload.signature-placeholder. Dev-mode only. */
export function mintDevToken(uid = DEV_UID): string {
  const header = { alg: "none", typ: "JWT" };
  const payload = { sub: uid, user_id: uid, email: `${uid}@local` };
  return `${b64url(header)}.${b64url(payload)}.`;
}

interface AuthState {
  uid: string;
  token: string | null;
}

const AuthContext = createContext<AuthState>({ uid: DEV_UID, token: null });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token] = useState<string | null>(() => {
    const stored = window.localStorage.getItem("arkadia_token");
    if (stored) return stored;
    return import.meta.env.DEV ? mintDevToken() : null;
  });

  useEffect(() => {
    setTokenProvider(() => token);
  }, [token]);

  const value = useMemo(() => ({ uid: DEV_UID, token }), [token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}
