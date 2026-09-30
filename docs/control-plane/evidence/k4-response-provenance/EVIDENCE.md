# K4 — Response Provenance

**Workstream:** K (Knowledge OS Integration) · **Checkpoint:** K4
**Base main:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Status:** IMPLEMENTED (backend + frontend wiring complete and locally proven;
frontend typecheck environment-blocked)
**Authority:** no merge, no push to `main`, no force-push. Human-only merge.

## Objective

Arkana must be able to show *which* retrieved Knowledge OS notes informed a reply.
Before this pass the Oracle response carried `rag_refs` / `rag_hits` counts but no
inspectable provenance, so a reply could not be audited back to its sources.

## The invariant

> A source may be cited **only** if its note was actually part of the context package
> that was injected into the provider for that turn.

Citations are evidence of retrieval, never decoration. Consequences that are tested:

1. An empty/absent context package yields **no** citations (never a fabricated one).
2. Every citation resolves to a note present in the injected package.
3. The cited excerpt is a whitespace-normalised projection of text that was actually
   injected into the provider block.
4. A note reachable both directly and via graph expansion is cited once.
5. The citation list is bounded (`limit=6`) and each entry carries the note's stable
   UUID, so a citation survives a rename and is inspectable against the Knowledge OS graph.

## Changes

| File | Change |
|---|---|
| `api/oracle_spine.py` | `retrieve_arkana_context` retains the retrieved `_context_package` in its meta dict (underscore-prefixed: internal diagnostic, never serialised). New `build_sources(package, limit=6)` + `_excerpt()` derive the citable list. |
| `api/main.py` | +2 lines at the `/api/commune/resonance` return seam: `"sources": build_sources(memory_meta.get("_context_package"))`. |
| `web/public_prism/src/components/ArkanaCommune.tsx` | `SourceRef` type; `Message.sources`; fetch captures `data.sources`; "Based on" citation block renders between the reply and the separator. |
| `tests/test_k4_response_provenance.py` | New — 6 tests. |

**Budget:** `api/main.py` = **2521 / 2600** lines (was 2519; +2). `python -m py_compile api/main.py` passes.

**Design note:** the K4 logic lives in `api/oracle_spine.py`, not `api/main.py`, so the
boot surface grows by two lines only.

## Tests

| Suite | Result |
|---|---|
| `tests/test_k4_response_provenance.py` | **6 passed** |
| `tests/test_oracle_spine.py` (regression) | 7 passed |
| `tests/architecture` | **11 passed** |
| `tests/` (full) | 1045 passed / 20 failed / 13 skipped / 2 collection errors |

Embeddings are stubbed with deterministic local vectors (same technique as
`tests/test_oracle_spine.py`) because the Gemini embedding API is unavailable offline.
This is strictly necessary to exercise the **real** retrieval plumbing — chunk storage,
thread filtering, scoring and `format_context_for_provider` all run unmodified.

## Regression boundary

The full-suite failure fingerprint was captured on **clean `main`** (work stashed) and
diffed against the with-K4 run. **Fingerprint identical: 20 failures, same test IDs.**
The 2 collection errors are pre-existing (`test_autonomy.py`, `test_render_codex.py`).

Baseline drift recorded, not silently accepted: the contract's stated baseline
(`6038989`, 804/54/12/2, architecture 9/10) is **stale**. Live `main` at `002b189`
measures **1039 passed / 20 failed / 13 skipped / 2 errors, architecture 11/11**.
K4 accounts for exactly the +6 passed delta. No baseline debt was fixed in this pass.

CP10 mutation boundary pre-checked against the changed path set: **PASS**.

## Remaining uncertainty

- **Frontend typecheck not run.** `web/public_prism/node_modules` is absent and there is
  no npm registry access in this environment, so `pnpm build` / `tsc` is
  environment-blocked. The `.tsx` change is inspection-verified only: `SourceRef` is
  consistent with `build_sources`' emitted keys, and the render guard is
  `msg.sources && msg.sources.length > 0`.
- No runtime/browser evidence of the rendered citation block. Per the standing AEAS
  boundary, this pass does **not** claim production parity.

## Next bounded task

Adjudicate the AGENTS.md encoding-repair PR queue (#143/#147/#150/#151/#152).
