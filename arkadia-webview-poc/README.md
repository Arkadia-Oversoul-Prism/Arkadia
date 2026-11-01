# ARKADIA-ANDROID-WEBVIEW-POC-01

Isolated Android proof of concept for hosting the existing Arkadia Console in a restricted WebView.

## Scope

This project is intentionally separate from `arkadia-android/` and `sonata-android/`.
It does not replace either application and does not modify the Console frontend or backend.

- One Android Activity containing one WebView.
- Loads one build-configured HTTPS origin.
- Uses the Console's existing Firebase Web authentication and same-origin API requests.
- No JavaScript-to-native bridge, native token handling, local approval engine, or execution API.
- DOM storage and first-party cookies are enabled for the existing web authentication flow.
- Third-party cookies, file access, content access, mixed content, popups, and cleartext traffic are disabled.
- Offline/error state is explicit; reconnection triggers a reload, never a queued mutation.
- WebView cookies and local storage are not cleared by the app.

The default build origin is deliberately non-routable (`https://arkadia-poc.invalid`) so CI cannot accidentally exercise production. Supply a controlled staging origin for a test build:

```bash
gradle -PARKADIA_ORIGIN=https://arkadia-staging.example testDebugUnitTest assembleDebug
```

The Gradle property is named `arkadiaOrigin` (case-sensitive).

## Build

Requirements: JDK 17, Android SDK 34, Gradle 8.2.x.

```bash
gradle testDebugUnitTest assembleDebug
```

The PR workflow builds an unsigned debug APK and uploads it as a short-lived artifact. It does not sign, publish, deploy, or contact the configured origin.

## Verification matrix

| ID | Test | Method | Acceptance |
|---|---|---|---|
| POC-01 | Firebase session persistence | Install staging build, sign in with controlled test account, close/relaunch app | Firebase session restores without re-entering credentials, unless Firebase policy requires reauth |
| POC-02 | Token refresh | Keep session active through token refresh; inspect protected request behavior | Firebase SDK refreshes ID token; protected API request remains authenticated; no stale bearer token |
| POC-03 | Protected API | Compare signed-in and signed-out requests to a staging protected route | Signed-in request succeeds; signed-out request is rejected |
| POC-04 | Approval boundary | Attempt approval/execution as authenticated user without an approval | Backend rejects unauthorized transition/execution |
| POC-05 | Approved workflow | Use staging approval route with a human-authorized test approval | Existing backend approval gate is enforced; execution remains separate |
| POC-06 | Network recovery | Disable network during load and during a read; restore network | Offline state is visible; retry/reconnect restores the page; no mutation is replayed |
| POC-07 | Session recovery | Revoke/expire controlled test session | Protected access fails closed and Console returns to its normal auth flow |
| POC-08 | Native isolation | Inspect manifest and WebView setup | No addJavascriptInterface; exact HTTPS origin only; no file/content access |

## Evidence protocol

For each device run record: build SHA, Android version, WebView provider/version, origin hostname (never credentials), test account alias (never email/password/token), timestamp, expected result, observed result, and sanitized log excerpt.

Never attach Firebase ID tokens, cookies, passwords, full authorization headers, or private user data to evidence.

## Known constraints / non-goals

- CI compilation and JVM origin-policy tests do not prove Firebase behavior on a physical device.
- Device authentication tests require an explicitly configured staging origin and controlled test account.
- No production authentication, production approval, or production tool execution is part of this POC.
- Backend approval durability is outside the Android shell; the existing process-local approval-store risk must be assessed separately.
- No offline mutation queue or offline approval is permitted.
- No full ecosystem packaging, release signing, Play Store publication, production deployment, or merge is authorized by this POC.

## Exit gates

1. Source and JVM tests pass.
2. Debug APK builds successfully in CI.
3. Controlled Android device tests pass POC-01 through POC-08.
4. Evidence is reviewed and limitations are documented.
5. Separate human acceptance authorizes any expansion beyond this POC.
