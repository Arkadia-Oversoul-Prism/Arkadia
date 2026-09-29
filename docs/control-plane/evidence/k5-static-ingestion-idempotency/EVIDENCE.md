# K5 — Static Ingestion · vault-projection re-ingestion defect · Evidence

Gate: **Workstream K — Checkpoint K5 (Static Ingestion)**
Branch: `gate-k/k5-static-ingestion-idempotency`
Base: `main` @ `a26af40` (`BASE_MAIN`, merge of PR #104)
Status: **VERIFIED** — bounded, evidence-backed. Human review + merge remain mandatory.

---

## 1. The defect

K5's idempotency guarantee was believed to hold. It does not hold under production cwd.

Reproduced on `main` @ `a26af40` at repository root:

```
pass1: {'ingested': 33, 'skipped': 31, 'errors': 0}  total_notes=33
pass2: {'ingested':  2, 'skipped': 64, 'errors': 0}  total_notes=35
pass3: {'ingested':  0, 'skipped': 68, 'errors': 0}  total_notes=35
```

Two objects were re-ingested on the second pass. Characterised: both were the
`static:oracle_open_loops` records (`Open loop: ship phase 4`, `Open loop: phase 6
verify`), re-entering through the `static:vault` source.

## 2. Root cause

A persistence round-trip that is not a fixed point of the dedup key.

`knowledge/pipeline.ingest()` dedupes on `sha256(content)`. `knowledge/vault.create_note()`
persists `_build_frontmatter(row) + content` to disk. `_ingest_oracle_open_loops()`
passed content carrying a **trailing newline**; `vault.py` writes it verbatim, and
`_strip_frontmatter()` returns the body with trailing whitespace stripped.

So the stored checksum was `sha256("Open loop\nID: …\nUpdated: …\n")` while the
re-read (and re-checksummed) body was `sha256("Open loop\nID: …\nUpdated: …")`. Proven
directly:

```
orig        a2ec82a33386b9c4…
round-trip  397fc7adf15d20f4…
checksum equal? False
```

The mechanism is source-agnostic: *any* ingest whose content is not already
`strip()`-clean writes a projection that can never match its own checksum. It surfaces
via `vault/` only because that is both a K5 write target and a K5 scan root.

## 3. Bounded change

- `knowledge/static_ingestion.py`
  - new `_normalize_body()` — the single definition of a note body for checksum
    purposes (`text.strip()`).
  - `_ingest_oracle_open_loops()` builds content through it; the trailing newline is
    removed (trailing whitespace is presentation, not content).
  - the file-source path normalises the body on read, so legacy projections written
    before this fix converge instead of duplicating forever.
  - module docstring records the residual, un-fixable-in-layer boundary: a note
    created from source A is still a real second object when source B scans the same
    bytes. K5 works *because* `static:vault` runs after the other sources; that is an
    ordering property, now documented rather than assumed.
- `tests/test_static_ingestion_idempotency.py` — 2 tests, private tempdir DB + vault.
- This evidence record.

No new ingestion path. Every object still flows through `knowledge.pipeline.ingest()`.
No API, governance, authority, identity, pipeline, ontology, migration, or execution
surface touched. `api/main.py` is unmodified (`2519` lines).

## 4. Verification

- **Round-trip fixed point** — the 3-pass production-fidelity repro is now stable:
  `36 → 0/36 → 0/36 → 0/36`.
- **The production path itself** — simulating `static:vault` re-scanning all 36
  on-disk projections: `re-ingested (spurious): 0`, `total_notes` unchanged at 36.
  This is the exact failure that produced `pass2 ingested=2`.
- Scoped: `tests/test_static_ingestion_sources.py` +
  `tests/test_static_ingestion_idempotency.py` → **12 passed**.
- Architecture gate: **11/11**. `py_compile api/main.py`: clean.
- Full suite at pass start (`main` @ `a26af40`, `PYTHONPATH=archive/legacy_python`):
  **49 failed / 903 passed / 12 skipped / 2 errors**. 49 failing node-ids recorded;
  failure node-id set unchanged by this pass. Baseline debt documented, not fixed.
- Frontend `vite build`: environment-blocked, not attempted.

## 5. Remaining uncertainty

- Pre-fix projections already on disk (any deployment that ran the old code) carry the
  old whitespace. The read-side normalisation makes them dedupe on the next scan
  rather than duplicating, but their stored checksum remains pre-fix. No migration is
  proposed — it is a data, not a code, question and belongs to the sovereign.
- The `static:vault`-scans-its-own-writes ordering dependency is documented, not
  eliminated. Eliminating it would mean declaring a note-class exclusion for generated
  projections, which changes corpus semantics and is a curation call (cf. the
  `docs/recon/` curation question from PR #101/#103).

## 6. Authorization

Human review/merge remains required. No baseline debt folded in.
