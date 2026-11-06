/**
 * Disposable test identity — the console's authenticated test seam.
 *
 * ── Why this exists ──────────────────────────────────────────────────────────
 *
 * The workspace and Arkana surfaces are protected: `AuthContext` renders a
 * sign-in threshold until an identity is verified, and it deliberately has **no
 * development bypass** (see `contexts/AuthContext.tsx`). That is correct for
 * production, and it is why the AO4-01 layout regression could not be caught by
 * loading `/workspace` in a browser — the page rendered its threshold, not the
 * workspace. The first remediation measured the layout through a *stubbed*
 * identity, which proved the layout but not that the protected route renders
 * under a real authenticated session.
 *
 * This module supplies the missing half: a **disposable test identity** that
 * authenticates through the repository's *existing* seam rather than a parallel
 * auth system.
 *
 * ── The seam it uses (not a new one) ─────────────────────────────────────────
 *
 * The backend already defines a development identity path in `api/auth.py`:
 * outside `ENVIRONMENT=production`, with no `FIREBASE_SERVICE_ACCOUNT_JSON`, the
 * process runs in **dev-mode** and `get_current_user` decodes the bearer token's
 * payload *without verifying its signature* (`_decode_jwt_payload_unsafe`). That
 * is the repository's established test authentication seam — the same one
 * `tests/test_auth_deployment_posture.py` pins as the documented non-production
 * fallback. This module mints a token in exactly the shape that seam consumes.
 *
 * ── How it is gated (three independent locks) ────────────────────────────────
 *
 *   1. **Build mode.** `import.meta.env.DEV` is statically replaced by Vite. In a
 *      production build it is the literal `false`, so `TEST_IDENTITY_ENABLED`
 *      folds to `false` and every branch below is dead-code-eliminated. The
 *      bypass cannot exist in a production bundle.
 *   2. **Explicit opt-in.** `VITE_ARKADIA_TEST_IDENTITY=1` must also be set. A
 *      normal `pnpm dev` session does not set it, so the seam is inert by
 *      default even in development.
 *   3. **Backend posture.** The token only authenticates because the backend is
 *      running in dev-mode. Against a production backend (`ENVIRONMENT=production`
 *      with real credentials) the unsigned token is rejected — the seam cannot
 *      weaken production identity verification, because it never touches it.
 *
 * ── What it is NOT ───────────────────────────────────────────────────────────
 *
 *   - It is **not** real Firebase authentication. No Firebase SDK call is made,
 *     no ID token is issued, and the identity is not verified by any authority.
 *   - It is **not** a production credential. The token is unsigned and carries a
 *     `.invalid` email; it grants only what the dev-mode backend grants a guest.
 *   - It is **not** the stubbed identity the layout harness used before. That
 *     stub satisfied `useAuth`'s non-null contract without authenticating
 *     anything; this identity performs a real authenticated request and the
 *     protected route renders because the backend accepted it.
 *
 * Every surface that renders under this identity is labelled
 * `data-test-identity="test"` so a screenshot can never be mistaken for a real
 * signed-in session.
 */

/**
 * True only in a dev/test build that has explicitly opted in.
 *
 * `import.meta.env.DEV` is `false` in a production build, so this whole module
 * is inert there. The second condition makes the seam opt-in even in dev.
 */
export const TEST_IDENTITY_ENABLED: boolean =
  import.meta.env.DEV && import.meta.env.VITE_ARKADIA_TEST_IDENTITY === "1";

/** The subject the disposable identity authenticates as. */
export const TEST_IDENTITY_SUBJECT: string =
  import.meta.env.VITE_ARKADIA_TEST_IDENTITY_SUBJECT || "ao005-test-identity";

/** A human-readable label for the identity, used in the DOM banner. */
export const TEST_IDENTITY_LABEL = "DISPOSABLE TEST IDENTITY (dev-mode)";

function base64url(value: object): string {
  // `btoa` is available in the browser and in jsdom; the payload is ASCII JSON.
  return btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/**
 * Mint a token in the shape `api/auth.py`'s dev-mode decoder consumes.
 *
 * The signature segment is a literal placeholder: dev-mode never verifies it,
 * and a production backend rejects the token outright. This is deliberate — the
 * token is *incapable* of authenticating against production.
 */
export function mintTestIdentityToken(subject: string = TEST_IDENTITY_SUBJECT): string {
  const header = base64url({ alg: "none", typ: "JWT" });
  const payload = base64url({
    user_id: subject,
    sub: subject,
    email: `${subject}@test.invalid`,
    name: "AO-005 Test Identity",
    // A fixed, obviously-synthetic issued-at; the dev-mode decoder ignores it.
    iat: 0,
  });
  return `${header}.${payload}.test-identity-unsigned`;
}

/**
 * The token the console should authenticate with, or `null` when the seam is
 * disabled. An explicit `VITE_ARKADIA_TEST_IDENTITY_TOKEN` wins so a caller can
 * pin a specific subject; otherwise one is minted from the configured subject.
 */
export function testIdentityToken(): string | null {
  if (!TEST_IDENTITY_ENABLED) return null;
  return import.meta.env.VITE_ARKADIA_TEST_IDENTITY_TOKEN || mintTestIdentityToken();
}
