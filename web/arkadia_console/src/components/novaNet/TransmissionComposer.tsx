/**
 * NovaNet public field — transmit composer (create a transmission).
 *
 * The archived Prism field (`archive/.../pages/SocialFieldVerified.tsx`) opened
 * with a composer that `POST`ed a new public transmission, gated on the verified
 * identity (`canTransmit = isAuthenticated && profile`). The console reconciled
 * the field's *read* side (engagement readings, author controls, live react /
 * comment writes) but never offered the create path, so an authenticated reader
 * could reply to a post yet not originate one.
 *
 * The contract is live and verified on `api/transmissions.py`:
 *
 *   * ``POST /api/transmissions`` — body ``{content, author}``; blank content is
 *     refused with 400, and the response is ``{"transmission": {...}}``. The
 *     author identity is projected from the verified profile server-side
 *     (`_author_block`), so the client does not author the identity it sends —
 *     it mirrors the archived shape and lets the backend resolve the owner.
 *
 * The path is composed from the one endpoint registry (`lib/endpoints.ts`)
 * against the declared `/api/transmissions` collection; nothing here invents a
 * route (console directive §3.1). The composer renders **only** for an
 * authenticated caller — an anonymous reader is told to sign in, mirroring the
 * archived gate rather than offering a control the archived product withheld.
 */
import { useState } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { NodeProfile, Transmission } from "../../lib/types";

/** `POST /api/transmissions` — the registry's own collection path. */
function transmitPath(): string {
  return endpoints.transmissions;
}

/** A refusal is reported honestly; an auth failure is named rather than shown as a fault. */
function refusalFor(caught: unknown, fallback: string): string {
  const error = caught instanceof ApiError ? caught : null;
  if (error?.kind === "AUTH_REQUIRED") return "Sign in to transmit to the public field.";
  if (error?.kind === "BAD_REQUEST") return error.message;
  return caught instanceof Error ? caught.message : fallback;
}

export function TransmissionComposer({
  isAuthenticated,
  profile,
  onCreated,
}: {
  isAuthenticated: boolean;
  profile: NodeProfile | null;
  onCreated: (transmission: Transmission) => void;
}) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isAuthenticated) {
    return (
      <p className="mb-3 font-mono text-[11px] text-white/40" data-testid="novanet-transmit-signin">
        Sign in to transmit to the public field. The field remains readable without an identity.
      </p>
    );
  }

  async function submit() {
    const content = text.trim();
    if (!content || busy) return;
    setBusy(true);
    setError(null);
    try {
      const response = await apiRequest<{ transmission: Transmission }>(transmitPath(), {
        method: "POST",
        body: JSON.stringify({
          content,
          author: {
            name: profile?.display_name || "Node",
            avatar: profile?.role_sigil || "◈",
            role: profile?.role || "Node",
          },
        }),
      });
      onCreated(response.transmission);
      setText("");
    } catch (caught) {
      setError(refusalFor(caught, "The transmission was not accepted."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-3 flex flex-col gap-2 rounded border border-line bg-ink/40 p-3" data-testid="novanet-transmit-composer">
      <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
        Public transmission · visible on the field
      </p>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) void submit();
        }}
        placeholder="Transmit something to the public field…"
        rows={3}
        aria-label="New public transmission"
        className="w-full resize-none rounded border border-line bg-ink/60 p-2 text-sm text-white/85"
      />
      <div className="flex items-center justify-end gap-2">
        {error ? (
          <p role="alert" className="mr-auto font-mono text-[10px] text-ember/80" data-testid="novanet-transmit-error">
            {error}
          </p>
        ) : null}
        <button
          type="button"
          data-testid="novanet-transmit-submit"
          onClick={submit}
          disabled={busy || !text.trim()}
          className="rounded border border-azure/60 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-azure disabled:opacity-40"
        >
          {busy ? "Transmitting…" : "Transmit"}
        </button>
      </div>
    </div>
  );
}
