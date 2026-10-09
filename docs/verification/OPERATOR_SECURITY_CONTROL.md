# Operator Security Verification Control

## Purpose

Provide a read-only, sovereign-authorized runtime attestation for the live Arkadia API. The endpoint reports only safe booleans and a correlation ID. It never returns environment-variable contents, Firebase credentials, tokens, UIDs, emails, or exception strings.

## Endpoint

`GET /api/operator/security-verification`

- No bearer token: expected HTTP 401.
- Invalid/unsigned token in production: expected HTTP 401.
- Valid Firebase identity without sovereign authorization: expected HTTP 403.
- Valid Firebase identity with sovereign authorization: expected HTTP 200 and a server-side verification record.

## Server-side checks

The endpoint records:
- whether the runtime declares `ENVIRONMENT=production`;
- whether Firebase Admin is initialized and the application is not in dev mode;
- whether the current identity passed Firebase verification (derived from production mode and the verified request identity);
- whether the current identity passed the sovereign authorization dependency.

The endpoint is read-only. It does not change configuration, restart services, mutate identity claims, or call external providers.

## Evidence and redaction

Each authenticated invocation emits one structured `[OPERATOR_SECURITY_VERIFICATION]` log record containing a random run ID, overall result, and check booleans. The caller identity and all request headers are excluded. The JSON response uses `Cache-Control: no-store`.

## Acceptance

1. Anonymous request returns 401.
2. Malformed/unsigned bearer token returns 401.
3. A Firebase-authenticated non-sovereign identity returns 403.
4. A Firebase-authenticated sovereign receives 200 with all checks PASS only when the live process is in production mode and Firebase Admin is initialized.
5. The log record contains no credential, token, UID, email, or secret value.
6. The console must use the signed-in Arkadia Firebase token provider. The standalone reconciled console currently mints a dev-only unsigned token and must not be treated as an authenticated production client until that integration is completed.
