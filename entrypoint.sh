#!/usr/bin/env bash
set -euo pipefail

echo "Starting Arkadia Oracle Temple..."

# Create /run directory
mkdir -p /run

# If a JSON blob was provided as env, write it to /run/service_account.json
if [ -n "${GDRIVE_SERVICE_ACCOUNT_JSON:-}" ]; then
  echo "$GDRIVE_SERVICE_ACCOUNT_JSON" > /run/service_account.json
  chmod 600 /run/service_account.json
  echo "✓ Wrote Drive service account JSON to /run/service_account.json"
elif [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" ]; then
  echo "$GOOGLE_SERVICE_ACCOUNT_JSON" > /run/service_account.json
  chmod 600 /run/service_account.json
  echo "✓ Wrote Google service account JSON to /run/service_account.json"
fi

# If user provided a file pointer env, copy it into /run (optional fallback)
if [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE:-}" ] && [ -f "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE}" ]; then
  cp "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE}" /run/service_account.json
  chmod 600 /run/service_account.json
  echo "✓ Copied GOOGLE_SERVICE_ACCOUNT_JSON_FILE to /run/service_account.json"
fi

# Set default environment variables
export GOOGLE_SERVICE_ACCOUNT_JSON_FILE="/run/service_account.json"
export ARKADIA_FOLDER_ID="${ARKADIA_FOLDER_ID:-1J_2_RQWml85SQ7ZP7DwAVSbrXOHTO9fF}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-AIzaSyCGBWv8tDCevIAc1flyFKN8twx3wq9jQ-Y}"

# Display configuration
echo "Configuration:"
echo "  ARKADIA_FOLDER_ID: ${ARKADIA_FOLDER_ID}"
echo "  GEMINI_API_KEY: $([ -n "${GEMINI_API_KEY:-}" ] && echo "✓ set" || echo "✗ not set")"
echo "  SERVICE_ACCOUNT_JSON: $([ -f "/run/service_account.json" ] && echo "✓ available" || echo "✗ missing")"

# Use PORT from environment (Render sets this) or default to 8080
PORT="${PORT:-8080}"
echo "  Starting server on port: ${PORT}"

# Start the FastAPI server
exec uvicorn arkana_app:app --host 0.0.0.0 --port "$PORT" --log-level info
