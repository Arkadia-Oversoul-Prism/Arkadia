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

Rehearsed at `main` `a58f0849` (see "Rehearsal result" below): the archived tree
installs with `--frozen-lockfile` and builds the same artifact the canonical
runtime served before the cutover.

To restore Prism as the served application:

1. Move the tree back to its canonical path:

   ```bash
   git mv archive/frontend/arkadia-prism/web/public_prism web/public_prism
   ```

2. Repoint the build and serving paths at it. Two surfaces currently name the
   **console** (`web/arkadia_console`) and must be changed to name
   `web/public_prism`:

   - `Dockerfile` — the `frontend-build` stage currently copies
     `web/arkadia_console/`, runs `pnpm install --frozen-lockfile && pnpm run
     build` there, and `COPY --from=frontend-build
     /build/web/arkadia_console/dist …`. Repoint all three at
     `web/public_prism`.
   - `api/frontend_routes.py` — `configure_frontends()` currently sets
     `console_app_dist = … / "web" / "arkadia_console" / "dist"`. Repoint it at
     `web/public_prism/dist`.

   (Before the console rebuild these two named `web/public_prism`; this step is
   the inverse of the cutover, not a new edit.)

3. Rebuild and redeploy. The build command is unchanged:
   `pnpm install --frozen-lockfile && pnpm run build` inside the package.

4. Confirm the served revision with `GET /api/version` **and** re-read the served
   asset before claiming any restoration — a matching revision is necessary
   evidence, not proof the application works.

The archived tree keeps a `pnpm-lock.yaml`, so the frozen-lockfile install path
continues to work from the archive location without regenerating the lockfile.

## Rehearsal result

Measured at `main` `a58f0849` in a detached worktree:

- `git mv` of the tree back to `web/public_prism` succeeds.
- `corepack pnpm install --frozen-lockfile` succeeds.
- `corepack pnpm build` emits `dist/assets/index-BzLymmg4.js` (890.33 kB) — the
  same bundle hash the canonical runtime served before the console cutover. The
  archive is bit-for-bit recoverable.

## Provenance

- Prism source was current in `main` through `eb63342d1951e638b8952f4b66ea1308f052ed2f`,
  the revision immediately before the console rebuild merged.
- The last **measured** Production deployment serving Prism was `c8abb28e4ac0`
  (GitHub deployment `6985099151`, 2026-10-10). Its served bundle was
  `assets/index-BzLymmg4.js` (890 kB) — the same artifact this archive rebuilds.
  (Source revision `eb63342d` and running revision `c8abb28e` are distinct
  concepts; the running revision is the measured one.)
- Archive record: `docs/control-plane/evidence/frontend-arkadia-console-01/`.
