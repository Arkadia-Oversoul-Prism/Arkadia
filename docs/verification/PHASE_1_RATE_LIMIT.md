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

## Production smoke (2026-08-19)

Host: `https://arkadia-kw64.onrender.com`  
Commit: `9c0a6ac`

| Probe | Result |
|-------|--------|
| Exempt `/api/knowledge/status` | 200 |
| Search under limit | 200 |
| Search burst → 429 at request 60 | PASS |
| `Retry-After` present | PASS (e.g. 49s) |
| 429 JSON `{detail, retry_after}` | PASS |
| Exempt after burst | 200 |
| Public corpus after window | 200 |
| Personal ingest unauth | 401 |
| Anon graph no private owners | PASS |
| UID keying (A exhausts, B still 200) | PASS |

**PHASE 1 PRODUCTION SMOKE: GREEN**

Caveat remains: in-memory limiter is per process, not cross-instance.
