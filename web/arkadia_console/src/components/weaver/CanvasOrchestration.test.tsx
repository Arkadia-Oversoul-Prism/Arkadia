import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { useHydration } from "../../lib/useHydration";
import { CanvasOrchestration } from "./CanvasOrchestration";

vi.mock("../../contexts/AuthContext", () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

vi.mock("../../lib/useHydration", () => ({
  useHydration: vi.fn(),
}));

vi.mock("../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
}));

const hydration = vi.mocked(useHydration);
const reload = vi.fn();

function setHydration(state: string, data: unknown, error: unknown = null) {
  hydration.mockReturnValue({ state, data, error, reload } as never);
}

function canvasPayload(empty = false): unknown {
  return {
    read_only: true,
    surfaces: ["engineering-lab", "arkana", "weaver"],
    sections: {
      "engineering-lab": {
        contract: "/api/lab/engineering/overview",
        sessions: empty ? [] : [{ session_id: "session-1", state: "READY_FOR_REVIEW" }],
      },
      arkana: {
        contract: "/api/commune/threads",
        threads: empty ? [] : [{ uuid: "thread-1", title: "Mission notes" }],
        count: empty ? 0 : 1,
      },
      weaver: {
        contract: "/api/lab/engineering/sessions",
        sessions: empty ? [] : [{ session_id: "session-1", state: "READY_FOR_REVIEW" }],
        runs: empty ? [] : [{ run_id: "run-1", state: "READY_FOR_REVIEW" }],
        orchestration: {
          dependencies: empty ? [] : [{ from: "run-0", to: "run-1" }],
          subtasks: empty
            ? []
            : [
                {
                  run_id: "run-1",
                  id: "SUB-1",
                  kind: "read",
                  target: "README.md",
                  state: "SUCCEEDED",
                  description: "inspect repository entry point",
                },
              ],
          retries: empty
            ? []
            : [
                {
                  run_id: "run-1",
                  attempt: 1,
                  retryable: false,
                  retry_policy: "AEAS-5/REVISION_REQUIRED:terminal",
                },
              ],
          poll: {
            mode: "poll",
            cursor_field: "updated_at",
            updated_at: empty ? null : "2026-11-08T08:00:00Z",
            note: "No SSE/WebSocket orchestration transport is served.",
          },
        },
      },
    },
  };
}

describe("CanvasOrchestration", () => {
  beforeEach(() => {
    hydration.mockReset();
    reload.mockReset();
  });

  it("renders server-reported cross-surface counts and orchestration records", () => {
    setHydration("ready", canvasPayload());
    render(<CanvasOrchestration />);

    expect(screen.getByTestId("weaver-canvas-surface-engineering-lab").textContent).toContain("1");
    expect(screen.getByTestId("weaver-canvas-surface-arkana").textContent).toContain("1");
    expect(screen.getByTestId("weaver-canvas-surface-weaver").textContent).toContain("1");
    expect(screen.getByTestId("weaver-canvas-dependencies").textContent).toContain("run-0");
    expect(screen.getByTestId("weaver-canvas-dependencies").textContent).toContain("run-1");
    expect(screen.getByTestId("weaver-canvas-subtasks").textContent).toContain("read · README.md");
    expect(screen.getByTestId("weaver-canvas-retries").textContent).toContain("Not retryable");
    expect(screen.getByTestId("weaver-canvas-retries").textContent).toContain(
      "AEAS-5/REVISION_REQUIRED:terminal",
    );

    fireEvent.click(screen.getByTestId("weaver-canvas-refresh"));
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("renders valid empty collections as zero, not as unavailable", () => {
    setHydration("ready", canvasPayload(true));
    render(<CanvasOrchestration />);

    expect(screen.getByTestId("weaver-canvas-surface-arkana").textContent).toContain("0");
    expect(screen.getByText("No dependency edges recorded.")).toBeTruthy();
    expect(screen.getByText("No operation subtasks recorded.")).toBeTruthy();
    expect(screen.getByText("No retry decisions recorded.")).toBeTruthy();
    expect(screen.getByText(/Latest session\/run update: No timestamp supplied/)).toBeTruthy();
    expect(screen.queryByTestId("weaver-canvas-unknown")).toBeNull();
  });

  it("marks a malformed canvas UNKNOWN instead of inferring empty collections", () => {
    const malformed = JSON.parse(JSON.stringify(canvasPayload())) as {
      sections: { weaver: { orchestration: Record<string, unknown> } };
    };
    delete malformed.sections.weaver.orchestration.dependencies;
    setHydration("ready", malformed);
    render(<CanvasOrchestration />);

    expect(screen.getByTestId("weaver-canvas-unknown")).toBeTruthy();
    expect(screen.queryByTestId("weaver-canvas-orchestration")).toBeNull();
  });

  it("keeps transport failure distinct from a valid empty response", () => {
    setHydration("unavailable", null, { message: "network unavailable" });
    render(<CanvasOrchestration />);

    expect(screen.getByText("Backend unavailable")).toBeTruthy();
    expect(screen.getByText(/this is not an empty result/)).toBeTruthy();
    expect(screen.queryByTestId("weaver-canvas-readout")).toBeNull();
  });
});
