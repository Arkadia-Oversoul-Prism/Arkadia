/**
 * Behavioural tests for the authenticated test-identity path in `AuthContext`.
 *
 * These mount the **real** `AuthProvider` with the disposable test-identity seam
 * enabled and a stubbed transport, and assert that the provider reaches an
 * authenticated state — i.e. that the protected surfaces would render rather
 * than their sign-in threshold.
 *
 * This is the seam the layout harness depends on: if `AuthContext` stopped
 * honouring the test identity, the authenticated layout run would silently fall
 * back to the threshold, and these tests would fail first.
 *
 * The transport is stubbed (no network); the *identity* is the real seam. This
 * is a disposable test identity, not real Firebase authentication.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

function ProfileProbe({ useAuth }: { useAuth: () => { isAuthenticated: boolean; testIdentity: boolean; identityState: string } }) {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="authed">{auth.isAuthenticated ? "yes" : "no"}</span>
      <span data-testid="test-identity">{auth.testIdentity ? "yes" : "no"}</span>
      <span data-testid="state">{auth.identityState}</span>
    </div>
  );
}

describe("AuthContext — disposable test identity", () => {
  it("reaches an authenticated state when the seam is enabled", async () => {
    vi.stubEnv("VITE_ARKADIA_TEST_IDENTITY", "1");
    // The provider hydrates the profile through the real apiClient; stub the
    // transport so the test is hermetic. The identity itself is the real seam.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            user: { uid: "ao005-test-identity", display_name: "AO-005 Test Identity", role: "Guest" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    vi.resetModules();
    const { AuthProvider, useAuth } = await import("./AuthContext");
    render(
      <AuthProvider>
        <ProfileProbe useAuth={useAuth} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("authed").textContent).toBe("yes"));
    expect(screen.getByTestId("test-identity").textContent).toBe("yes");
    expect(screen.getByTestId("state").textContent).toBe("ready");
  });

  it("does not authenticate when the seam is disabled", async () => {
    // No opt-in env var: the seam is inert, and with no Firebase config the
    // provider settles into its documented unauthenticated state.
    vi.resetModules();
    const { AuthProvider, useAuth } = await import("./AuthContext");
    render(
      <AuthProvider>
        <ProfileProbe useAuth={useAuth} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("state").textContent).not.toBe("loading"));
    expect(screen.getByTestId("authed").textContent).toBe("no");
    expect(screen.getByTestId("test-identity").textContent).toBe("no");
  });
});
