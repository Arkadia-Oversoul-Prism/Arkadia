# K4 — Response Provenance

**Status:** COMPLETE — backfilled record
**Date of implementation:** 2026-09-30
**Date of this record:** 2026-10-02
**Role:** Implementation Steward (record) / Weaver pass (reconciliation)
**Commits:** merged via **PR #153** → `4a9281b` (base `002b189`)

> **This document was written after the fact.** K4 shipped on `main` via PR #153, but the
> checkpoint record required by `MISSION.md` §Deliverables was never created, and
> `.bootstrap/01_STATE.md` / `MISSION.md` / `NEXT_AGENT.md` still reported K4 as
> "READY TO BEGIN" / "NEXT". This file closes that bookkeeping gap. **No implementation
> code was changed by this pass.**

---

## Objective

Make Oracle responses citable. `knowledge/context_engine.assemble_context()` already
returns note UUIDs alongside the text chunks it selects, but the Oracle response discarded
them — the reader received a confident answer with no way to tell which archived knowledge
produced it. K4 surfaces those identities as a `sources` array so answers become citable.

Exit condition (from `docs/recon/KNOWLEDGE_OS_EVOLUTION.md` §K4): *"Oracle response
includes a `sources` list; frontend shows 'Based on: ...' citations."*

## Change Made

| File | Change |
|---|---|
| `api/oracle_spine.py` | New `build_sources(context_package, limit=6)`; the spine stashes the assembled package in `meta["_context_package"]` |
| `api/main.py` | Oracle response shape gains `"sources": build_sources(memory_meta.get("_context_package"))` |
| `web/public_prism/src/components/ArkanaCommune.tsx` | `SourceRef[]` on the message model; renders "Based on" citations |
| `tests/test_k4_response_provenance.py` | 6 tests pinning the provenance invariant |

**Seam discipline.** The sources are derived inside the existing spine from the context
package that was actually injected into the provider. No second retrieval path, no new
query, no graph call — provenance is a *view* of the retrieval that already happened.

**Provenance invariant** (documented in the `build_sources` docstring and pinned by tests):

- A source is emitted **only if its note was part of the retrieved context**. The Oracle
  cannot cite a note it did not retrieve.
- An empty or absent package yields **no** citations — citations are evidence of
  retrieval, never decoration.
- Entries carry the note's stable UUID, so a citation survives rename and is inspectable
  against the Knowledge OS graph.
- `_context_package` stays internal to the `meta` dict; it is not serialised to the client.

**Response shape change is additive** — `api/main.py` is at its 2600-line budget and was
kept compact (`api/main.py` remains untouched by this reconciliation pass).

## Verification

Re-measured 2026-10-02 on `main` @ `64cbe74` (clean worktree `/tmp/wt-k4`):

- `python -m pytest tests/test_k4_response_provenance.py -q` → **6 passed**
  (`test_sources_cite_the_note_actually_retrieved`,
  `test_sources_are_never_fabricated_without_retrieval`,
  `test_sources_tolerate_absent_or_empty_package`,
  `test_sources_deduplicate_and_respect_limit`,
  `test_source_excerpt_is_collapsed_and_bounded`,
  `test_context_package_stays_internal_to_the_meta_dict`)
- `python -m pytest tests/architecture -q` → **11 passed** (unchanged)
- Seams re-derived from source, not from prose:
  `api/oracle_spine.py:92 build_sources`; `api/oracle_spine.py:74` stashes the package under
  the internal `_context_package` key of `meta`;
  `api/main.py:1280` emits `sources` via `build_sources(...)`;
  `ArkanaCommune.tsx:972` conditional render of `msg.sources`.

## Known gaps (recorded, not fixed — outside this checkpoint's scope)

1. **`MISSION.md` §Deliverables listed `docs/checkpoints/K4_response_provenance.md` and a
   `docs/phase1/CONTINUATION_LEDGER.md` session record for the K4 session; neither was
   produced.** This pass supplies the checkpoint record. The ledger entry is appended by
   the same pass (session-end record).
2. **`_context_package` reaches the response through `memory_meta`.** That is the existing
   diagnostics channel, so no new plumbing was introduced, but it means provenance depends
   on the spine populating `meta` on the same code path that builds the reply. A future
   refactor that separates reply construction from diagnostics would silently empty
   `sources`; `test_context_package_stays_internal_to_the_meta_dict` is the guard.
3. **K4 is the last checkpoint named by `docs/recon/KNOWLEDGE_OS_EVOLUTION.md`.** Workstream
   K has no K6. The next workstream is not defined by the recon doc — see the checkpoint
   doc's "Next" section below and `.bootstrap/01_STATE.md`.

## Architectural Boundaries

- No new dependency; no duplicate retrieval engine; no second graph implementation.
- `api/oracle_spine.py` remains the single shared spine (Oracle Chat, ReasoMate, NovaNet).
- Ontology frozen — no new node or relationship types were introduced.
- No governance, ADR, or ROADMAP edit. No authority or mutation path added.

## Next

**Workstream K is complete.** K1, K2, K3, K4 and K5 are all shipped and now all carry
checkpoint records. There is no K6 in the design doc.

The named successor is **CS2 — Reusable conversational UI** (deferred, not discarded;
recorded in `NEXT_AGENT.md`). It is a *product* workstream: extract the proven Oracle Chat
capabilities into a reusable conversational component boundary so all surfaces inherit one
canonical chat shell over the same spine. Do **not** rebuild the Oracle UI.

CS2 is a scope expansion relative to Workstream K. Selecting it is a sovereign decision —
this record names it as the recommended next bounded task but does not begin it.

Standing non-K candidates, all requiring a sovereign ruling or a separate bounded
workstream (see `PARKING_LOT.md`):

- `weaver.autonomy` module/package shadowing — **awaiting a sovereign ruling** on which
  object is canonical (an authority-model question).
- Spiral Grove registry declaration-order vs topological-order contract — **awaiting a
  ruling** on which contract the registry means.
- Baseline test debt — separately classified, must not be folded into an unrelated gate.

## Standing reconciliation note

`.bootstrap/01_STATE.md`, `MISSION.md` and `NEXT_AGENT.md` carried a stale "K4 — READY TO
BEGIN / NEXT" marker until this pass. All three are corrected here. K4's status was
re-derived from live evidence — the merged implementation (PR #153 → `4a9281b`), the
present seams, and the passing test file — before the marker was changed, so the correction
does not simply move the staleness one checkpoint forward.
