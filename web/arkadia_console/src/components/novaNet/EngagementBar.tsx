/**
 * NovaNet public field — declared engagement readings (reactions, comments,
 * reposts).
 *
 * The public transmissions feed (`GET /api/transmissions`,
 * `api/transmissions.py`) carries four reaction counters (`heart` / `fire` /
 * `star` / `mind`), a `reposts` count and a `comments` array on every post.
 * The console rendered none of them, so engagement a reader could already fetch
 * was invisible — the archived Prism field card showed exactly these readings.
 *
 * Display-only and server-authoritative. It performs no mutation and derives
 * nothing: the reaction vocabulary is the backend's own seed keys in their
 * declared order, and a count the server did not return reads the server's own
 * `0` rather than an invented value. `reposts` has no verified write handler on
 * the router, so it is shown as a reading with no control; the reaction and
 * comment write paths (both live on the router) are a separate bounded slice
 * that is not wired here until its contract is proven.
 */
import type { Transmission } from "../../lib/types";

/** The backend's seeded reaction keys (`api/transmissions.py`), in its order. */
export const REACTION_TYPES = ["heart", "fire", "star", "mind"] as const;
export type ReactionType = (typeof REACTION_TYPES)[number];

/** The glyph the archived Prism field card used for each declared reaction. */
const REACTION_GLYPH: Record<ReactionType, string> = {
  heart: "💜",
  fire: "🔥",
  star: "✨",
  mind: "🧠",
};

export function EngagementBar({ transmission }: { transmission: Transmission }) {
  const reactions = transmission.reactions;
  const comments = transmission.comments;
  const commentCount = Array.isArray(comments) ? comments.length : 0;
  const reposts = typeof transmission.reposts === "number" ? transmission.reposts : 0;

  return (
    <div
      className="mt-2 flex flex-wrap items-center gap-3 font-mono text-[11px] text-white/50"
      data-testid="novanet-engagement"
    >
      <ul className="flex flex-wrap items-center gap-3" data-testid="novanet-reactions">
        {REACTION_TYPES.map((type) => (
          <li key={type} data-testid={`novanet-reaction-${type}`} className="flex items-center gap-1">
            <span aria-hidden="true">{REACTION_GLYPH[type]}</span>
            <span aria-label={`${type} reactions`}>{reactions?.[type] ?? 0}</span>
          </li>
        ))}
      </ul>
      <span data-testid="novanet-comments" className="flex items-center gap-1">
        <span aria-hidden="true">💬</span>
        <span aria-label="comments">{commentCount}</span>
      </span>
      <span data-testid="novanet-reposts" className="flex items-center gap-1">
        <span aria-hidden="true">⟳</span>
        <span aria-label="reposts">{reposts}</span>
      </span>
    </div>
  );
}
