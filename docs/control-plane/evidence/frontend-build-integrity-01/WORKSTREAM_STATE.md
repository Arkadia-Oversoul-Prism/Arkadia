# WORKSTREAM_STATE — gate-hygiene / FB-01 frontend build integrity

**Gate:** GATE-00 baseline hygiene (pre-gate engineering envelope)
**Workstream:** `gate-hygiene` → frontend build integrity (new bounded thread)
**Pass:** heartbeat, `BASE_MAIN` = `002b189` (merge of PR #141)
**Branch:** `gate-hygiene/frontend-build-verification-01`
**PR:** #160
**Classification:** `IMPLEMENTED` — build proven, architecture green, zero regression. **READY FOR SOVEREIGN MERGE**

---

## Objective (bounded)

Repo memory (`AGENTS.md`) recorded `vite build` as *environment-blocked (no npm registry
access)*, and every prior ledger row repeated it verbatim (e.g. F-02: "`vite build` |
environment-blocked (no npm registry) — unchanged"). The claim had never been re-tested
since it was first written.

This pass re-tested it. It is **false**, and it was concealing two real defects.

## Defects found

1. **`vite.config.js` shadowed `vite.config.ts`.** Vite resolves config extensions `.js`
   before `.ts`, so the tracked `.js` won and the canonical build config (`manualChunks`,
   `chunkSizeWarningLimit`) was never read. Every build silently bypassed vendor chunking —
   visible only as a single 1,939 kB entry bundle with no vendor chunks.
2. **The canonical config was itself unbuildable.** `manualChunks` named the bare specifier
   `"firebase"`; Firebase 12.x removed the root `"."` export. Removing the shadow exposed
   this immediately. Neither defect is observable without the other.

## State reconstructed this pass (from live evidence, not memory)

| item | value |
|---|---|
| `main` / `origin/main` / `origin/HEAD` | `002b189` (merge of #141) — agree |
| open PRs at pass start | **19** (#142–#159) |
| full suite | `20 failed / 1041 passed / 11 skipped / 2 collection errors` |
| `tests/architecture` | **11/11** |
| `api/main.py` | 2519 lines, `py_compile` clean |
| `vite build` | **WORKS** — registry reachable (200 in 0.08s); this row was wrong in every prior ledger |
| CP10 judge | PASS |

Fingerprint is **identical to the recorded baseline** — no drift attributable to any open PR.

## Correction to the ledger baseline

Prior rows carry `architecture := 9/10` and later `11/11`; the task contract says "expect
10/10". Live evidence is **11 tests, 11 passing**. The contract's count is stale. Live
evidence wins — this is the same class of error as the `vite build` claim: a recorded number
that stopped being re-derived.

## Changes

| File | Change |
|---|---|
| `web/public_prism/vite.config.ts` | firebase manualChunks → subpaths |
| `web/public_prism/vite.config.js` | deleted (shadow) |
| `web/public_prism/dist/index.html` | deleted (broken pointer) |
| `web/public_prism/vite.config.js.timestamp-*.mjs` | deleted (generated shadow) |
| `web/public_prism/.gitignore` | ignore `vite.config.js.timestamp-*.mjs` |
| `docs/control-plane/evidence/frontend-build-integrity-01/EVIDENCE.md` | new |

## Evidence

- Build: exit 0, 3438 modules, entry bundle **1,939.32 kB → 820.85 kB**, real vendor chunks.
- Full suite: `20F/1041P/11S/2E` — byte-identical to pre-change fingerprint.
- Architecture: 11 passed.
- CP10 judge: PASS.
- CI on PR #160: `validate` pass, `Vercel` pass, `Full-history secret scan` pass,
  `Vercel Preview Comments` pass — **4/4**. Vercel building the canonical config green is
  independent confirmation outside the sandbox.

## Queue position

Verified orthogonal to all 19 open PRs: none touch `vite.config.*`, `public_prism/dist/`, or
`public_prism/.gitignore`.

## Credential finding (carry forward)

`GITHUB_PERSONAL_ACCESS_TOKEN` is **invalid** (`401` on `/repos/...`). `github_token` is
valid (`200`, repo `permissions.push = true`) and was used for this push. Any automation
binding `GITHUB_PERSONAL_ACCESS_TOKEN` for git/API work will silently fail. Not fixed —
recorded so the next pass does not re-derive it.

## Next bounded task (proposed, not started)

Repair the **two collection errors** (`tests/test_autonomy.py` →
`load_autonomy_config`; `tests/test_render_codex.py` → `arkadia_drive_sync`) — the
longest-standing, best-characterised baseline debt. PR #149 already claims
`test_render_codex.py` is a *naming defect, not a missing dependency*; that claim should be
adjudicated against live evidence before any repair is attempted, to avoid duplicating
in-flight work.

**Not started** — discovery does not authorize execution. Requires its own bounded envelope.
