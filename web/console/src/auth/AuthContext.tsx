/**
 * Read-only session identity.
 *
 * This console holds no login form and no mutation control. It mints an
 * unsigned dev token (mirroring the derived console's AuthContext) so the
 * read-only surfaces can reach an auth-gated substrate in dev-mode. Against a
 * production backend this token 401s — which is truthful, and is shown as such
 * rather than hidden.
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
  const [token] = useState<string | null>(() => mintDevToken());

  useEffect(() => {
    setTokenProvider(() => token);
  }, [token]);

  const value = useMemo(() => ({ uid: DEV_UID, token }), [token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}
