---
name: Recharts/es-toolkit runtime crash fix
description: Why recharts crashes at runtime and how it's fixed in Arkadia Prism
---

## The rule
DashboardView must stay lazy-loaded (`React.lazy` + `Suspense`). Do not move it back to eager imports.

**Why:** recharts 2.x ships CJS modules that call `require()` on es-toolkit 1.48.x. In es-toolkit ≥1.38 the CJS interop for `isUnsafeProperty` was refactored. When Vite bundles recharts eagerly, `require_isUnsafeProperty is not a function` crashes the entire SPA on load.

**How to apply:**
1. Keep `DashboardView` as `const DashboardView = React.lazy(() => import('./components/DashboardView'))` in App.tsx.
2. Keep `optimizeDeps: { include: ['recharts', 'es-toolkit', 'es-toolkit/compat'] }` in vite.config.ts — forces Vite to pre-bundle these CJS modules before runtime.
3. If recharts or es-toolkit is upgraded, re-test by navigating to the Dashboard view and checking browser console.
