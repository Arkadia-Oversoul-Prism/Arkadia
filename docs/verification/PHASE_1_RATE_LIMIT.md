# PHASE 1 — Rate Limiting / Operational Hardening

**Status:** IMPLEMENTED (code-level)  
**Commit target:** after `4d00d5b` Phase 0C baseline  

## Design

- In-memory sliding window (no Redis required)
- Key: `uid:<firebase_uid>` when Bearer present, else `ip:<client>`
- Path-prefix limits (longest match wins)
- Exempt: `/api/knowledge/status`, `/health`, `/docs`, static assets
- 429 + `Retry-After` header
- Disable: `ARKADIA_RATE_LIMIT=0`

## Default free-tier envelope

| Prefix | Limit |
|--------|-------|
| `/api/commune/resonance` | 20 / 60s |
| `/api/personal/` | 15 / 60s |
| `/api/knowledge/ingest` | 20 / 60s |
| `/api/knowledge/search` | 60 / 60s |
| `/api/knowledge/` | 90 / 60s |
| `/api/` | 120 / 60s |

Override via `ARKADIA_RL_*` env vars (see `.env.example`).

## Tests

`pytest tests/test_rate_limit.py` — pure logic  
Isolation + oracle suites remain green.

## Limits

- Per-process memory only (Render multi-instance does not share buckets)
- Not a substitute for edge WAF / Cloudflare
- Payload size limits and TTS quotas are separate follow-ups
