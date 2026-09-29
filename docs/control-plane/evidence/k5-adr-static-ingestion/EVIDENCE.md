# K5 — Static Ingestion · ADR corpus coverage gap · Evidence

Gate: **Workstream K — Checkpoint K5 (Static Ingestion)**
Branch: `gate-k/k5-adr-static-ingestion`
Base after rebase: `main` @ `2d62a21`
Status: **IMPLEMENTED** — bounded, evidence-backed. Human review + merge remain mandatory.

---

## 1. The gap

K5 explicitly names the vault notes, **ADRs**, open loops, and structured markdown in `docs/`.

Before this change, `knowledge/static_ingestion.py::_SOURCES` declared five roots: `static/`, `docs/*.md`, `docs/collective/`, `docs/creative/`, and `vault/`. `docs/adr/` was outside every glob.

The six architecture decision records were therefore never seeded into the Knowledge OS.

## 2. Bounded change

- Added one `docs/adr/*.md` source: `note_type="document"`, tags `["adr","architecture","static-corpus"]`, provider `static:adr`.
- Added four boundary tests.
- No new ingestion path; ingestion still flows through `knowledge.pipeline.ingest()`.
- No API, governance, authority, identity, ontology, or execution surface touched.

## 3. Runtime evidence

Isolated Knowledge OS:

| Run | Result |
|---|---|
| Before change | `{ingested: 28, skipped: 0, errors: 0}` |
| After change, first pass | `{ingested: 34, skipped: 0, errors: 0}` |
| After change, second pass | `{ingested: 0, skipped: 34, errors: 0}` |

Exactly six `static:adr` rows are present.

## 4. Regression boundary

- Full suite: **891 passed / 49 failed / 12 skipped / 2 errors**.
- Failing/error node-id set unchanged from the recorded baseline.
- Architecture gate: **11/11**.
- `py_compile api/main.py knowledge/static_ingestion.py`: clean.
- No vault test-output leakage.

## 5. Remaining uncertainty

K5 is **not complete**. `docs/recon/` and `docs/verification/` remain outside `_SOURCES`. Broad recursion is deliberately not executed because it is a corpus-curation decision, not a mechanical ingestion fix.

## 6. Authorization

No self-merge. Human review and merge remain required.
