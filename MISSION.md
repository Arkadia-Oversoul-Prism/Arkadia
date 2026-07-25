# Arkadia — Mission
> One page. Never grow this file. Update at the end of every session.
> Start here. Then read BOOTSTRAP.md and CURRENT_STATE.md. Nothing else is mandatory.

---

## Current Phase
Phase 1 — Runtime Stabilization

## Current Workstream
C — Corpus Synchronisation

## Current Checkpoint
**C1.2 — Incremental Sync Engine**

## Today's Goal
Implement `github_corpus_incremental.py` with SHA-comparison logic, per-file
checkpoint writes, and rate-limit backoff. Unit-test with mocked GitHub
responses. Do not modify `github_corpus.py` or any API file.

## Stop Condition
`pytest tests/test_corpus_sync_incremental.py` passes.
`pytest tests/architecture/` is 10/10.
`github_corpus_incremental.py` implements the algorithm in CORPUS_SYNC_DESIGN.md.
Repository is deployable.

## Success Criteria
- [ ] `github_corpus_incremental.py` implements `incremental_sync()`
- [ ] `load_sync_state()` / `save_sync_state()` read/write `corpus_sync_state`
- [ ] `load_file_shas()` / `save_file_sha()` read/write `corpus_file_state`
- [ ] `fetch_with_backoff()` handles 403 + X-RateLimit-Remaining
- [ ] Unit tests cover: tree-unchanged fast-path, partial ingest, rate-limit abort, resumability
- [ ] `pytest tests/test_corpus_sync_incremental.py` — all passing
- [ ] Architecture fitness: 10/10
- [ ] `docs/checkpoints/C1.2.md` written
- [ ] `CURRENT_STATE.md` updated to C1.3 ready
