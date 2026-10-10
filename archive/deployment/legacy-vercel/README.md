# Legacy Vercel artifacts — archived

Effective 2026-10-10, Vercel is not an active Arkadia deployment target.

Canonical production runtime:
- Render service: `Arkadia`
- Service ID: `srv-db49jbh42hec73aj84qg`
- Origin: `https://arkadia-qzu4.onrender.com`
- Repository/branch: `Arkadia-Oversoul-Prism/Arkadia` / `main`
- Build: root `Dockerfile`, which builds both frontends and the FastAPI backend into one image.

Files in this directory are preserved for historical auditability only. They must not be copied back into active root or frontend directories, and must not be treated as live routing configuration or production evidence.

The Render reconciliation workflow is `.github/workflows/render-production-reconciliation.yml`. It captures live `/openapi.json`, compares every path/method against the source composition root, probes the main UI/API routes, and records anonymous/invalid-token behavior. A valid authenticated non-sovereign test identity is still required before that part of the authorization matrix can be accepted.
