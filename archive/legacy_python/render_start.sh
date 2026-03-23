#!/usr/bin/env bash
set -euo pipefail

if [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" ]; then
  echo "Writing GOOGLE_SERVICE_ACCOUNT_JSON -> /tmp/service_account.json"
  printf "%s" "$GOOGLE_SERVICE_ACCOUNT_JSON" > /tmp/service_account.json
  chmod 600 /tmp/service_account.json
  export GOOGLE_SERVICE_ACCOUNT_JSON_FILE="/tmp/service_account.json"
fi

echo "ARKADIA_FOLDER_ID=${ARKADIA_FOLDER_ID:-<not-set>}"
echo "GOOGLE_SERVICE_ACCOUNT_JSON_FILE=${GOOGLE_SERVICE_ACCOUNT_JSON_FILE:-<not-set>}"
echo "GEMINI_API_KEY set? ->" [ -n "${GEMINI_API_KEY:-}" ] && echo "yes" || echo "no"

exec python arkadia_console.py
