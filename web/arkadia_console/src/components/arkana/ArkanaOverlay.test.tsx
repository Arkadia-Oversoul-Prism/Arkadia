/**
 * Behavioural tests for the global Arkana overlay (ARK-UI-UNIFICATION-001, Phase C).
 *
 * These mount the **real** `ArkanaOverlay` and the **real** `Shell`. Nothing
 * asserts on source text: every claim is made against rendered DOM, against a
 * render count, or against the arguments the overlay actually passes to the
 * shared Arkana transport.
 *
 * What is pinned here, and why each matters:
 *
 *   1. **One conversational surface.** The overlay is mounted by the shell and
 *      nowhere else, and the shell suppresses its trigger on the Arkana surface
 *      (where the full-page conversation already is). A second live Arkana
 *      conversation on one screen is the exact duplication the mandate forbids.
 *   2. **Reuse, not a second engine.** A turn is streamed through
 *      `lib/arkana.streamArkana` — the same module `ArkanaPage` and
 *      `WorkspacePage` call. The test asserts the call, so a future
 *      reimplementation that bypasses the shared transport fails here.
 *   3. **Bounded context awareness.** The turn carries a preamble naming the
 *      surface and, when a project is active, the project and the counts the
 *      runtime-context contract reported — never a full-corpus dump.
 *   4. **Lifecycle.** Escape and a backdrop click close the overlay; focus moves
 *      into the composer on open; the body does not scroll behind it.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";

import { ArkanaOverlay, buildOverlayPreamble } from "./ArkanaOverlay";
import { Shell } from "../Shell";
import { SurfaceChromeProvider } from "../../lib/surfaceChrome";

const mocks = vi.hoisted(() => ({
  streamArkana: vi.fn(),
  apiRequest: vi.fn(),
  useHydration: vi.fn(),
  projectContext: { current: null as unknown },
}));

vi.mock("../../lib/arkana", () => ({
  streamArkana: (...args: unknown[]) => mocks.streamArkana(...args),
}));

vi.mock("../../lib/apiClient", () => ({
  apiRequest: (...args: unknown[]) => mocks.apiRequest(...args),
  ApiError: class ApiError extends Error {},
}));

vi.mock("../../lib/useHydration", () => ({
  useHydration: (...args: unknown[]) => mocks.useHydration(...args),
}));

vi.mock("../../contexts/AuthContext", () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

vi.mock("../../lib/projectContext", () => ({
  useOptionalProjectContext: () => mocks.projectContext.current,
}));

const READY_REPLY = {
  reply: "Hello world",
  resonance: 0,
  patterns: [],
  rag_refs: [],
  rag_hits: 0,
  sources: [],
  memory: {},
  provenance: {},
};

function projectContextValue(overrides: Record<string, unknown> = {}) {
  return {
    activeProjectId: "proj-1",
    activeProject: { id: "proj-1", name: "Mission Alpha", status: "active" },
    ...overrides,
  };
}

beforeEach(() => {
  mocks.streamArkana.mockReset();
  mocks.apiRequest.mockReset();
  mocks.useHydration.mockReset();
  mocks.projectContext.current = null;
  // The thread-history rail reads through `useHydration`; a ready empty list
  // keeps the overlay's own assertions about the thread unambiguous.
  mocks.useHydration.mockReturnValue({ state: "ready", data: { threads: [] }, error: null, reload: vi.fn() });
  mocks.apiRequest.mockResolvedValue({
    project_store: { tasks: [1, 2], files: [1], memory: [], events: [1, 2, 3] },
    binding_state: { daily_pulse: "BOUND", workload: "UNKNOWN" },
  });
});

afterEach(() => {
  cleanup();
});

describe("buildOverlayPreamble", () => {
  it("names the surface and the project, and states the bounded counts", () => {
    const preamble = buildOverlayPreamble("workspace", "Mission Alpha", "proj-1", {
      state: "partial",
      tasks: 2,
      files: 1,
      memory: 0,
      events: 3,
      unavailable: ["workload"],
    });

    expect(preamble).toContain("Surface: Workspace");
    expect(preamble).toContain("Project: Mission Alpha (proj-1)");
    expect(preamble).toContain("tasks 2");
    expect(preamble).toContain("Unavailable sources: workload");
    // It is a scope statement, not a corpus: it must not claim execution.
    expect(preamble).toContain("Do not claim to have executed");
  });

  it("states that no project is selected rather than omitting the scope", () => {
    const preamble = buildOverlayPreamble("weaver", null, null, {
      state: "idle",
      tasks: null,
      files: null,
      memory: null,
      events: null,
      unavailable: [],
    });

    expect(preamble).toContain("Surface: Weaver");
    expect(preamble).toContain("Project: none selected");
  });

  it("reports an unreadable project snapshot as unavailable, never as empty", () => {
    const preamble = buildOverlayPreamble("projects", "Mission Alpha", "proj-1", {
      state: "unavailable",
      tasks: null,
      files: null,
      memory: null,
      events: null,
      unavailable: ["runtime context"],
    });

    expect(preamble).toContain("Project snapshot: unavailable");
  });
});

describe("ArkanaOverlay lifecycle", () => {
  it("renders nothing while closed", () => {
    render(<ArkanaOverlay open={false} onClose={() => {}} surface="workspace" />);
    expect(screen.queryByTestId("arkana-overlay")).toBeNull();
  });

  it("renders a dialog naming the current surface when open", () => {
    render(<ArkanaOverlay open onClose={() => {}} surface="engineering-lab" />);

    const dialog = screen.getByTestId("arkana-overlay");
    expect(dialog.getAttribute("role")).toBe("dialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(screen.getByTestId("arkana-overlay-context-pack").textContent).toContain("Engineering Lab");
  });

  it("closes on Escape", () => {
    const onClose = vi.fn();
    render(<ArkanaOverlay open onClose={onClose} surface="workspace" />);

    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on a backdrop click", () => {
    const onClose = vi.fn();
    render(<ArkanaOverlay open onClose={onClose} surface="workspace" />);

    fireEvent.click(screen.getByTestId("arkana-overlay-backdrop"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("moves focus into the composer on open", async () => {
    render(<ArkanaOverlay open onClose={() => {}} surface="workspace" />);

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(document.activeElement).toBe(screen.getByTestId("arkana-overlay-input"));
  });

  it("locks body scroll while open and restores it on close", () => {
    const { rerender } = render(<ArkanaOverlay open onClose={() => {}} surface="workspace" />);
    expect(document.body.style.overflow).toBe("hidden");

    rerender(<ArkanaOverlay open={false} onClose={() => {}} surface="workspace" />);
    expect(document.body.style.overflow).not.toBe("hidden");
  });
});

describe("ArkanaOverlay context awareness", () => {
  it("shows the active project and its bounded snapshot in the context pack", async () => {
    mocks.projectContext.current = projectContextValue();
    render(<ArkanaOverlay open onClose={() => {}} surface="workspace" />);

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    const pack = screen.getByTestId("arkana-overlay-context-pack").textContent ?? "";
    expect(pack).toContain("Mission Alpha");
    expect(pack).toContain("TASKS 2");
    expect(pack).toContain("UNAVAILABLE · workload");
  });

  it("states that no project is selected when the context is absent", () => {
    render(<ArkanaOverlay open onClose={() => {}} surface="workspace" />);
    const pack = screen.getByTestId("arkana-overlay-context-pack").textContent ?? "";
    expect(pack).toContain("PROJECT · NONE");
  });
});

describe("ArkanaOverlay turn transport", () => {
  it("streams a turn through the shared Arkana transport and renders the reply", async () => {
    mocks.streamArkana.mockImplementation(
      async (_message: string, _history: unknown, handlers: { onDelta?: (t: string) => void }) => {
        handlers.onDelta?.("Hello ");
        handlers.onDelta?.("world");
        return READY_REPLY;
      },
    );

    render(<ArkanaOverlay open onClose={() => {}} surface="workspace" />);

    fireEvent.change(screen.getByTestId("arkana-overlay-input"), {
      target: { value: "What am I looking at?" },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("arkana-overlay-send"));
    });

    // The shared transport was used — not a second engine.
    expect(mocks.streamArkana).toHaveBeenCalledTimes(1);
    const [message, , , projectId] = mocks.streamArkana.mock.calls[0];
    expect(String(message)).toContain("ARKANA OVERLAY CONTEXT");
    expect(String(message)).toContain("What am I looking at?");
    expect(projectId).toBeUndefined();

    expect(screen.getByTestId("arkana-overlay-thread").textContent).toContain("Hello world");
  });

  it("carries the active project id into the turn", async () => {
    mocks.projectContext.current = projectContextValue();
    mocks.streamArkana.mockResolvedValue(READY_REPLY);

    render(<ArkanaOverlay open onClose={() => {}} surface="projects" />);

    fireEvent.change(screen.getByTestId("arkana-overlay-input"), { target: { value: "status?" } });
    await act(async () => {
      fireEvent.click(screen.getByTestId("arkana-overlay-send"));
    });

    const [, , , projectId] = mocks.streamArkana.mock.calls[0];
    expect(projectId).toBe("proj-1");
  });
});

describe("Shell integration — one conversational surface", () => {
  function renderShell(surface: Parameters<typeof Shell>[0]["current"]) {
    return render(
      <SurfaceChromeProvider>
        <Shell current={surface} onNavigate={() => {}}>
          <div>canvas</div>
        </Shell>
      </SurfaceChromeProvider>,
    );
  }

  it("mounts exactly one overlay and offers the trigger on a non-Arkana surface", () => {
    renderShell("workspace");

    expect(screen.getByTestId("arkana-overlay-open")).toBeTruthy();
    // Closed by default: the dialog is not in the DOM until it is opened.
    expect(screen.queryByTestId("arkana-overlay")).toBeNull();
  });

  it("suppresses the trigger on the Arkana surface so the full-page conversation is not duplicated", () => {
    renderShell("arkana");
    expect(screen.queryByTestId("arkana-overlay-open")).toBeNull();
  });

  it("opens the single overlay from the shell trigger", async () => {
    renderShell("workspace");

    await act(async () => {
      fireEvent.click(screen.getByTestId("arkana-overlay-open"));
    });

    expect(screen.getAllByTestId("arkana-overlay").length).toBe(1);
  });
});
