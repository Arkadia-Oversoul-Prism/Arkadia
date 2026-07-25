# Arkadia — Current State
> Updated at the end of every session. The next agent reads this before anything else.
> If this file and another document disagree, verify the code. Update this file. (Principle 11)

---

## Phase
Phase 1 — Runtime Stabilization

## Checkpoint
**C1.2 — Incremental Sync Engine** (READY TO BEGIN)

## Mode
BUILD

## Objective
Implement `github_corpus_incremental.py` with the incremental sync algorithm
from `docs/phase1/CORPUS_SYNC_DESIGN.md`. Unit-test with mocked GitHub
responses. Do not touch `github_corpus.py`, `api/`, or architecture tests.

## Scope (this checkpoint only)
- Create `github_corpus_incremental.py` at repo root (alongside `github_corpus.py`)
- Implement `incremental_sync(repo, branch, token)` → `SyncResult`
- Implement `load_sync_state()` / `save_sync_state()` using `corpus_sync_state` table
- Implement `load_file_shas()` / `save_file_sha()` using `corpus_file_state` table
- Implement `fetch_with_backoff()` with rate-limit handling (X-RateLimit-Remaining)
- Write `tests/test_corpus_sync_incremental.py`
- `github_corpus.py` is NOT modified

## Stop When
All tests pass. Architecture fitness 10/10. `github_corpus.py` untouched. Repository deployable.

## Do Not Touch
- `github_corpus.py` (unchanged until C1.3 cutover)
- `api/` (any file)
- Fitness tests / LAYER_MAP.py
- ADRs / Governance docs

## Blocked By
Nothing.

## Repository Health
- Branch: `main`
- Architecture fitness: 10/10 passing
- Schema tests: 11/11 passing (B1.1)
- Job store tests: 21/21 passing (B1.2)
- Goal store tests: 26/26 passing (B1.2)
- Corpus sync schema tests: 13/13 passing (C1.1)
- Total: 81/81 passing
- Workflows: failing (pre-existing — missing secrets, not a C1 blocker)

## Deployment Status
- **Render:** exhausted free-tier allocation — unavailable
- **Railway:** configuration committed (`railway.json` + `docs/deployment/RAILWAY.md`)
  - Pending: operator must create Railway service, set env vars, add volume at `/arkadia-data`
  - See `docs/deployment/RAILWAY.md` for full steps

## Success Criteria (C1.2)
- [ ] `github_corpus_incremental.py` exists at repo root
- [ ] `incremental_sync()` implements algorithm from CORPUS_SYNC_DESIGN.md
- [ ] `fetch_with_backoff()` handles 403 + rate-limit headers
- [ ] `pytest tests/test_corpus_sync_incremental.py` passes
- [ ] `pytest tests/architecture/` still 10/10
- [ ] Repository deployable
- [ ] `docs/checkpoints/C1.2.md` written
- [ ] `CURRENT_STATE.md` updated to C1.3 ready

## Last Session
Infrastructure — Railway migration configuration.
- Created `railway.json` (root): DOCKERFILE builder, healthcheck `/api/heartbeat`, restart on failure
- Created `docs/deployment/RAILWAY.md`: env vars, volume setup, migration from Render, rollback
- No application code modified
- Architecture fitness: 10/10 (unchanged)

## Next Checkpoints (do not implement yet)
- C1.3 — Integration: switch `/api/sync` endpoint to `incremental_sync()`
- C1.4 — Cleanup: remove legacy `github_corpus.py` after two stable cycles; close Gate F
