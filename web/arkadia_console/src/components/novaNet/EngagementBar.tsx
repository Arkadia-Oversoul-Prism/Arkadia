/**
 * NovaNet public field — interactive engagement bar (reactions + comments).
 *
 * The public transmissions feed (`GET /api/transmissions`, `api/transmissions.py`)
 * carries four reaction counters (`heart` / `fire` / `star` / `mind`) and a
 * `comments` array on every post, and the archived Prism field card made exactly
 * these two readings **interactive**: each reaction glyph was a button that
 * `POST`ed the reaction, and the comment count toggled a thread with a composer.
 * The console rendered the readings read-only, so the interaction was missing
 * even though both write handlers are live and verified.
 *
 * Two handlers are wired, and only these two — each a declared route on
 * `api/transmissions.py`:
 *
 *   * ``POST /api/transmissions/{id}/react``   — body ``{type}``; the server
 *     refuses any key outside ``{"heart","fire","star","mind"}`` with 400 and
 *     answers ``{"reactions": {...}}``.
 *   * ``POST /api/transmissions/{id}/comment`` — body ``{content}``; the server
 *     refuses blank content with 400 and answers ``{"comment": {...}}``.
 *
 * Both paths are composed from the one endpoint registry (`lib/endpoints.ts`)
 * against the declared `/api/transmissions` collection; nothing here invents a
 * route (console directive §3.1). The path builders are local helpers, not
 * registry entries, because `lib/endpoints.ts` is the shell workstream's file —
 * the registry member is referenced, never restated.
 *
 * `reposts` has **no** verified write handler on the router (a grep of
 * `api/transmissions.py` shows no repost route), so it is shown as a reading with
 * no control — an unverified capture path is not invented. No value is invented
 * either: a count the server did not return reads the server's own `0`.
 */
import { useState } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { Transmission } from "../../lib/types";

/** The backend's seeded reaction keys (`api/transmissions.py`), in its order. */
export const REACTION_TYPES = ["heart", "fire", "star", "mind"] as const;
export type ReactionType = (typeof REACTION_TYPES)[number];

/** The glyph the archived Prism field card used for each declared reaction. */
export const REACTION_GLYPH: Record<ReactionType, string> = {
  heart: "💜",
  fire: "🔥",
  star: "✨",
  mind: "🧠",
};

/** A comment record as the feed serves it (`_author_block` + timestamp). */
interface TransmissionComment {
  id?: string;
  content?: string;
  author?: { name?: string; avatar?: string; role?: string };
  timestamp?: number;
}

/** `POST /api/transmissions/{post_id}/react` derived from the registry. */
function reactPath(postId: string): string {
  return `${endpoints.transmissions}/${encodeURIComponent(postId)}/react`;
}

/** `POST /api/transmissions/{post_id}/comment` derived from the registry. */
function commentPath(postId: string): string {
  return `${endpoints.transmissions}/${encodeURIComponent(postId)}/comment`;
}

/** A refusal is reported honestly; a gone post is named rather than shown as a generic fault. */
function refusalFor(caught: unknown, fallback: string): string {
  const error = caught instanceof ApiError ? caught : null;
  if (error?.kind === "NOT_FOUND") return "This transmission no longer exists.";
  return caught instanceof Error ? caught.message : fallback;
}

export function EngagementBar({
  transmission,
  onChanged,
}: {
  transmission: Transmission;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [threadOpen, setThreadOpen] = useState(false);
  const [draft, setDraft] = useState("");

  const reactions = transmission.reactions;
  const comments = Array.isArray(transmission.comments)
    ? (transmission.comments as TransmissionComment[])
    : [];
  const reposts = typeof transmission.reposts === "number" ? transmission.reposts : 0;

  async function react(type: ReactionType) {
    setBusy(`react:${type}`);
    setError(null);
    try {
      await apiRequest<{ reactions: Record<string, number> }>(reactPath(transmission.id), {
        method: "POST",
        body: JSON.stringify({ type }),
      });
      onChanged();
    } catch (caught) {
      setError(refusalFor(caught, "The reaction was not accepted."));
    } finally {
      setBusy(null);
    }
  }

  async function submitComment() {
    const content = draft.trim();
    if (!content) return;
    setBusy("comment");
    setError(null);
    try {
      await apiRequest<{ comment: TransmissionComment }>(commentPath(transmission.id), {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      setDraft("");
      onChanged();
    } catch (caught) {
      setError(refusalFor(caught, "The comment was not accepted."));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mt-2" data-testid="novanet-engagement">
      <div className="flex flex-wrap items-center gap-3 font-mono text-[11px] text-white/50">
        <ul className="flex flex-wrap items-center gap-3" data-testid="novanet-reactions">
          {REACTION_TYPES.map((type) => (
            <li key={type}>
              <button
                type="button"
                data-testid={`novanet-react-${type}`}
                aria-label={`React ${type}`}
                disabled={busy !== null}
                onClick={() => react(type)}
                className="flex items-center gap-1 rounded border border-line px-2 py-1 uppercase tracking-widest text-white/55 disabled:opacity-40"
              >
                <span aria-hidden="true">{REACTION_GLYPH[type]}</span>
                <span data-testid={`novanet-reaction-${type}`}>{reactions?.[type] ?? 0}</span>
              </button>
            </li>
          ))}
        </ul>
        <button
          type="button"
          data-testid="novanet-comments-toggle"
          aria-expanded={threadOpen}
          onClick={() => setThreadOpen((open) => !open)}
          className="flex items-center gap-1 rounded border border-line px-2 py-1 uppercase tracking-widest text-white/55"
        >
          <span aria-hidden="true">💬</span>
          <span aria-label="comments">{comments.length}</span>
        </button>
        <span
          data-testid="novanet-reposts"
          className="flex items-center gap-1"
          title="Reposts are a reading only — no verified write handler"
        >
          <span aria-hidden="true">⟳</span>
          <span aria-label="reposts">{reposts}</span>
        </span>
      </div>

      {threadOpen && (
        <div className="mt-2 flex flex-col gap-2" data-testid="novanet-comments">
          {comments.length === 0 ? (
            <p className="text-xs text-white/40">No replies on this transmission yet.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {comments.map((comment, index) => (
                <li key={comment.id ?? index} className="flex gap-2">
                  <span aria-hidden="true" className="text-azure">
                    {comment.author?.avatar ?? "◈"}
                  </span>
                  <p className="text-xs text-white/70">
                    <span className="text-white/50">{comment.author?.name ?? "Node"}</span> {comment.content}
                  </p>
                </li>
              ))}
            </ul>
          )}
          <div className="flex items-center gap-2">
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void submitComment();
              }}
              placeholder="Reply…"
              aria-label="Reply to this transmission"
              className="flex-1 rounded border border-line bg-ink/60 px-2 py-1 text-xs text-white/80"
            />
            <button
              type="button"
              data-testid="novanet-comment-send"
              onClick={submitComment}
              disabled={busy !== null || !draft.trim()}
              className="rounded border border-azure/60 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-azure disabled:opacity-40"
            >
              Send
            </button>
          </div>
        </div>
      )}

      {error ? (
        <p role="alert" className="mt-1 font-mono text-[10px] text-ember/80" data-testid="novanet-engagement-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}
