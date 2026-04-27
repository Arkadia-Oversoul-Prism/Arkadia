#!/usr/bin/env bash
set -euo pipefail

echo "Starting Arkadia Oracle Temple..."

mkdir -p /run

# Use PORT from environment (Render sets this) or default to 8080
PORT="${PORT:-8080}"
echo "Configuration:"
echo "  GOOGLE_API_KEY:                $([ -n "${GOOGLE_API_KEY:-}" ] && echo "set (oracle + planner active)" || echo "NOT SET — Phase 7 planner will use deterministic fallback")"
echo "  GITHUB_PERSONAL_ACCESS_TOKEN:  $([ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ] && echo "set" || echo "NOT SET — corpus will only see public files")"
echo "  Starting server on port:       ${PORT}"

exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --log-level info
