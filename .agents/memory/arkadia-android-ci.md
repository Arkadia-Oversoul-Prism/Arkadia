---
name: Arkadia Android CI diagnosis
description: How the arkadia-android APK build was diagnosed without repo-admin log access, and the real blocker found.
---

## Architecture
`arkadia-android/` is a WebView shell (Kotlin) that loads the Prism React frontend + Oracle Temple API at a
configurable URL (`Prefs.arkadiaUrl`, default `http://10.0.2.2:5000` for emulator). It deliberately does NOT
reimplement the UI natively — the backend/frontend are "the system", the app is just "the surface". This
satisfies "must run the full backend and current frontend" without a separate Expo/Flutter rebuild.
`sonata-android/` is a separate, unrelated native Kotlin app (TTS reader) that already builds successfully in
the same CI workflow — useful as a working reference when diagnosing arkadia-android build failures.

## Diagnosing GitHub Actions failures without admin/log access
The GitHub Actions log-download API (`/actions/jobs/{id}/logs`) returns 403 "Must have admin rights" even for
public repos, and check-run annotations only surface generic `Process completed with exit code 1` unless the
workflow explicitly writes detail to `$GITHUB_STEP_SUMMARY` (which IS publicly viewable without login, unlike
raw logs). **How to apply:** when a CI step might fail and you don't have repo-admin GitHub auth, add an
`if: failure()` step that tees command output to a file and appends `tail -n 150` of it to
`$GITHUB_STEP_SUMMARY` — this becomes visible via the public run/job page without needing a token.

## Push rejected: root cause was NOT code
`gitPush()` failed with generic `PUSH_REJECTED` on every branch tried (including a brand-new throwaway
branch with trivial content), while the target repo confirmed unprotected via the branches API. That
ruled out non-fast-forward, branch protection, and secret-scanning as causes. **Why:** a repo-write
permission/credential problem with the Replit↔GitHub git connection itself blocks ALL pushes regardless of
branch or diff content — this is diagnosable by testing push to a disposable branch. **How to apply:** if
`gitPush` rejects an ordinary fast-forward push to an unprotected branch, don't keep retrying with code
changes — tell the user to reconnect/re-authorize GitHub for git operations in Replit account settings.
