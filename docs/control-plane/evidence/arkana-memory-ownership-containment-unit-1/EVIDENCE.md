# Unit 1 — Arkana memory ownership containment

**Status:** IMPLEMENTED, tests pass, NOT COMMITTED, NOT PUSHED, NO PR.
**Authorization:** Unit 1 only, bounded as specified by the user. No blanket
authorization; no other unit is implemented or inferred.
**Base revision:** `main` @ `776766b9` (feat(lab): Engineering Lab repository/change reading #592).
**Date:** 2026-10-30.

---

## 1. What was authorized, and what was not

Authorized: **Unit 1 — Arkana memory ownership containment**, explicitly bounded.

Not authorized, and deliberately not done:

* any product/UX roadmap change (separate from this security finding by user decision);
* the public-codex issue (materially different exposure, separate finding);
* `api/lab_routes.py` or any other authority surface;
* deployment, merge, production acceptance, or a PR.

## 2. The defect (measured, not inferred)

`knowledge/context_engine.py::assemble_context` assembles the Oracle/Arkana memory
package from four channels. Only one applied an ownership filter, and that filter was
itself permissive: it ran **only when a `user_id` was bound**, so an anonymous caller
retrieved *unscoped*. Measured on the pre-repair tree with one archived turn owned by
`uid-victim-A`:

| channel | anonymous | another user | owner |
|---|---|---|---|
| notes (chunk filter) | **LEAKED** | scoped | reached |
| graph expansion | unfiltered (`traverse` called with no owner) | unfiltered | reached |
| timeline | **LEAKED** (7 rows, no owner clause) | **LEAKED** (7 rows) | reached |
| project context | **LEAKED** (caller-supplied `project_id` resolved without an owner check) | **LEAKED** | reached |

Reproduction used a throwaway DB via `ARKADIA_DB_PATH` and a deterministic embedding
stub; it does not touch the repository's real store. All probe artifacts were deleted
and the generated `vault/` notes removed (they are gitignored; only tracked scaffolding
remains).

## 3. The change

`knowledge/context_engine.py`

* New `_owner_scope_sql(user_id, thread_id)` / `retrievable_note_ids(...)` state the
  boundary **once**; three things are reachable and nothing else: the seeded public
  corpus (NULL-owner notes that are *not* conversation material), the caller's own
  notes, and — for a caller with no owner — conversation notes in an ownerless thread
  (which is what preserves anonymous session continuity).
* The chunk filter is now applied to **both** branches; it is no longer gated on a
  bound `user_id`.
* Graph expansion passes `user_id` to `traverse` and re-applies the boundary to each
  hop, so a graph edge cannot re-expose a note the direct filter excluded.
* Project context resolves `project_id` through an owner clause, and its recent-note
  titles are owner-scoped.
* The timeline channel reuses the canonical fail-closed
  `knowledge.timeline._timeline_owner_clause` instead of restating the boundary.

`api/oracle_spine.py`

* `archive_oracle_turn` keeps archiving an ownerless turn **into its own thread**
  rather than refusing it. An earlier draft refused to persist ownerless turns; that
  removed a tested product feature (anonymous session continuity) and was rejected —
  containment scopes the turn, it does not delete the feature.

## 4. Acceptance evidence

`tests/test_arkana_memory_ownership_containment.py` — **10 passed**. One test per
exposed channel, plus owner-reachability (the legitimate workflow must survive), plus
anonymous continuity, plus a **negative control** that drives the pre-repair predicate
and asserts the canary *is* reachable through it.

Negative control bites: reverting `_owner_scope_sql` to the permissive shape
(`user_id = ? OR user_id IS NULL`, anonymous `1 = 1`) reddens **4** tests
(`test_anonymous_retrieval_does_not_surface_an_owned_turn`,
`test_anonymous_turn_is_not_reachable_from_another_session`,
`test_guessed_session_id_does_not_disclose_an_owned_turn`,
`test_negative_control_detects_a_permissive_scope`). The file was restored
byte-identically afterwards.

Guessed-session-id case: `session_id` is client-supplied, so addressing a thread is not
authority over it. Measured with an anonymous caller replaying the victim's session id:
`notes_retrieved: 0`, secret absent.

Regression: full suite on the changed tree vs a detached `main` @ `776766b9` worktree in
the same environment — failing/error node sets **identical**, `sha256
e40434527aacfe85197142c6e879c360d8c2157d187f7d853be090592c24327f` (26 nodes) on both
sides. `+10 passed` is exactly the new test file.

## 5. Recorded, NOT repaired — outside this unit's boundary

Sibling read paths still treat `user_id IS NULL` as public and are not
conversation-aware: `knowledge/vault.py::_note_owner_clause`,
`knowledge/search.py::_notes_owner_sql`, `knowledge/graph.py::accessible_note_ids`,
and `knowledge/enrichment.py` (predecessor link, no owner predicate).

Measured severity, stated precisely rather than as an alarm:

* These paths do **not** expose an *authenticated* victim's note to an anonymous
  caller — that is scoped correctly by `user_id` (measured: `vault.get_note(anon)` →
  `False`, `list_notes(anon)` → `[]`, `accessible_note_ids(anon)` → `set()`,
  `fulltext_search(anon)` → `0` hits against an owned note).
* They **do** expose an *anonymous visitor's own* turn to other anonymous callers
  (measured: a NULL-owner `conversation` note is returned by `get_note`/`list_notes`/
  `fulltext_search` for an anonymous caller).

That is a **distinct, pre-existing** exposure with a different blast radius from the
one Unit 1 repairs. Repairing it edits three shared retrieval modules and their
contract tests, which is a wider boundary than "Arkana memory ownership containment".
It is proposed here, not executed. Anonymous inputs also reach `note_type='conversation'`
via `POST /api/knowledge/ingest` (client-supplied `note_type`) — also recorded, not
repaired.

## 6. Next action

Awaiting the user's decision on committing/pushing Unit 1. Nothing is committed or
pushed. No further unit is implemented.
