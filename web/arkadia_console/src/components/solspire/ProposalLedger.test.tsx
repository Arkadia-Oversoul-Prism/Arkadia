/**
 * Behavioural tests for the read-only SolSpire proposal ledger.
 *
 * The ledger is a *read* surface, so what it must get right is state honesty:
 * an empty ledger, an unbound workspace (`409`), an unlistable payload and a
 * transport failure are four different facts and must not render as each other.
 * The mounted component is the real one; only the transport hook is stubbed.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import { ProposalLedger } from "./ProposalLedger";

const mocks = vi.hoisted(() => ({
  useHydration: vi.fn(),
}));

vi.mock("../../lib/useHydration", () => ({
  useHydration: (...args: unknown[]) => mocks.useHydration(...args),
}));

vi.mock("../../lib/apiClient", () => ({
  apiRequest: vi.fn(),
  ApiError: class ApiError extends Error {},
}));

beforeEach(() => {
  mocks.useHydration.mockReset();
});

afterEach(cleanup);

function hydration(state: string, data: unknown, error: unknown = null) {
  return { state, data, error, reload: vi.fn() };
}

describe("ProposalLedger", () => {
  it("reads the served proposal collection through the registry", () => {
    mocks.useHydration.mockReturnValue(hydration("loading", null));
    render(<ProposalLedger />);
    expect(mocks.useHydration).toHaveBeenCalledWith("/solspire/proposals", expect.any(Function));
  });

  it("renders the recorded proposals without inventing a decision control", () => {
    mocks.useHydration.mockReturnValue(
      hydration("ready", {
        count: 2,
        proposals: [
          { proposal_id: "PROP-1", proposal_status: "DRAFT", objective: "Survey demand", proposal_version: 1 },
          { proposal_id: "PROP-2", proposal_status: "SUBMITTED", objective: "Price wheat", proposal_version: 3 },
        ],
      }),
    );
    render(<ProposalLedger />);
    expect(screen.getByText(/2 proposals recorded/)).toBeTruthy();
    expect(screen.getByText("Survey demand")).toBeTruthy();
    expect(screen.getByText("Price wheat")).toBeTruthy();
    expect(screen.getByText("SUBMITTED")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("states an empty ledger as empty, not as an approval", () => {
    mocks.useHydration.mockReturnValue(hydration("ready", { count: 0, proposals: [] }));
    render(<ProposalLedger />);
    expect(screen.getByText(/No proposals are recorded for this workspace/)).toBeTruthy();
    expect(screen.getByText(/An empty ledger is not an approval/)).toBeTruthy();
  });

  it("refuses an unlistable payload instead of showing an empty list", () => {
    mocks.useHydration.mockReturnValue(hydration("ready", { count: 1, unexpected: true }));
    render(<ProposalLedger />);
    expect(screen.getByText(/cannot list/)).toBeTruthy();
    expect(screen.queryByText(/No proposals are recorded/)).toBeNull();
  });

  it("renders an unbound workspace (409) as a prerequisite, not a failure", () => {
    mocks.useHydration.mockReturnValue(
      hydration("error", null, { kind: "CONFLICT", message: "Canonical workspace not found" }),
    );
    render(<ProposalLedger />);
    expect(screen.getByText(/No canonical workspace is bound/)).toBeTruthy();
    expect(screen.getByText(/not an empty ledger and not a failure/)).toBeTruthy();
  });

  it("does not render a transport failure as an empty ledger", () => {
    mocks.useHydration.mockReturnValue(
      hydration("unavailable", null, { kind: "NETWORK_ERROR", message: "Network unreachable" }),
    );
    render(<ProposalLedger />);
    expect(screen.queryByText(/No proposals are recorded/)).toBeNull();
  });
});
