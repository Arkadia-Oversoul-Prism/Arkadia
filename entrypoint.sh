#!/usr/bin/env bash
set -euo pipefail

echo "Starting Arkadia Oracle Temple..."

mkdir -p /run

# Vite bakes import.meta.env into static assets at image-build time. Render's
# runtime environment is not automatically available in that build stage, so
# write only the public Firebase Web config into the served frontend at startup.
# Firebase Web config is client-side configuration, never the Admin service account.
python3 - <<'PY'
import json
import os
from pathlib import Path

keys = {
    "apiKey": "VITE_FIREBASE_API_KEY",
    "authDomain": "VITE_FIREBASE_AUTH_DOMAIN",
    "projectId": "VITE_FIREBASE_PROJECT_ID",
    "appId": "VITE_FIREBASE_APP_ID",
}
config = {field: os.environ.get(env_name, "").strip() for field, env_name in keys.items()}
config_path = Path("/app/web/public_prism/dist/firebase-config.js")
config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(
    "window.__ARKADIA_FIREBASE_CONFIG__ = "
    + json.dumps(config, separators=(",", ":"))
    + ";" + chr(10),
    encoding="utf-8",
)
configured = all(config.values())
print(f"[FRONTEND-CONFIG] Firebase web config {'present' if configured else 'incomplete'}; values withheld.")
PY

echo "  GOOGLE_API_KEY:                $([ -n "${GOOGLE_API_KEY:-}" ] && echo "set (oracle + planner active)" || echo "NOT SET — Phase 7 planner will use deterministic fallback")"
echo "  GITHUB_PERSONAL_ACCESS_TOKEN:  $([ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ] && echo "set" || echo "NOT SET — corpus will only see public files")"

# Use PORT from environment (Render sets this) or default to 8080
PORT="${PORT:-8080}"
echo "  Starting server on port:       ${PORT}"

exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --log-level info
