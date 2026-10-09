# Operator Security Verification Control

## Purpose

Provide a read-only, sovereign-authorized runtime attestation for the live Arkadia API. The endpoint reports safe check statuses and a correlation ID. It never returns environment-variable contents, Firebase credentials, bearer tokens, UIDs, emails, or raw exception strings.

## Endpoint

`GET /api/operator/security-verification`

- No bearer token: expected HTTP 401.
- Invalid/unsigned token in production: expected HTTP 401.
- Valid Firebase identity without sovereign authorization: expected HTTP 403.
- Valid Firebase identity with sovereign authorization: expected HTTP 200 and a server-side verification record.

## Server-side checks

The endpoint checks:
- whether the running process declares `ENVIRONMENT=production`;
- whether Firebase Admin is initialized and the application is not in dev mode;
- whether the exact request bearer token is accepted by the Firebase Admin verifier and its verified UID matches the user profile resolved by the authorization dependency;
- whether the resolved identity has sovereign access level (at least 3).

The endpoint is read-only. It does not change configuration, restart services, mutate identity claims, or call external providers.

## Evidence and redaction

Each successful sovereign invocation emits one `[OPERATOR_SECURITY_VERIFICATION]` log record containing a random run ID, overall result, and boolean check outcomes. Caller identity, bearer token material, request headers, and raw exceptions are excluded. The JSON response uses `Cache-Control: no-store`.

Unauthorized requests are rejected by the shared authorization dependency before the attestation handler runs. They are expected to appear in Render request logs by status/path, not as attestation records with a run ID.

## Operator console behavior

The console runs three probes: no authorization header (expect 401), a deliberately invalid bearer token (expect 401), and the current same-origin Arkadia session. It reads the canonical `arkadia_token` storage value dynamically; this value is untrusted input and production acceptance still depends on Firebase Admin verification. The console never displays or logs the token.

Run the third probe in two real sessions:
1. A valid Firebase test identity with access level below 3, selecting **non-sovereign**. Expected result: 403.
2. The authorized sovereign Firebase session, selecting **sovereign**. Expected result: 200 and all server checks PASS.

The selector states the expected outcome only; it does not create, impersonate, or grant an identity. Do not paste tokens into chat or logs.

## Acceptance

1. Anonymous request returns 401.
2. Invalid bearer token returns 401.
3. A Firebase-authenticated non-sovereign identity returns 403.
4. A Firebase-authenticated sovereign receives 200 with all checks PASS only when the live process is in production mode and Firebase Admin is initialized.
5. The displayed run ID matches exactly one Render application log record.
6. The correlated record contains only the run ID, overall result, and booleans. Confirm it contains no credential, token, UID, email, or secret value.
7. Do not mark production acceptance PASS until live evidence for all four authorization outcomes and the redacted log correlation is recorded.
