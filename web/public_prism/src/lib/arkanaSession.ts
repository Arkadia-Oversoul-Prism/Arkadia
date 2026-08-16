/**
 * Arkana Session Identity — shared conversational spine key.
 *
 * Canonical, interface-independent session identifier for the Oracle/Arkana
 * runtime. Oracle Chat, ReasoMate, and NovaNet all resolve the SAME
 * session_id for a given human so that conversation archival + Knowledge OS
 * retrieval describe one longitudinal conversation regardless of which
 * surface initiated the turn.
 *
 * Resolution order (human-owned, stable, contestable):
 *   1. Authenticated user uid  (strongest — identical across every surface)
 *   2. Sovereign token          (legacy Oracle Chat gate identity)
 *   3. Stable guest id          (localStorage, shared across surfaces)
 *
 * This is NOT a second memory system — it is only the thread key the backend
 * uses to scope Knowledge OS retrieval/archival. Memory itself lives in the
 * Knowledge OS.
 */

const GUEST_SESSION_KEY = 'arkadia_arkana_session';

function stableGuestId(): string {
  try {
    const existing = localStorage.getItem(GUEST_SESSION_KEY);
    if (existing) return existing;
    const id = `guest-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(GUEST_SESSION_KEY, id);
    return id;
  } catch {
    // localStorage unavailable (private mode / SSR) — derive an ephemeral id.
    return `guest-ephemeral-${Date.now().toString(36)}`;
  }
}

/**
 * Resolve the canonical Arkana session id for the current human.
 *
 * @param uid       authenticated user uid (from useAuth / useArkadiaAuth)
 * @param sovereignToken  legacy Oracle Chat sovereign token, if present
 * @returns a stable, interface-independent session id string
 */
export function arkanaSessionId(uid?: string | null, sovereignToken?: string | null): string {
  if (uid && uid.trim()) return `arkana-${uid.trim()}`;
  if (sovereignToken && sovereignToken.trim()) return `arkana-token-${sovereignToken.trim()}`;
  return stableGuestId();
}

/** Read-only guest id accessor (does not create one). */
export function getGuestSessionId(): string | null {
  try {
    return localStorage.getItem(GUEST_SESSION_KEY);
  } catch {
    return null;
  }
}
