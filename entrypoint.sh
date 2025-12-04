#!/usr/bin/env bash
set -euo pipefail

# If a JSON blob was provided as env, write it to /run/service_account.json
if [ -n "${GDRIVE_SERVICE_ACCOUNT_JSON:-}" ]; then
  mkdir -p /run
  echo "$GDRIVE_SERVICE_ACCOUNT_JSON" > /run/service_account.json
  chmod 600 /run/service_account.json
  echo "Wrote Drive service account JSON to /run/service_account.json"
fi

# If user provided a file pointer env, copy it into /run (optional fallback)
if [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE:-}" ] && [ -f "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE}" ]; then
  mkdir -p /run
  cp "${GOOGLE_SERVICE_ACCOUNT_JSON_FILE}" /run/service_account.json
  chmod 600 /run/service_account.json
  echo "Copied GOOGLE_SERVICE_ACCOUNT_JSON_FILE to /run/service_account.json"
fi

echo "ARKADIA_FOLDER_ID=${ARKADIA_FOLDER_ID:-<not-set>}"
echo "GEMINI_API_KEY set? ->" && { [ -n "${GEMINI_API_KEY:-}" ] && echo "yes" || echo "no"; }

# Render supplies PORT; fallback to 5005
PORT="${PORT:-5005}"

# Start the FastAPI server
exec uvicorn arkana_app:app --host 0.0.0.0 --port "$PORT" --log-level info
