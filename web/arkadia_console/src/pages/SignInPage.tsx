/**
 * Sign-in surface.
 *
 * Firebase is the identity provider and the backend verifies the ID token.
 * There is no development bypass: if Firebase is not configured this page says
 * so and offers no credential path, rather than accepting a local identity.
 */
import { FormEvent, useState } from "react";
import { Page, Panel } from "../components/ui";
import { useAuth } from "../contexts/AuthContext";
import { consumeReturnTo } from "../lib/returnTo";
import type { SurfaceId } from "../lib/surfaces";

export function SignInPage({ onNavigate }: { onNavigate: (id: SurfaceId, section?: string) => void }) {
  const { signIn, firebaseConfigured, identityState, identityError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setLocalError(null);
    try {
      await signIn(email, password);
      // Only a confirmed sign-in crosses back: the destination is consumed
      // (and cleared) here, validated through the router, so a failed sign-in
      // neither navigates nor spends the remembered destination.
      const destination = consumeReturnTo(window.location.search);
      if (destination) onNavigate(destination.surface, destination.section);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  const error = localError ?? identityError;

  return (
    <Page title="Sign in" subtitle="Authenticate against the canonical Arkadia backend.">
      <Panel className="mx-auto max-w-md">
        {!firebaseConfigured ? (
          <p className="text-sm text-amber-200/80">
            Authentication is not configured on this deployment. Sign-in is unavailable.
          </p>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <div className="flex gap-2 border-b border-white/10 pb-2">
              <button
                type="button"
                data-testid="tab-signin"
                className="rounded px-2 py-1 font-mono text-[11px] uppercase tracking-widest text-gold"
              >
                Sign in
              </button>
            </div>
            <label className="block">
              <span className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-white/40">Email</span>
              <input
                data-testid="input-email-signin"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded border border-white/15 bg-black/30 px-3 py-2 text-sm text-white/90 outline-none focus:border-gold/60"
              />
            </label>
            <label className="block">
              <span className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-white/40">Password</span>
              <input
                data-testid="input-password-signin"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded border border-white/15 bg-black/30 px-3 py-2 text-sm text-white/90 outline-none focus:border-gold/60"
              />
            </label>
            <button
              data-testid="button-signin"
              type="submit"
              disabled={busy}
              className="w-full rounded border border-gold/40 bg-gold/10 px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-gold disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Sign in"}
            </button>
            {error && <p className="text-xs text-amber-200/80">{error}</p>}
            {identityState === "backend-unavailable" && (
              <p className="text-xs text-amber-200/60">Arkadia is temporarily unreachable.</p>
            )}
          </form>
        )}
      </Panel>
    </Page>
  );
}
