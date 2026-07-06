# 11 — Dependency Audit

## Node.js Manifests (5 found across the repo, one is a nested duplicate project)

| Manifest | React | Vite | Tailwind | Notable deps |
|---|---|---|---|---|
| `/package.json` (root) | ^19.2.6 | ^8.0.14 | ^4.3.0 | `@google/genai` ^2.6.0, `@google/generative-ai` ^0.24.1, `discord.js` ^14.26.4, `firebase` ^12.14.0, `drizzle-zod`, `zod`, `@tanstack/react-query` ^5.100.14, `wouter` ^3.10.0 |
| `/web/public_prism/package.json` | **^18.3.1** | **^5.4.21** | **^3.4.4** | `firebase` ^12.12.0, `react-router-dom` ^7.11.0 (unused for routing — see Frontend Blueprint), `wouter` ^3.9.0, `recharts` ^3.8.1 |
| `/bot/package.json` | — | — | — | `@google/generative-ai` ^0.21.0, `discord.js` ^14.0.0 |
| `/openclaw/package.json` | — | — | — | `express` ^4.19.2, `node-telegram-bot-api` ^0.66.0 |
| `/artifacts/mockup-sandbox/package.json` | 19.1.0 | ^7.3.0 | ^4.1.14 | Radix UI suite, `recharts` ^2.15.4 (tooling only, not shipped product) |
| `/attached_assets/arkadia_spirit/GovernanceSpirit/package.json` | ^18.3.1 | ^5.4.14 | ^3.4.17 | `drizzle-orm`, `express`, `passport` (isolated nested app, not part of live product) |

### Version Mismatches (real risk)
- **React 19 (root) vs React 18.3.1 (web/public_prism — the actual shipped frontend)**. The root `package.json`'s React version is irrelevant to what ships, but its presence is confusing and risks accidental `npm install` at the wrong directory level pulling incompatible versions.
- **Vite 8 (root, bleeding-edge/pre-release-range) vs Vite 5.4.21 (shipped frontend) vs Vite 7 (mockup sandbox)** — three different major versions in one repo.
- **Tailwind 4 (root) vs Tailwind 3.4.4 (shipped frontend)** — Tailwind 4 has breaking config-format changes from v3; if anyone runs root-level Tailwind tooling against the frontend's `tailwind.config.js` (v3 format) it will fail.
- **Router duplication**: both `wouter` and `react-router-dom` are installed in the same `package.json` (root and `web/public_prism`), but the frontend blueprint confirms neither is actually used for page navigation (state-based `View` union instead) — both may be dead weight, or used for a sub-feature not yet identified (flagged as uncertain, not confirmed dead).

## Python Manifests (3 found, 1 legacy)
| Manifest | Python | Key deps |
|---|---|---|
| `/requirements.txt` (root) | 3.11-slim (Dockerfile) | `fastapi`, `uvicorn[standard]`, `google-generativeai`, `pydantic`, `httpx`, `pdfminer.six`, `python-docx`, `beautifulsoup4`, `piper-tts`, `edge-tts`, `firebase-admin` |
| `/arkana_space/requirements.txt` | 3.11-slim | `fastapi`, `uvicorn`, `pydantic`, `httpx`, `pyyaml` — a lean subset, consistent with it being a separate lightweight deployable |
| `/archive/legacy_python/requirements.txt` | — | `sqlalchemy`, `psycopg2-binary`, `sift-stack-py`, `google-api-python-client` — **none of these are used by the active `api/` service**, confirming this directory is safely archival |

### Notable dependency observations
- `piper-tts` is still listed in root `requirements.txt` despite Edge TTS being the active engine per session memory (`.agents/memory/tts-engine.md`) — likely a leftover, low-risk dependency bloat.
- `firebase-admin` (backend) vs `firebase` JS SDK (frontend) is the correct/expected split, not a conflict.

## Android
Two parallel modules (`sonata/` Java, `sonata-android/` Kotlin), both targeting SDK 34, Java 17/Kotlin 1.9 — no version conflict between them since they're fully independent build trees, but their *coexistence* is itself the redundancy (see Redundancy Audit).

## Security/Maintenance Posture of Dependencies
Not independently vulnerability-scanned this session (would require `npm audit`/`pip-audit` execution, not performed as part of this read-only recon). Flagged as a follow-up action.
