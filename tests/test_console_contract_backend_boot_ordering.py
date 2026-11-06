"""Boundary guard: the authenticated layout check must be able to boot its backend.

The authenticated layout check in ``.github/workflows/prism-console-contract.yml``
boots the real backend with ``python -m uvicorn`` and waits for ``/health`` before it
measures any layout. That import fails unless the backend's runtime dependencies are
installed first.
