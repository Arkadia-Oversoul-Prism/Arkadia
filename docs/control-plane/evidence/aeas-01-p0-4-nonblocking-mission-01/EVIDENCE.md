# AEAS-01 · P0.4-A — Non-blocking mission workspace (request-in-flight + session poll)

**Directive:** issue #590 — *Engineering Lab becomes the execution substrate for Arkadia One*
**Slice:** P0.4 — Make execution non-blocking and recoverable (first sub-increment)
**Date:** 2026-10-30
**Branch:** `aeas/p0-4-nonblocking-mission-01` (base: `a1fe177f`)

---

## 1. Why this slice

Measured baseline:

- `MissionWorkspace` used a single `phase: idle | working` that disabled **all** mission controls while any step awaited the server.
- Execute is a blocking HTTP POST; there is no SSE/WebSocket event transport.
- Resume-on-reload already existed and remained truthful (session id hint + server re-read; no authorization reconstruction).
- Sibling panels on the Lab page were already independent of mission `busy`.

P0.4 requires the operator to keep access to prior outputs and evidence during execution and to recover honestly after failure or reload.

## 2. What was implemented

### Frontend only (no backend mutation routes)

| File | Change |
|---|---|
| `web/arkadia_console/src/components/lab/MissionWorkspace.tsx` | Replace global `busy` with per-action `activeAction`. While `execute` is in flight, poll `GET /api/lab/engineering/sessions/{id}` every 1.5s for substrate events/state. Show explicit "Request in flight" banner (not LIVE). On execute failure, keep prior steps and re-read the view. |

### Explicit non-claims

- No SSE / WebSocket endpoint was added.
- No server-side async job queue.
- No decorative LIVE / SUCCESS indicator.
- "Request in flight" is client request state, not substrate `RUNNING`.
- Poll adopts a run only if the substrate already recorded one; the execute promise remains authoritative for the step label.

## 3. Overlap / governance

**PR #591** (`feat/dea-01-mission-state-guard-01`) was recorded in prior evidence as owning `MissionWorkspace.tsx` and related mission contract files. This branch edits `MissionWorkspace.tsx` under explicit human authorization for P0.4-A and is opened as a **draft** PR for human coordination. No merge is performed by this worker.

## 4. Verification

Automated tests and browser session against a live Firebase-authenticated Lab were **not** run in this worker environment. Required before acceptance:

```
# console typecheck / build
corepack pnpm --filter arkadia_console build   # or repo-equivalent

# existing lab / mission contract tests if present
.venv/bin/python -m pytest tests/test_lab_mission_workspace_contract.py -q
```

Manual operator check (when environment available):

1. Start mission steps; confirm only the active step is blocked.
2. During execute, confirm banner `Request in flight · execute` and that step timeline remains visible.
3. Confirm no control or label claims LIVE streaming.
4. Fail or reload; confirm prior steps/events remain and resume still re-reads the server without inventing authorization.

## 5. Capability status

| Capability | Status |
|---|---|
| Per-action non-blocking mission controls | **IMPLEMENTED** (code) — not browser-verified here |
| Session-view poll during execute | **IMPLEMENTED** (code) — depends on server returning events mid-request |
| Truthful "request in flight" label (not LIVE) | **IMPLEMENTED** |
| Preserve prior steps on execute failure | **IMPLEMENTED** |
| Resume after reload | **LIVE** (pre-existing; unchanged contract) |
| SSE / WebSocket live stream | **UNAVAILABLE** |
| Server async job API | **NOT IMPLEMENTED** |

## 6. Remaining gap

- Browser-verified operator path (P0.5) against authenticated Lab.
- If intermediate events never appear until POST returns (single-threaded server), poll still degrades safely to "no new events yet" without false LIVE claims.
- Coordination with PR #591 before merge.

## 7. Next bounded task

Human review of this draft PR vs #591; then either merge coordination or P0.5 browser evidence on the resulting head.
