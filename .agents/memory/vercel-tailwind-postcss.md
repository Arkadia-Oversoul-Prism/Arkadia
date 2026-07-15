---
name: web/public_prism Tailwind version pin
description: Why the Vercel build crashes if @tailwindcss/postcss gets added to web/public_prism.
---

`web/public_prism` (the Vercel-deployed frontend) is pinned to Tailwind v3 (`tailwindcss@^3.x` +
`postcss.config.cjs` using the `tailwindcss` plugin key + `autoprefixer`). It must NOT depend on
`@tailwindcss/postcss` (the v4 PostCSS plugin) — that package name only works with `tailwindcss@^4`.

**Why:** having `tailwindcss@3.x` in `dependencies`/`devDependencies` alongside `@tailwindcss/postcss`
(v4 plugin) is a direct peer conflict. `npm install` on Vercel's build image crashes with
`npm error Exit handler never called!` (an npm-internal crash triggered by resolving that conflict),
which fails the whole deployment before any code even runs — the error message gives no hint that
Tailwind is the cause.

**How to apply:** if the Vercel build fails at `npm install` with a cryptic npm-internal error, check
`web/public_prism/package.json` for `@tailwindcss/postcss` and `web/public_prism/postcss.config.cjs`
for the `@tailwindcss/postcss` plugin key — remove both and use plain `tailwindcss: {}` in the postcss
config to match the pinned v3 major version. Root-level `package.json` (unrelated to the Vercel build,
see `vercel.json` installCommand) is on Tailwind v4 and correctly pairs with `@tailwindcss/postcss` —
don't "fix" that one to match.

**Separate recurring failure mode:** even after the Tailwind conflict was fixed, Vercel's `npm install`
kept crashing with npm's own internal bug `npm error Exit handler never called!` (unresolved npm/cli
arborist bug, e.g. npm/cli#8037/#8404 — not a project dependency conflict). Ruled out stale Vercel
build cache as the cause: forcing a cache skip (via a Node engine version change) reproduced the exact
same crash on a clean cache. `.npmrc` audit/fund=false and pinning `engines.node` did NOT fix it either.
**Actual fix:** switch the Vercel `installCommand` from `npm install` to `npm ci` (in `vercel.json`,
which is the file Vercel actually reads — `web/public_prism/vercel.json` is unused/vestigial but kept
in sync). `npm ci` takes a different, more deterministic arborist code path (installs straight from an
in-sync lockfile instead of re-resolving) and avoids this bug. Requires `package-lock.json` to stay in
sync with `package.json` — regenerate it locally with `npm install` after any dependency change, don't
hand-edit the lockfile. Keep `engines.node` on whatever Vercel currently recommends as non-deprecated
(check the deploy log's deprecation warning) rather than pinning an older LTS defensively.
