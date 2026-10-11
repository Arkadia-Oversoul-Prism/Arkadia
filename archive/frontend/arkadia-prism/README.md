# Arkadia Prism — Archived Frontend

This directory holds the **retired Prism frontend** (`public_prism`). It is the
user-facing application that was deployed on the canonical runtime
(`https://arkadia-qzu4.onrender.com`) through revision
`eb63342d1951e638b8952f4b66ea1308f052ed2f`, before the Arkadia Console rebuild.

## What this is not

Archiving Prism does **not**:

- delete the Prism source — it is preserved in full here;
- retire "Prism" as an architectural concept — the term still appears across the
  repository's identity language and engineering records;
- remove any shared backend functionality — the FastAPI backend, APIs,
  authentication, provider routing, and persistence are untouched by this move.

Prism was moved here with `git mv`, so its full commit history is preserved and
`git log --follow` still works for every file.

## Layout

```
archive/frontend/arkadia-prism/
  web/public_prism/         # the retired application (React + Vite + TS + Tailwind)
    src/                    # ~30k LOC across 135 source files
    public/                 # static assets, including the audio files
    index.html
    package.json            # pnpm@10.26.1, node 24.x
    vite.config.ts
    tailwind.config.js
```

## Recovery procedure

To restore Prism as the served application:

1. Move the tree back to its canonical path:

   ```bash
   git mv archive/frontend/arkadia-prism/web/public_prism web/public_prism
   ```

2. Repoint the build and serving paths at it. The two surfaces that name the
   retired path are:

   - `Dockerfile` — the `frontend-build` stage copies `web/public_prism/` and
     runs `pnpm install --frozen-lockfile && pnpm run build`.
   - `api/frontend_routes.py` — `configure_frontends()` mounts
     `web/public_prism/dist` at `/` and `/assets`.

3. Rebuild and redeploy. The build command is unchanged:
   `pnpm install --frozen-lockfile && pnpm run build` inside the package.

4. Confirm the served revision with `GET /api/version` before claiming any
   restoration.

The archived tree keeps a `pnpm-lock.yaml`, so the frozen-lockfile install path
continues to work from the archive location without regenerating the lockfile.

## Provenance

- Last revision before archive: `eb63342d1951e638b8952f4b66ea1308f052ed2f`.
- Archive record: `docs/control-plane/evidence/frontend-arkadia-console-01/`.
