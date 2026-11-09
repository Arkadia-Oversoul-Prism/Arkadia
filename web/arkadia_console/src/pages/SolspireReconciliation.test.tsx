/**
 * Behavioural tests for the Solariun / SolSpire lens reconciliation
 * (ARK-UI-UNIFICATION-002).
 *
 * These mount the **real** `SolariunPage` and the **real** `SolSpirePage` and
 * assert against rendered DOM and the arguments the shared lens strip actually
 * passes to the navigator. Nothing asserts on source text.
 *
 * What is pinned, and why each matters:
 *
 *   1. **One navigation system.** Both surfaces render the shared
 *      `SurfaceLenses` strip, and a lens click navigates to
 *      `<surface>/<lens-id>` through the one navigator — the strip and the
 *      address bar cannot disagree.
 *   2. **The reconciled vocabulary.** Solariun offers the archived Home cockpit
 *      (`overview`) and the `engineering-lab` / `field` lenses; SolSpire is
 *      section-addressed with the archived `field` (opportunity-radar) lens.
 *   3. **Truthful states.** A section outside the declared set renders the
 *      "not a lens" state rather than silently showing the field view.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import { SolariunPage } from "./SolariunPage";
import { SolSpirePage } from "./SolSpirePage";

const mocks = vi.hoisted(() => ({
  useHydration: vi.fn(),
  apiRequest: vi.fn(),
}));

vi.mock("../lib/useHydration", () => ({
  useHydration: (...args: unknown[]) => mocks.useHydration(...args),
}));

vi.mock("../lib/apiClient", () => ({
  apiRequest: (...args: unknown[]) => mocks.apiRequest(...args),
  ApiError: class ApiError extends Error {},
}));

vi.mock("../contexts/AuthContext", () => ({
  useAuth: () => ({ isAuthenticated: true, profile: null, identityState: "ready" }),
}));

vi.mock("../lib/projectContext", () => ({
  useProjectContext: () => ({ activeProjectId: null, selectProject: vi.fn() }),
}));

beforeEach(() => {
  mocks.useHydration.mockReset();
  mocks.apiRequest.mockReset();
  // Path-aware: the project list is ready and empty (so the surfaces' own
  // assertions are unambiguous); every other read stays in a non-ready state so
  // the control-plane and field panels render their contract state, not data.
  mocks.useHydration.mockImplementation((path: string) => {
    if (path === "/solspire/projects") {
      return { state: "ready", data: { count: 0, projects: [] }, error: null, reload: vi.fn() };
    }
    return { state: "loading", data: null, error: null, reload: vi.fn() };
  });
});

afterEach(() => {
  cleanup();
});

describe("SolariunPage — reconciled lens strip", () => {
  it("renders the shared lens strip with the reconciled vocabulary", () => {
    render(<SolariunPage section="overview" onNavigate={() => {}} />);

    const strip = screen.getByTestId("solariun-lenses");
    expect(strip.tagName).toBe("NAV");
    for (const lens of ["overview", "projects", "knowledge", "memory", "weaver", "engineering-lab", "field"]) {
      expect(screen.getByTestId(`surface-lens-${lens}`)).toBeTruthy();
    }
  });

  it("navigates to the lens's own section through the one navigator", () => {
    const onNavigate = vi.fn();
    render(<SolariunPage section="overview" onNavigate={onNavigate} />);

    fireEvent.click(screen.getByTestId("surface-lens-engineering-lab"));
    expect(onNavigate).toHaveBeenCalledWith("solariun", "engineering-lab");
  });

  it("marks the current lens as the current page", () => {
    render(<SolariunPage section="field" onNavigate={() => {}} />);
    expect(screen.getByTestId("surface-lens-field").getAttribute("aria-current")).toBe("page");
  });

  it("renders the overview cockpit on the overview lens", () => {
    render(<SolariunPage section="overview" onNavigate={() => {}} />);
    expect(screen.getByTestId("solariun-overview")).toBeTruthy();
  });

  it("states that a section outside the declared set is not a lens", () => {
    render(<SolariunPage section="bogus" onNavigate={() => {}} />);
    expect(screen.getByText(/is not a lens of this surface/)).toBeTruthy();
  });
});

describe("SolSpirePage — section-addressed field surface", () => {
  it("renders the shared lens strip with the field vocabulary", () => {
    render(<SolSpirePage section="field" onNavigate={() => {}} />);

    const strip = screen.getByTestId("solspire-lenses");
    expect(strip.tagName).toBe("NAV");
    for (const lens of ["field", "enterprise", "voice", "proposals"]) {
      expect(screen.getByTestId(`surface-lens-${lens}`)).toBeTruthy();
    }
  });

  it("navigates to the lens's own section through the one navigator", () => {
    const onNavigate = vi.fn();
    render(<SolSpirePage section="field" onNavigate={onNavigate} />);

    fireEvent.click(screen.getByTestId("surface-lens-enterprise"));
    expect(onNavigate).toHaveBeenCalledWith("solspire", "enterprise");
  });

  it("states that a section outside the declared set is not a lens", () => {
    render(<SolSpirePage section="bogus" onNavigate={() => {}} />);
    expect(screen.getByText(/is not a lens of this surface/)).toBeTruthy();
  });
});
