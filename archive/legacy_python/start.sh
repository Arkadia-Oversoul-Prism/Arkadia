#!/usr/bin/env bash
set -e

# Optional: display environment info for debugging
echo "Starting Arkadia Console..."
echo "GEMINI_API_KEY set? ->" [ -n "$GEMINI_API_KEY" ] && echo "yes" || echo "no"
echo "ARKADIA_FOLDER_ID=$ARKADIA_FOLDER_ID"

# Run the console
python arkadia_console.py
