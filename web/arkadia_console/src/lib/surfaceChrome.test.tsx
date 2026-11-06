/**
 * Behavioural tests for surface chrome publication (AO4-01 runtime).
 *
 * These mount the **real** `surfaceChrome` module and the **real** `Shell`
 * component. Nothing here asserts on source text: every claim is made against
 * rendered DOM or against a render counter, because the defect being guarded
 * against was a runtime update loop that a source-text guard cannot see.
 *
 * ── The defect these tests were written against ──────────────────────────────
 *
 * The previous implementation published from an effect that depended on the
 * whole context object:
 *
 *     const value = useMemo(() => ({ chrome, publish, clear }), [chrome, ...]);
 *     useEffect(() => {
 *       context.publish({ rail, railLabel, status });
 *       return () => context.clear();
 *     }, [context, rail, railLabel, status]);
 *
 * `publish` set `chrome`, which changed `value`, which re-ran the effect, which
 * published again — an unbounded loop. `clear()` also had no owner, so a
 * departing surface's cleanup could erase the arriving surface's chrome.
 *
 * Each test below therefore fails against that implementation:
 *   - "settles" tests exceed the render bound (the loop never settles);
 *   - the navigation test loses the new rail (old cleanup clears it);
 *   - the dedupe test sees a second publication for an identical value.
 *
 * The render bound is justified rather than arbitrary: a correct mount of
 * `Surface` + `Shell` needs one render for the initial state and one for the
 * publication to land (plus one more if React batches the provider update
 * separately). `MAX_SETTLED_RENDERS` allows generous headroom over that — it is
 * a *loop* detector, not a performance assertion, so it is set well above the
 * real count and far below the thousands a loop produces.
 */
import { afterAll, describe, expect, it } from "vitest";
import { act, render, screen, cleanup } from "@testing-library/react";
import { useRef, type ReactNode } from "react";

import {
  SurfaceChromeProvider,
  usePublishedChrome,
  useSurfaceChrome,
  type SurfaceChrome,
} from "./surfaceChrome";
import { Shell } from "../components/Shell";
import { AuthProvider } from "../contexts/AuthContext";

/**
 * A correct mount settles in ~2-4 renders. A loop produces thousands within the
 * same tick. 40 is comfortably above the former and far below the latter.
 */
const MAX_SETTLED_RENDERS = 40;

/** Counts renders of the component that publishes chrome. */
function useRenderCount() {
  const count = useRef(0);
  count.current += 1;
  return count;
}

/**
 * A minimal surface: publishes whatever chrome it is given, and counts its own
 * renders so a loop is observable.
 */
function Surface({
  chrome,
  onRender,
  children,
}: {
  chrome: SurfaceChrome;
  onRender?: (n: number) => void;
  children?: ReactNode;
}) {
  const renders = useRenderCount();
  onRender?.(renders.current);
  useSurfaceChrome(chrome);
  return <div data-testid="surface-body">{children}</div>;
}

/** Reads the published chrome as the shell would. */
function ChromeProbe() {
  const chrome = usePublishedChrome();
  return (
    <div>
      <span data-testid="probe-label">{chrome.railLabel}</span>
      <span data-testid="probe-status">{chrome.status ?? "—"}</span>
      <span data-testid="probe-has-rail">{chrome.rail ? "yes" : "no"}</span>
    </div>
  );
}

function renderInProvider(ui: ReactNode) {
  return render(<SurfaceChromeProvider>{ui}</SurfaceChromeProvider>);
}

/**
 * The real `Shell` reads identity through `useAuth`, so it must be mounted
 * inside the real `AuthProvider`. With no Firebase configuration present the
 * provider settles into its documented unauthenticated state — that is the
 * honest state for a test, and it is enough to render the shell's chrome.
 */
function renderShell(ui: ReactNode) {
  return render(
    <AuthProvider>
      <SurfaceChromeProvider>{ui}</SurfaceChromeProvider>
    </AuthProvider>,
  );
}

describe("surface chrome publication", () => {
  it("mounts with a published rail and exposes it to the shell", () => {
    renderInProvider(
      <>
        <Surface
          chrome={{ rail: <nav aria-label="Projects rail">rail</nav>, railLabel: "Workspace orientation", status: "ready" }}
        />
        <ChromeProbe />
      </>,
    );

    expect(screen.getByTestId("probe-has-rail").textContent).toBe("yes");
    expect(screen.getByTestId("probe-label").textContent).toBe("Workspace orientation");
    expect(screen.getByTestId("probe-status").textContent).toBe("ready");
  });

  it("delivers the rail into the real global Shell", () => {
    renderShell(
      <>
        <Surface
          chrome={{
            rail: <nav aria-label="Projects rail">PROJECTS_RAIL_MARKER</nav>,
            railLabel: "Workspace orientation",
            status: "Arkana · Solariun canvas",
          }}
        />
        <Shell current="workspace" onNavigate={() => {}}>
          <div>canvas</div>
        </Shell>
      </>,
    );

    // The shell renders the published rail in exactly one region...
    const rail = screen.getByTestId("shell-surface-rail");
    expect(rail).toBeTruthy();
    expect(rail.textContent).toContain("PROJECTS_RAIL_MARKER");
    // ...with the surface's accessible name, not a hardcoded one.
    expect(rail.querySelector("aside")?.getAttribute("aria-label")).toBe("Workspace orientation");
    // ...and the status line reaches the header.
    expect(screen.getByTestId("shell-surface-status").textContent).toBe("Arkana · Solariun canvas");
  });

  it("settles: ordinary re-renders do not loop", () => {
    let renders = 0;
    const { rerender } = renderInProvider(
      <Surface
        chrome={{ rail: <nav>rail</nav>, railLabel: "Context", status: "idle" }}
        onRender={(n) => {
          renders = n;
        }}
      />,
    );

    // Force several ordinary re-renders of the tree.
    for (let i = 0; i < 5; i += 1) {
      rerender(
        <SurfaceChromeProvider>
          <Surface
            chrome={{ rail: <nav>rail</nav>, railLabel: "Context", status: "idle" }}
            onRender={(n) => {
              renders = n;
            }}
          />
        </SurfaceChromeProvider>,
      );
    }

    expect(renders).toBeLessThan(MAX_SETTLED_RENDERS);
  });

  it("republishes when the rail content actually changes", () => {
    const { rerender } = renderInProvider(
      <>
        <Surface chrome={{ rail: <nav>first</nav>, railLabel: "Context", status: "idle" }} />
        <ChromeProbe />
      </>,
    );
    expect(screen.getByTestId("probe-has-rail").textContent).toBe("yes");

    rerender(
      <SurfaceChromeProvider>
        <Surface chrome={{ rail: null, railLabel: "Context", status: "idle" }} />
        <ChromeProbe />
      </SurfaceChromeProvider>,
    );

    // A genuine content change must land — dedupe must not swallow it.
    expect(screen.getByTestId("probe-has-rail").textContent).toBe("no");
  });

  it("does not republish an unchanged value (no duplicate publication)", () => {
    // A stable rail node, so the only thing that changes across re-renders is
    // the *object literal* the surface passes in — which is exactly the case
    // that must not produce a new publication.
    const stableRail = <nav>stable</nav>;

    // Record the identity of every published chrome value the probe observes.
    const seen: SurfaceChrome[] = [];
    function RecordingProbe() {
      const chrome = usePublishedChrome();
      if (seen[seen.length - 1] !== chrome) seen.push(chrome);
      return null;
    }

    function SpySurface() {
      useSurfaceChrome({ rail: stableRail, railLabel: "Context", status: "idle" });
      return null;
    }

    const { rerender } = renderInProvider(
      <>
        <SpySurface />
        <RecordingProbe />
      </>,
    );
    const afterMount = seen.length;

    // Re-render three times with a fresh object literal but identical content.
    for (let i = 0; i < 3; i += 1) {
      rerender(
        <SurfaceChromeProvider>
          <SpySurface />
          <RecordingProbe />
        </SurfaceChromeProvider>,
      );
    }

    // Dedupe means the published *value* never changed identity after the
    // publication landed: no second publication was pushed through context.
    // (The probe still re-renders because its parent re-rendered — that is
    // React, not a publication.) `afterMount` is 2 because the probe observes
    // the initial empty value and then the published one; the assertion that
    // matters is that the three re-renders added nothing.
    expect(seen.length).toBe(afterMount);
    expect(seen.length).toBe(2);
  });

  it("navigation: the outgoing surface's cleanup does not erase the new chrome", () => {
    function Harness({ active }: { active: "a" | "b" }) {
      return (
        <SurfaceChromeProvider>
          {active === "a" ? (
            <Surface
              chrome={{ rail: <nav>RAIL_A</nav>, railLabel: "Surface A", status: "a" }}
            />
          ) : (
            <Surface
              chrome={{ rail: <nav>RAIL_B</nav>, railLabel: "Surface B", status: "b" }}
            />
          )}
          <ChromeProbe />
        </SurfaceChromeProvider>
      );
    }

    const { rerender } = render(<Harness active="a" />);
    expect(screen.getByTestId("probe-label").textContent).toBe("Surface A");

    // Navigate: A unmounts (its cleanup runs) and B mounts in the same commit.
    act(() => {
      rerender(<Harness active="b" />);
    });

    // B's chrome must survive A's cleanup.
    expect(screen.getByTestId("probe-label").textContent).toBe("Surface B");
    expect(screen.getByTestId("probe-status").textContent).toBe("b");
    expect(screen.getByTestId("probe-has-rail").textContent).toBe("yes");
  });

  it("unmount clears the active publisher's chrome", () => {
    function Harness({ show }: { show: boolean }) {
      return (
        <SurfaceChromeProvider>
          {show ? (
            <Surface chrome={{ rail: <nav>rail</nav>, railLabel: "Context", status: "live" }} />
          ) : null}
          <ChromeProbe />
        </SurfaceChromeProvider>
      );
    }

    const { rerender } = render(<Harness show />);
    expect(screen.getByTestId("probe-has-rail").textContent).toBe("yes");

    act(() => {
      rerender(<Harness show={false} />);
    });

    // The surface is gone, so its rail must be gone too — a stale rail must
    // never outlive the surface that contributed it.
    expect(screen.getByTestId("probe-has-rail").textContent).toBe("no");
    expect(screen.getByTestId("probe-status").textContent).toBe("—");
  });

  it("keeps the typed publication contract", () => {
    // Compile-time contract: a SurfaceChrome is exactly these three fields.
    const chrome: SurfaceChrome = { rail: null, railLabel: "Context", status: null };
    expect(Object.keys(chrome).sort()).toEqual(["rail", "railLabel", "status"]);
  });
});

describe("shell layout contract", () => {
  it("renders exactly one main landmark and one primary navigation", () => {
    renderShell(
      <Shell current="workspace" onNavigate={() => {}}>
        <div>canvas</div>
      </Shell>,
    );

    expect(document.querySelectorAll("main").length).toBe(1);
    expect(document.querySelectorAll("#main-content").length).toBe(1);
    // One desktop nav + one mobile nav, both real <nav> elements with names.
    const navs = Array.from(document.querySelectorAll("nav")).filter((n) =>
      (n.getAttribute("aria-label") ?? "").toLowerCase().includes("navigation"),
    );
    expect(navs.length).toBe(2);
  });

  it("does not render a second rail when no surface publishes one", () => {
    renderShell(
      <Shell current="workspace" onNavigate={() => {}}>
        <div>canvas</div>
      </Shell>,
    );
    expect(screen.queryByTestId("shell-surface-rail")).toBeNull();
  });
});

// Keep the DOM clean between tests; jsdom is shared across the file.
afterAll(() => cleanup());
