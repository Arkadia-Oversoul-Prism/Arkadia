# K5 — Static Ingestion · Open-loop corpus coverage gap · Evidence

Gate: **Workstream K — Checkpoint K5 (Static Ingestion)**
Branch: `gate-k/k5-open-loop-corpus-coverage`
Base: `main` @ `e6f79f1` (`BASE_MAIN`, merge of PR #102)
Status: **IMPLEMENTED** — bounded, evidence-backed. Human review + merge remain mandatory.

---

## 1. The gap

K5's own wording names the vault notes, ADRs, **open loops**, and structured markdown
under `docs/`. PR #101 closed the ADR half of that gap. The open-loop half was still open.

`docs/control-plane/evidence/k5-adr-static-ingestion/EVIDENCE.md` expressed this as
remaining uncertainty, but scoped it to `docs/recon/` and `docs/verification/` — a
*markdown* curation question. The open loops are not markdown. They are records inside
`data/oracle_store.json`, so no `root` + `glob` source can ever reach them. The gap was
therefore not a curation decision awaiting a sovereign call; it was a missing source
*shape*.

Reconstructed on `main` @ `e6f79f1`: `knowledge/static_ingestion.py::_SOURCES` declared
six roots — `static/**`, `docs/*.md`, `docs/collective/**`, `docs/creative/**`,
`vault/**`, and `docs/adr/*.md` — and no record source. The open loops in the canonical
oracle store were never seeded into the Knowledge OS.

## 2. Bounded change

- `knowledge/static_ingestion.py`
  - `_SOURCES` gains one **record** source: `kind="oracle_open_loops"`,
    `note_type="task"`, tags `["open-loop","oracle-store","static-corpus"]`,
    provider `static:oracle_open_loops`.
  - `_ORACLE_STORE_PATH` resolves the same store `kernel/oracle_store.py` owns
    (`SOLSPIRE_DATA_DIR` or `data/oracle_store.json`).
  - `_oracle_open_loop_rows()` — tolerant read; a missing or malformed store yields no
    rows and never raises.
  - `_ingest_oracle_open_loops()` — one `pipeline.ingest()` call per loop row.
  - `run_static_ingestion()` dispatches record sources before the filesystem path; the
    existing five-markdown-source loop is untouched.
- `tests/test_static_ingestion_sources.py` — six added tests.
- This evidence record.

No new ingestion path. Every record still flows through `knowledge.pipeline.ingest()`.
No API, governance, authority, identity, pipeline, ontology, migration, or execution
surface touched. `api/main.py` is unmodified (`2519` lines — the `schedule_static_ingestion()`
call site added by PR #101 already covers the new source).

## 3. Why the ingestion path is unchanged (LAW I)

The record source calls the same canonical entry point as every file source. Idempotency
is not re-implemented: `pipeline.ingest()` performs checksum deduplication against the
`notes` table, and the per-loop content is a pure function of the stored row (`id`, loop
text, status, `ts`, `updated_at`) — never a clock read taken at ingestion time. The same
row therefore renders byte-identical content on every pass and dedupes deterministically.

## 4. Runtime evidence

Isolated Knowledge OS (`ARKADIA_DB_PATH` + `VAULT_ROOT` redirected to a throwaway
directory), whole startup pass via `run_static_ingestion()`:

| Run | Result |
|---|---|
| Before change, first pass | `{"ingested": 34, "skipped": 0, "errors": 0}` |
| Before change, second pass | `{"ingested": 0, "skipped": 34, "errors": 0}` |
| After change, first pass | `{"ingested": 36, "skipped": 0, "errors": 0}` |
| After change, second pass | `{"ingested": 0, "skipped": 36, "errors": 0}` |

Provider tally after the change (SQLite `notes`):

```
static:adr 6 · static:collective 3 · static:creative 6 · static:docs 16
static:oracle_open_loops 2 · static:vault 3
```

`task` rows: `Open loop: ship phase 4`, `Open loop: phase 6 verify` — the two open loops
observed in the canonical store on this pass. Delta is exactly **+2**, matching the two
`status="open"` rows; nothing else moved. The `34 → 0 new` second pass on both sides of
the change is the idempotency proof.

## 5. Regression boundary

- Full suite (`--continue-on-collection-errors`): **49 failed / 899 passed / 10 skipped /
  2 errors**.
- Failing + error node-id set: **identical (51 nodes)** to the recorded baseline
  fingerprint at `/tmp/fingerprint_main.txt` (md5 `ad76b9d86dee682e58e3ce5b1431ee80`).
  Failure text differs in pytest's short-summary suffix only; no node entered or left the
  set.
- Architecture gate: **11/11**.
- `py_compile api/main.py knowledge/static_ingestion.py`: clean.
- `api/main.py`: **2519 / 2600** lines (budget unmoved).
- No vault test-output leakage (`find vault -name '*.md' …` → `0`).

## 6. Remaining uncertainty

K5 is **still not complete**. The markdown half of the gap is unchanged: `docs/recon/`,
`docs/verification/`, and the rest of the non-`docs/*.md` tree remain outside `_SOURCES`.
That is a corpus-curation decision — which documents belong in the Oracle's retrieval
corpus — and remains a sovereign call. It is deliberately not bundled here.

Also deliberate: this change ingests only rows where `open_loops` exist. A closed loop
already ingested stays in the corpus as historical record; no retraction path is added.

## 7. Authorization

No self-merge. Human review and merge remain required.
