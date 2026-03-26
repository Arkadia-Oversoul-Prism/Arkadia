#!/usr/bin/env bash
set -euo pipefail

echo "Starting Arkadia Oracle Temple..."

mkdir -p /run

# Use PORT from environment (Render sets this) or default to 8080
PORT="${PORT:-8080}"
echo "Configuration:"
echo "  GEMINI_API_KEY: $([ -n "${GEMINI_API_KEY:-}" ] && echo "set" || echo "NOT SET — oracle will degrade gracefully")"
echo "  Starting server on port: ${PORT}"

exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT" --log-level info
