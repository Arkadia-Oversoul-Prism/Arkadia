/**
 * Arkana thread-history contract (feature-local).
 *
 * These interfaces are the shape `api/commune_threads.py` actually returns,
 * measured against the handler with a composed router (not inferred from the
 * archive UI). `_public_thread()` deliberately omits `user_id`, so ownership is
 * enforced server-side and never round-trips to the client.
 *
 * The paths live in the page module as expressions over the declared collection
 * `endpoints.arkanaThreads`, so the shared registry stays the single source of
 * declared endpoints. Workstream 1 owns `lib/endpoints.ts`; a request for a
 * first-class parameterised helper is recorded in this slice's evidence.
 */

/** `GET /api/commune/threads` element — the public thread projection. */
export interface ArkanaThread {
  id: number | null;
  uuid: string;
  title: string | null;
  project_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

/** `GET /api/commune/threads` response envelope. */
export interface ArkanaThreadList {
  threads: ArkanaThread[];
}

/** `GET /api/commune/threads/{uuid}` response envelope. */
export interface ArkanaThreadDetail {
  thread: ArkanaThread;
}

/**
 * The handler emits exactly two roles. `arkana` is the assistant turn; it is not
 * named `assistant` on this contract, so the UI must not assume the resonance
 * endpoint's vocabulary.
 */
export type ArkanaThreadRole = "user" | "arkana";

export interface ArkanaThreadMessage {
  role: ArkanaThreadRole;
  content: string;
  /** SQLite's `created_at` default format (`YYYY-MM-DD HH:MM:SS`), not ISO-8601. */
  created_at: string | null;
}

/** `GET /api/commune/threads/{uuid}/messages` response envelope. */
export interface ArkanaThreadMessages {
  messages: ArkanaThreadMessage[];
}
