# Arkadia — Deployment Guide

**Canonical deployment:** one reconciled deployment, per
`docs/adr/ADR-016-single-canonical-deployment.md`.
**Production origin:** `https://arkadia-qzu4.onrender.com` (Render service `arkadia-qzu4`).
**Read-only revision probe:** `GET /api/version`.

Deployment, verification and acceptance are three different things. This guide describes how to
build and verify the application. It does not assert that the running deployment is correct, and it
does not grant acceptance — that is a human decision.

## What is deployed

One application, built from the repository-root `Dockerfile`:

| Part | Path | Role |
|---|---|---|
| Frontend | `web/arkadia_console` | The active console. Built with pnpm in the `frontend-build` stage into `dist/`, then copied into the runtime image. |
| Backend | `api/main.py` | FastAPI application. |
| Serving path | `api/frontend_routes.py` | Serves the built console; holds the reserved-prefix list that keeps API namespaces out of the SPA catch-all. |
| Process | `entrypoint.sh` | Container entrypoint. Reads `$PORT` and writes the public Firebase web config into the served bundle. |

Two trees are present but **not** built, by design:

- `archive/frontend/arkadia-prism` — the retired Prism UI. Its README records the recovery path.
- `web/console` — the former standalone operator application. Its capabilities were migrated into
  `web/arkadia_console`'s route hierarchy; the source is retained for a reversible retirement.

`railway.json` also builds from the root `Dockerfile` and health-checks `/api/heartbeat`. It is an
alternative platform configuration for the same image, not a second application.

## Verifying a deployment

Read the revision the runtime actually reports:

```bash
curl -s https://arkadia-qzu4.onrender.com/api/version
```

The response carries `source_revision` (from `RENDER_GIT_COMMIT`), `revision_source`,
`revision_conflict` and `verification_note`. `api/version_routes.py` is the source.

- `revision_conflict: false` with a `source_revision` equal to the `main` SHA is **necessary**
  evidence of source-to-runtime consistency.
- It is **not** proof that the application behaves correctly, and it is **not** deployment
  acceptance.
- A deployment URL that cannot be read anonymously is an unproven boundary, not a passing one.
  Record it as `UNKNOWN` rather than inferring parity.

## Environment variables

| Variable | Consumed by | Notes |
|---|---|---|
| `PORT` | `entrypoint.sh` | Injected by the platform. Do not hardcode a production port. |
| `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID` | `entrypoint.sh` | Public Firebase **web** config, written into the served bundle at startup. Client-side configuration, not a secret. |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | `api/key_pool.py` | One source of the Gemini key pool. |
| `ELEVENLABS_API_KEY` | `kernel/tts.py` | Enables the premium TTS path; Edge TTS is the free fallback. |

Provider and TTS keys can also be supplied through the key stores (`api/provider_key_store.py`,
`api/key_manager.py`, `api/tts_key_manager.py`) rather than the environment. All of them are
optional for boot; the application degrades rather than failing to start.

The Firebase **Admin** service account is a server-side credential. Never bake it into the frontend
bundle, and never commit a secret value to a tracked file.

## Building and running the image locally

```bash
docker build -t arkadia .
docker run -p 8080:8080 -e PORT=8080 arkadia
```

The build installs `requirements.txt` and produces the console bundle in the same image, so a local
run serves the same artifact shape as the deployed one.

## API surface

The table below is the **canonical repository app surface**, verified against `api.main:app` (the app
`entrypoint.sh` serves). It describes the current source contract, not an assertion that every route
is already present on the deployed runtime. Deployment identity and a live probe are required before
claiming runtime parity.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Serves the console to a browser navigation; otherwise a liveness payload |
| `GET` | `/api/heartbeat` | Health check — canonical; used by `railway.json` |
| `GET` | `/health` | Liveness projection of `/api/heartbeat` (deployment contract path) |
| `GET` | `/api/version` | Read-only source-revision probe (ADR-016) |
| `POST` | `/api/commune/resonance` | Oracle / ReasoMate chat (POST-only) |
| `GET`, `POST` | `/api/commune/threads` | List / create conversation threads |
| `GET` | `/api/commune/threads/{thread_uuid}` | Thread metadata |
| `GET` | `/api/commune/threads/{thread_uuid}/messages` | Thread messages |
| `GET` | `/api/oracle-context` | Oracle context snapshot |
| `POST` | `/api/corpus/refresh` | Refresh the corpus |
| `GET` | `/api/codex` | Spiral Codex scrolls |
| `GET`, `POST` | `/api/scrolls` | List / write public scrolls |
| `GET` | `/api/stellar-cartography` | Encyclopedia Galactica star date |

Interactive API reference: `GET /docs` (and `GET /openapi.json`). These are FastAPI's own
documentation routes and are deliberately absent from the OpenAPI schema, so they are not listed in
the table above.

`/health` is a projection of `/api/heartbeat`, not a second liveness authority. Note that
`/api/health` is **not** a route: a `404` there is correct.

> The `openclaw/` gateway is a **separate** service with its own configuration and its own
> `GET /health`; it is not this backend and is not covered by the table above.

## What this guide does not authorize

An observed hostname is not proof of canonical ownership, and a successful HTTP response from an
alternate deployment does not establish acceptance. Do not stand up a second canonical deployment,
change production routing, or retire an alias without explicit human authorization.

## Testing the deployed surface

```bash
curl -s https://arkadia-qzu4.onrender.com/api/version
curl -s https://arkadia-qzu4.onrender.com/api/heartbeat
```

For the console, load the origin in a browser and exercise the route you changed. A `200` on any
path proves nothing by itself: the SPA catch-all serves the console for routes it does not own, so a
route assertion must be read against `api/frontend_routes.py` and the router, not against an HTTP
status.

The legacy CLI remains runnable from the archive for corpus work:

```bash
python archive/legacy_python/arkadia_console.py
# Commands: tree, preview <file>, refresh, ask <question>, status, exit
```

---

**Built for the House of Three.**
