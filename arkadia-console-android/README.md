# Arkadia Console

Native Android instrument for Arkadia Prism.

## Identity

Firebase Authentication is native to the app. The Console does not ask the human to paste a Firebase bearer token.

At build time provide the public Firebase application configuration through Gradle properties or environment variables:

- firebaseApiKey / FIREBASE_API_KEY
- firebaseProjectId / FIREBASE_PROJECT_ID
- firebaseAppId / FIREBASE_APP_ID
- firebaseGcmSenderId / FIREBASE_GCM_SENDER_ID (optional)

The app opens on a native Firebase sign-in / account-creation screen. The signed-in Firebase user supplies the ID token to Oracle. Oracle verifies that token server-side. The Console therefore keeps identity at the native Firebase boundary and authority at the server boundary.

## Governed action chain

The Console now exposes the existing ARK-WEAVER-01 chain rather than inventing a second approval system:

1. Solariun proposal is ACCEPTED.
2. Human presses AUTHORIZE.
3. Oracle records a HumanAuthorityEvent.
4. Oracle creates an Authorization causally bound to the enterprise proposal.
5. Console may record an ExecutionAttempt under that authorization.
6. Observed result becomes an EvidenceRecord.
7. A separate verification gesture creates a VerificationRecord.

The boundaries remain explicit:

- ACCEPTED != AUTHORIZED
- AUTHORIZED != EXECUTED
- EXECUTED != EVIDENCE
- EVIDENCE != VERIFIED

No step invents the next step's evidence.

## Backend

The native Console is pinned to the live Oracle endpoint `https://arkadia-kw64.onrender.com`. There is no backend URL prompt and no silent fallback. Changing the endpoint is a code-level deployment change, not a per-device setting.

The Android app owns device interaction, Firebase session handling, touch/capture surfaces and transport. Canonical identity, authority, execution records, evidence and verification remain server-side.

## Verification

CI builds the debug APK with JDK 17 / Gradle 8.2.

Next native gate: durable voice/camera/file capture and a real Weaver execution adapter that turns an authorized execution attempt into an actual tool invocation. Until that adapter exists, the Console records ATTEMPTED rather than claiming that a tool ran.