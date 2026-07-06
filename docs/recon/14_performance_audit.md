# 14 — Performance Audit

**Important caveat per mission principles ("do not guess"): this session performed static/read-only code analysis only. No bundle-size measurement, no load testing, no profiling was executed.** The items below are either directly observable facts from code structure, or explicitly marked as "not measured — requires instrumentation."

## Directly Observable (from code structure)
- **No streaming responses** for any Gemini call (AI Infrastructure Blueprint) — every Oracle/CEO-chat/planner response blocks until full generation completes. This is a structural latency ceiling, not a bug, but is worth measuring actual p50/p95 response times before deciding whether to invest in streaming.
- **12-turn hardcoded conversation history window** (`api/main.py`) bounds per-request prompt size — a deliberate cost/latency control, not a leak.
- **JSON-file stores rewritten in full on every mutation** (`oracle_store.json`, `job_store.json`, `goal_store.json`) — fine at current scale; will degrade linearly as these files grow, since Python's typical atomic-write pattern (write temp file, rename) still requires serializing the entire file per write.
- **Kernel worker pool defaults to 2 threads** (`SOLSPIRE_WORKERS`, per replit.md) — a deliberately small concurrency ceiling for job processing; under bursty load, jobs will queue rather than parallelize beyond this.
- **Two independent 6-hour/60-second caches stacked** for corpus freshness (`corpus/manager.py` disk cache + `api/main.py` in-memory cache) — redundant layering, not necessarily harmful, but adds complexity for marginal benefit at current corpus size (~29 scrolls per current session's workflow logs).
- **Frontend has no code-splitting evidence identified** (React lazy/Suspense not confirmed present) across 19+ page components including several 1000+ line pages — likely means the entire page set ships in one bundle. **Not measured** — actual bundle size unknown without running `vite build` and inspecting output.

## Not Measured — Requires Follow-Up Instrumentation
- Bundle size (would require `cd web/public_prism && npm run build` + inspect `dist/` output).
- Cold start time for the FastAPI service (would require timing an actual boot).
- Database/JSON-file read/write latency under realistic file sizes.
- API endpoint latency distribution (would require request tracing/APM, none found configured).
- React render-frequency/re-render hotspots (would require React DevTools profiler session, not available in this read-only static pass).
- Embedding/search cost — moot currently since no real embedding pipeline exists (see AI Infrastructure Blueprint); if one is added later, cost modeling should happen then.
- Memory leaks — not testable via static analysis; would require a running-process heap profile.

## Recommendation
Before optimizing anything performance-related, first **measure**: run a production build to get real bundle sizes, and add basic request-timing logging to `api/main.py` for the Gemini-backed endpoints. Static analysis alone cannot responsibly produce specific performance recommendations here without risking exactly the kind of guesswork this mission explicitly prohibits.
