# Archived Vercel routing configuration

**Archived:** 2026-10-10  
**Reason:** Arkadia no longer deploys its frontend through Vercel. The primary frontend, operator console, and API are built and served from the single canonical Render service at https://arkadia-qzu4.onrender.com.

These configurations are preserved as historical records only. They must not be restored as active routing.

## Former repository-root `vercel.json`

```json
{
  "installCommand": "cd web/console && pnpm install --frozen-lockfile",
  "buildCommand": "cd web/console && pnpm run build",
  "outputDirectory": "web/console/dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}

```

## Former `web/public_prism/vercel.json`

```json
{
  "framework": "vite",
  "buildCommand": "pnpm run build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install --frozen-lockfile",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://arkadia-kw64.onrender.com/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}

```

## Former `web/console/vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "installCommand": "pnpm install --frozen-lockfile",
  "buildCommand": "pnpm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}

```

The former Prism rewrite routed `/api/*` to `https://arkadia-kw64.onrender.com`, creating a split-origin path. That route is retired. Production browser traffic now reaches the frontend and backend through the same Render service and origin.
