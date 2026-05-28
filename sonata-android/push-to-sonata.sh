#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# push-to-sonata.sh
# Initialises a git repo inside sonata-android/ and pushes it to the
# Arkadia-Oversoul-Prism/sonata GitHub repository.
#
# Usage:
#   cd /path/to/arkadia-workspace
#   GITHUB_TOKEN=ghp_xxx bash sonata-android/push-to-sonata.sh
#
# The GITHUB_TOKEN must have push access to Arkadia-Oversoul-Prism/sonata.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REMOTE="https://${GITHUB_TOKEN}@github.com/Arkadia-Oversoul-Prism/sonata.git"
BRANCH="feature/sonata-tts-app"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Sonata Android → GitHub push ==="
echo "Directory : $DIR"
echo "Remote    : Arkadia-Oversoul-Prism/sonata"
echo "Branch    : $BRANCH"
echo ""

cd "$DIR"

if [ ! -d ".git" ]; then
  git init
  git remote add origin "$REMOTE"
fi

# Try to fetch + rebase onto existing remote branch
if git fetch origin "$BRANCH" 2>/dev/null; then
  git checkout -B "$BRANCH" "origin/$BRANCH"
else
  git checkout -B "$BRANCH"
fi

# Copy files if running from parent directory
# (The script lives inside sonata-android/, so files are already here)

git add -A
git config user.email "arkadia@build.ci"
git config user.name  "Arkadia Build"
git commit -m "feat(sonata): Android TTS app — PROCESS_TEXT, overlay, foreground service, CI pipeline

- ProcessTextActivity: PROCESS_TEXT intent → 'Speak with Sonata' in every app's text menu
- FloatingOverlayService: draggable black-glass overlay (play/pause/stop/speed/close)
- SpeechService: foreground service with MediaSession notification controls
- TtsEngine: tier-1 Arkadia neural voice (Edge TTS via /api/tts), tier-2 Android TTS offline
- SettingsActivity: voice, speed, pitch, auto-read, backend URL, cache management
- Prefs: SharedPreferences wrapper with typed accessors
- SonataApp: notification channel setup on startup
- .github/workflows/build-apk.yml: CI builds signed release APK on every push
- Min SDK 29 (Android 10), target SDK 34
" 2>/dev/null || echo "(nothing to commit)"

git push -u origin "$BRANCH" --force-with-lease 2>/dev/null || \
  git push -u origin "$BRANCH" --force

echo ""
echo "✓ Pushed to Arkadia-Oversoul-Prism/sonata @ $BRANCH"
echo "  GitHub Actions will now build the APK automatically."
echo ""
echo "  To enable signed releases, add these secrets to the repo:"
echo "    SIGNING_KEY        — base64 of your .jks keystore"
echo "    KEY_ALIAS          — key alias inside the keystore"
echo "    KEY_STORE_PASSWORD — keystore password"
echo "    KEY_PASSWORD       — key password"
echo ""
echo "  Generate a keystore (run once):"
echo "    keytool -genkey -v -keystore sonata-release.jks \\"
echo "      -alias sonata -keyalg RSA -keysize 2048 -validity 10000"
