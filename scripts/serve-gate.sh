#!/usr/bin/env bash
# Serve the repository root and open the Gate UI in the default browser.
# Usage: ./scripts/serve-gate.sh [PORT]
PORT=${1:-8000}
python -m http.server ${PORT} &
SERVER_PID=$!
# give server a moment to start
sleep 0.5
URL="http://localhost:${PORT}/gate/"
# Try to open in the default browser, fall back to xdg-open
if [ -n "$BROWSER" ]; then
  "$BROWSER" "$URL" || xdg-open "$URL" || open "$URL" || true
else
  xdg-open "$URL" || open "$URL" || true
fi
# Wait for server process to exit (Ctrl-C to stop)
wait ${SERVER_PID}
