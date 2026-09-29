# GATE-01 — Canonical Authorship: Implementation Record

Status: IMPLEMENTED
Base SHA: 6038989dc57e871331107b7dde9fc3d749d4d4aa
Branch: gate-01-canonical-authorship

## Objective

Establish what object is authoritative for every durable operational fact, and
prove the system can name a fact's canonical origin — or leave it UNKNOWN.

## Baseline Debt Declaration (captured before any change)

- Frozen base: `6038989dc57e871331107b7dde9fc3d749d4d4aa` (main, PR #90 merge).
- Full suite: 54 failed / 804 passed / 12 skipped.
- Failure fingerprint (sha256 of sorted failing node IDs):
  `394be25e3093f7763b282a4b0fa9f441964c86d2a2a4a4d3958d9e0f5778435`.
- Architecture suite: 2 pre-existing failures
  (`test_api_main_line_count_within_budget`, `test_no_layer_inversions`).
- Working tree clean at declaration time.

## Reconnaissance finding

No canonical SOURCE or CAPTURE primitive existed. `knowledge.pipeline.ingest`
accepted a free-text `source_provider` label and wrote a note directly; raw
input and interpretation were not separable, and authorship was not recorded.
The existing Knowledge OS (vault + pipeline + timeline) is the correct
canonical home, so the capability was **extended**, not duplicated (LAW-07,
LAW-09).

## Canonical source decision

The canonical record for a durable fact remains the Knowledge OS `notes` row.
GATE-01 adds the boundary that produces it:

    SOURCE → CAPTURE → CANONICAL RECORD → AUTHORSHIP → PROVENANCE

- `capture_sources` — canonical origin identity. Fingerprinted by
  (kind, ref, title); re-registering the same origin returns the existing row.
- `capture_records` — one immutable artifact per capture. `source_id` is
  NOT NULL, so SOURCE → CAPTURE cannot be skipped. `note_id` binds the capture
  to the canonical record it produced. `raw_checksum` is sha256 of the raw
  content, so identity is content-addressed.
- `knowledge/capture.py` — the boundary. `register_source`, `capture`,
  `bind_capture_to_note`, `provenance_for_capture`, `provenance_for_note`,
  `capture_and_ingest`.

## Authority model

- Authorship is **declared**, never inferred from the source, the captor, or
  the content. An undeclared author is stored NULL and reported as UNKNOWN.
- An actor declared with kind `unknown` keeps the actor id but records the
  nature as UNKNOWN rather than assuming `human`.
- Capture ≠ authorship: `captured_by` and `authored_by` are separate fields.
- A note with no capture record has UNKNOWN provenance. The system does not
  invent an origin for pre-existing notes.
- No authorization or execution semantics are introduced here. Those are later
  gates (LAW-10).

## Mutation path

`capture_and_ingest` delegates the write to `knowledge.pipeline.ingest` — the
single existing path. It introduces no second write path.

## Protected surfaces / adjacent defect

The capture boundary required importing `knowledge.pipeline` early, which
surfaced a pre-existing latent defect: `pipeline.py`, `context_engine.py`, and
`search.py` each imported `embed_text` by name at load time, freezing the
binding so later patching of `knowledge.embeddings.embed_text` had no effect.
`tests/test_oracle_spine.py` worked around this by patching every binding site.

Minimal repair (behavior-preserving; same public API): the three modules now
reference the `embeddings` module at call time (`from knowledge import
embeddings as emb` → `emb.embed_text(...)`), and the oracle test patches the
single module. This removes an import-order hazard and is required for the
suite to remain order-independent.

## Tests

- `tests/test_gate_01_canonical_authorship.py` — 18 tests, all passing, against
  the real Knowledge OS code paths (no mocks).
- Full suite: 54 failed / **822** passed / 12 skipped. The failing set is
  **identical** to the baseline fingerprint — no new failures, +18 passing.
- Architecture suite: 2 failures, both pre-existing and unrelated
  (`api/nodes.py` layer inversions; `api/main.py` line budget).

## Out-of-scope observed

- `api/main.py` exceeds its 2600-line budget by 7 lines (pre-existing).
- `api/nodes.py` has 2 unregistered layer inversions (pre-existing).
- Pre-existing tests write generated vault markdown into the repository vault
  root when run; cleaned up after verification, not addressed here.

## Verdict

IMPLEMENTED. Not yet independently verified by a second party; no autonomous
advance to GATE-02.
