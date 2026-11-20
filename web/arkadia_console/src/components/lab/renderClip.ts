/**
 * Bounded-view clipping that discloses its own truncation.
 *
 * The Lab's convention is that a bounded render states its bound: the repository
 * surface says "Showing the first N entries; the observation is capped at M", and
 * the bounded-test surface appends "… truncated in this view; the server record is
 * authoritative". A bare `slice` breaks that convention silently — the reader sees
 * a complete-looking record that is actually a prefix.
 *
 * This is the one place that rule lives, so a surface cannot reintroduce a silent
 * cap by writing its own `slice`. `clipForDisplay` returns the text unchanged when
 * it fits, and appends the disclosure only when it does not.
 */

export const VIEW_CLIP_NOTICE = "… truncated in this view; the server record is authoritative";

/** Longest prefix of `value` rendered before the disclosure is appended. */
export const OBSERVATION_CLIP_LIMIT = 4000;

export function clipForDisplay(value: string, limit: number = OBSERVATION_CLIP_LIMIT): string {
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}\n${VIEW_CLIP_NOTICE}`;
}
