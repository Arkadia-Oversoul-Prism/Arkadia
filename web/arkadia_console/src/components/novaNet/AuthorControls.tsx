/**
 * NovaNet public field — author-only Edit / Delete controls.
 *
 * The public field (`GET /api/transmissions`) is an open read; the mutation is
 * author-only and identity-derived on the backend (`api/transmissions.py`):
 * `PATCH /api/transmissions/{id}` and `DELETE /api/transmissions/{id}` resolve
 * the owner from the verified Firebase uid and return 401 for an anonymous
 * caller and 403 for a non-owner. This surface therefore renders the controls
 * **only** when the caller passes `isOwn` — the client does not decide
 * ownership, it mirrors the boundary the backend enforces, and a mismatch is
 * never offered a control that could only 403.
 *
 * Both paths are composed from the one endpoint registry (`lib/endpoints.ts`)
 * against the declared `/api/transmissions` collection; nothing here invents a
 * route (console directive §3.1). The path builder is a local helper, not a
 * registry entry, because `lib/endpoints.ts` is the shell workstream's file —
 * the registry member is referenced, never restated.
 */
import { useState } from "react";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { Transmission } from "../../lib/types";

/** `PATCH|DELETE /api/transmissions/{post_id}` derived from the registry. */
function transmissionPost(postId: string): string {
  return `${endpoints.transmissions}/${encodeURIComponent(postId)}`;
}

export function AuthorControls({
  transmission,
  isOwn,
  onChanged,
}: {
  transmission: Transmission;
  isOwn: boolean;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(transmission.content);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The backend is the authority: if this reader does not own the post, there
  // is no mutation to offer. Rendering the controls would be a decorative (and
  // inevitably 403-ing) action, which the console directive forbids.
  if (!isOwn) return null;

  async function save() {
    const content = draft.trim();
    if (!content) {
      setError("A transmission cannot be empty.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await apiRequest<{ transmission: Transmission }>(transmissionPost(transmission.id), {
        method: "PATCH",
        body: JSON.stringify({ content }),
      });
      setEditing(false);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The edit was not accepted.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await apiRequest<{ deleted: string }>(transmissionPost(transmission.id), { method: "DELETE" });
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The delete was not accepted.");
    } finally {
      setBusy(false);
    }
  }

  if (editing) {
    return (
      <div className="mt-2 flex flex-col gap-2" data-testid="novanet-author-edit">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          className="w-full rounded border border-line bg-ink/60 p-2 text-sm text-white/85"
          aria-label="Edit transmission"
        />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={save}
            disabled={busy}
            className="rounded border border-azure/60 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-azure disabled:opacity-40"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              setEditing(false);
              setDraft(transmission.content);
              setError(null);
            }}
            disabled={busy}
            className="rounded border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/60 disabled:opacity-40"
          >
            Cancel
          </button>
        </div>
        {error ? <p className="font-mono text-[10px] text-ember/80">{error}</p> : null}
      </div>
    );
  }

  return (
    <div className="mt-2 flex items-center gap-2" data-testid="novanet-author-controls">
      {confirmingDelete ? (
        <>
          <span className="font-mono text-[10px] uppercase tracking-widest text-white/40">
            Delete this transmission?
          </span>
          <button
            type="button"
            onClick={remove}
            disabled={busy}
            className="rounded border border-ember/60 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-ember disabled:opacity-40"
          >
            Confirm
          </button>
          <button
            type="button"
            onClick={() => setConfirmingDelete(false)}
            disabled={busy}
            className="rounded border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/60 disabled:opacity-40"
          >
            Cancel
          </button>
        </>
      ) : (
        <>
          <button
            type="button"
            onClick={() => {
              setDraft(transmission.content);
              setEditing(true);
            }}
            className="rounded border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/60"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="rounded border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/60"
          >
            Delete
          </button>
        </>
      )}
      {error ? <p className="font-mono text-[10px] text-ember/80">{error}</p> : null}
    </div>
  );
}
