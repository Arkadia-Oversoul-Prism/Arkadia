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
