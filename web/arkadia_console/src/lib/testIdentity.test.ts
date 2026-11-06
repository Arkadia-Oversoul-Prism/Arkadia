/**
 * Behavioural tests for the disposable test-identity seam (AO4-05/06).
 *
 * These assert the *gating* and the *token shape* — the two properties that make
 * the seam safe. They are behavioural, not source-text: the token is decoded and
 * its claims checked, and the enablement flag is read from the real module under
 * a controlled environment.
 *
 * The seam must be:
 *   - inert by default (no opt-in env var) — so a normal dev session is unaffected;
 *   - enabled only when `VITE_ARKADIA_TEST_IDENTITY=1`;
 *   - minting a token in the exact shape `api/auth.py`'s dev-mode decoder reads.
 *
 * The production-build elimination (`import.meta.env.DEV` folding to `false`) is
 * verified by the build scan in CI, not here — a jsdom test cannot observe a
 * production bundle.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

function decodePayload(token: string): Record<string, unknown> {
  const part = token.split(".")[1];
  const padded = part.replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(padded));
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("disposable test identity", () => {
  it("is disabled by default — no opt-in env var", async () => {
    vi.resetModules();
    const mod = await import("./testIdentity");
    expect(mod.TEST_IDENTITY_ENABLED).toBe(false);
    // With the seam disabled there is no token to authenticate with.
    expect(mod.testIdentityToken()).toBeNull();
  });

  it("mints a token in the shape api/auth.py's dev-mode decoder reads", async () => {
    vi.resetModules();
    const mod = await import("./testIdentity");
    const token = mod.mintTestIdentityToken("subject-x");

    const parts = token.split(".");
    expect(parts).toHaveLength(3);

    const payload = decodePayload(token);
    // `get_current_user` reads `user_id` or `sub`; both must be present.
    expect(payload.sub).toBe("subject-x");
    expect(payload.user_id).toBe("subject-x");
    // A `.invalid` address: the identity is obviously synthetic and unroutable.
    expect(String(payload.email)).toContain("@test.invalid");
  });

  it("enables only when VITE_ARKADIA_TEST_IDENTITY=1", async () => {
    vi.stubEnv("VITE_ARKADIA_TEST_IDENTITY", "1");
    vi.resetModules();
    const mod = await import("./testIdentity");
    expect(mod.TEST_IDENTITY_ENABLED).toBe(true);
    const token = mod.testIdentityToken();
    expect(token).toBeTruthy();
    expect(decodePayload(token as string).sub).toBe(mod.TEST_IDENTITY_SUBJECT);
  });

  it("does not enable on any other value", async () => {
    vi.stubEnv("VITE_ARKADIA_TEST_IDENTITY", "true");
    vi.resetModules();
    const mod = await import("./testIdentity");
    // Only the exact string "1" opts in — "true"/"yes" must not.
    expect(mod.TEST_IDENTITY_ENABLED).toBe(false);
  });
});
