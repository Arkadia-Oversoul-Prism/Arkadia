#!/bin/bash
# Arkadia / SolSpire post-merge setup.
# Runs after a task agent's changes are merged into main. Must be:
#   • idempotent (safe to run repeatedly)
#   • non-interactive (stdin is closed)
#   • fast (configured timeout is 20s)
#
# This project uses:
#   • Python backend (api/) — deps live in .pythonlibs, no install needed per merge
#   • Vite frontend (web/public_prism/) — npm deps
#   • Telegram bot (bot/) — npm deps
#   • JSON file storage (data/) — no migrations
set -euo pipefail

echo "post-merge: ensuring data directories exist"
mkdir -p data
mkdir -p .local/tasks

# Install frontend deps only when package.json or lockfile changed in the
# last merge commit. Avoids a 10-15s npm install on every merge.
if [ -f web/public_prism/package.json ]; then
  if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -qE '^web/public_prism/(package\.json|package-lock\.json)$'; then
    echo "post-merge: web/public_prism deps changed — installing"
    (cd web/public_prism && npm install --no-audit --no-fund --prefer-offline) || echo "post-merge: WARN frontend npm install failed (non-fatal)"
  else
    echo "post-merge: web/public_prism deps unchanged — skipping install"
  fi
fi

# Same logic for the Telegram bot.
if [ -f bot/package.json ]; then
  if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -qE '^bot/(package\.json|package-lock\.json)$'; then
    echo "post-merge: bot deps changed — installing"
    (cd bot && npm install --no-audit --no-fund --prefer-offline) || echo "post-merge: WARN bot npm install failed (non-fatal)"
  else
    echo "post-merge: bot deps unchanged — skipping install"
  fi
fi

echo "post-merge: done"
