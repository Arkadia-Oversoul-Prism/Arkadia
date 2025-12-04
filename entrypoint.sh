#!/usr/bin/env bash
set -euo pipefail

# If GOOGLE_SERVICE_ACCOUNT_JSON env var set, write it to /run/service_account.json
if [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" ]; then
  echo "Writing service account JSON to /run/service_account.json"
  mkdir -p /run
  printf "%s" "$GOOGLE_SERVICE_ACCOUNT_JSON" > /run/service_account.json
  chmod 600 /run/service_account.json
  export GOOGLE_SERVICE_ACCOUNT_JSON_FILE="/run/service_account.json"
fi

# Echo a short status (no secrets)
echo "ARKADIA_FOLDER_ID=${ARKADIA_FOLDER_ID:-<not-set>}"
echo "GOOGLE_SERVICE_ACCOUNT_JSON_FILE=${GOOGLE_SERVICE_ACCOUNT_JSON_FILE:-<not-set>}"
echo "GEMINI_API_KEY set? ->" [ -n "${GEMINI_API_KEY:-}" ] && echo "yes" || echo "no"

# Start the app (change if your run command differs)
exec python arkadia_console.py
