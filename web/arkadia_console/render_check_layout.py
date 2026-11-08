"""Layout acceptance harness for the conversational workspace (AO4-01 / AO4-05/06).

This measures the *rendered* workspace, not the source. It exists because the
defect it guards against was invisible to every static check: the CSS declared a
three-column grid with two children, so the conversation canvas collapsed into
the 248px rail track while the inspector took the flexible one. Typecheck, build
and the whole Python suite were green while the product was unusable.

What it asserts, at each viewport and for each route:

  * the canvas is the widest region and the inspector is narrower (>=1280px);
  * the canvas is not collapsed to rail width (the specific regression);
  * the workspace grid has exactly two tracks (no unused rail column);
  * there is no horizontal overflow;
  * there is exactly one primary navigation system and one <main> landmark;
  * the composer is aligned with the canvas (same left edge);
  * below the inspector breakpoint the inspector is not an inline column;
  * the DOM settles (a bounded mutation count) — a render loop is caught here.

── Identity modes ─────────────────────────────────────────────────────────────

The protected surfaces render a sign-in threshold until an identity is verified,
so the layout cannot be measured without one. Two modes exist, and the report
labels which was used:

  * **stub** (`--path /layout-harness.html`): the test-only harness mounts the
    real `Shell` and `WorkspaceShell` with a *stubbed* identity. It proves the
    layout primitives but NOT that the protected route renders authenticated.

  * **test identity** (`--require-authenticated`, routes `/workspace`, `/arkana`,
    `/weaver` or `/engineering-lab`): the real protected route renders under a **disposable test
    identity** (`lib/testIdentity.ts`), which authenticates through the backend's
    documented dev-mode seam (`api/auth.py`). This is genuine authenticated
    coverage of the real route components — but it is NOT real Firebase
    authentication, and the report says so.

`--require-authenticated` fails the run if the protected route did not render
(the auth threshold is visible, or the test-identity banner is absent), so a
stubbed or unauthenticated render can never be reported as authenticated.

Output: `render_evidence/layout_metrics.json` plus one screenshot per
(route, viewport).
"""
from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
OUT = HERE / "render_evidence"

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "tablet_1024x768", "width": 1024, "height": 768},
    {"name": "mobile_390x844", "width": 390, "height": 844, "dpr": 3, "touch": True},
]

# The rail track the canvas used to collapse into. A canvas at or below this
# width is the regression, not a narrow-but-valid layout.
RAIL_WIDTH = 248
# The inspector's declared track width.
INSPECTOR_WIDTH = 300
# The inspector is inline at >=1280px and a sheet below it (WorkspaceShell).
INSPECTOR_BREAKPOINT = 1280

# Measured over a quiet 1.5s window *after* the initial mount has settled. A
# settled app produces a handful of mutations (a status line, a late read); a
# render loop produces thousands. 200 is far above a real settle and far below a
# loop — it is a *loop* detector, not a performance assertion.
MAX_SETTLED_MUTATIONS = 200

# Per-route region selectors. `inspector` is None for a route that has no
# inspector region (Arkana is a single conversation column).
ROUTES = {
    "/workspace": {
        "label": "Workspace",
        "canvas": ".cg-canvas",
        "inspector": ".cg-inspector",
        "composer": ".cg-composer-inner",
        "workspace": ".cg-workspace",
        "grid": True,
        # The workspace composer is docked to the canvas, so its left edge must
        # track the canvas. Arkana centres its composer in a max-width column,
        # so that assertion does not apply there.
        "composer_aligned": True,
    },
    "/arkana": {
        "label": "Arkana",
        "canvas": ".arkana-main",
        "inspector": None,
        "composer": ".arkana-composer-inner",
        "workspace": ".arkana-shell",
        "grid": False,
        "composer_aligned": False,
    },
    "/layout-harness.html": {
        "label": "Layout harness (stub identity)",
        "canvas": ".cg-canvas",
        "inspector": ".cg-inspector",
        "composer": ".cg-composer-inner",
        "workspace": ".cg-workspace",
        "grid": True,
        "composer_aligned": True,
    },
    "/weaver": {
        "label": "Weaver",
        "canvas": ".page-column",
        "inspector": None,
        "composer": None,
        "workspace": ".page-column",
        "grid": False,
        "composer_aligned": False,
        "requires_canvas_readout": True,
    },
    "/engineering-lab": {
        "label": "Engineering Lab",
        "canvas": '[data-testid="mission-workspace"]',
        "inspector": None,
        "composer": None,
        "workspace": '[data-testid="mission-workspace"]',
        "grid": False,
        "composer_aligned": False,
        "requires_mission_workspace": True,
    },
}


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def do_GET(self):
        path = self.path.split("?")[0]
        target = DIST / path.lstrip("/")
        if path != "/" and not target.exists() and "." not in path.rsplit("/", 1)[-1]:
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, *a):
        pass


def serve() -> int:
    httpd = socketserver.TCPServer(("127.0.0.1", 0), SPAHandler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return port


# Installed before any application script runs, so it observes the whole mount.
# Counts DOM mutations; a render loop shows up as an unbounded count. Written as
# an IIFE so the observer is actually installed (a bare arrow expression would
# evaluate to a function and never run).
INSTALL_MUTATION_COUNTER = """
(() => {
  window.__ao005Mutations = 0;
  const observer = new MutationObserver((records) => {
    window.__ao005Mutations += records.length;
  });
  // `document` (not `documentElement`) — an init script runs before the root
  // element exists, and `document` is always a Node.
  observer.observe(document, {
    childList: true, subtree: true, attributes: true, characterData: true,
  });
  window.__ao005Observer = observer;
})();
"""


def measure_js(route: dict) -> str:
    """The measurement expression for one route's region selectors."""
    return """
    (route) => {
      const rect = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      };
      const q = (sel) => (sel ? document.querySelector(sel) : null);
      const all = (sel) => Array.from(document.querySelectorAll(sel));

      const canvas = q(route.canvas);
      const inspector = q(route.inspector);
      const composer = q(route.composer);
      const workspace = q(route.workspace);
      const rail = q('[data-testid="shell-surface-rail"]');
      const missionWorkspace = q('[data-testid="mission-workspace"]');
      const missionNextDecision = q('[data-testid="mission-next-decision"]');

      // Primary navigation landmarks: the shell owns exactly two (desktop
      // sidebar + mobile strip). A surface rail is NOT primary navigation.
      const primaryNavs = all('nav[aria-label]').filter(
        (n) => (n.getAttribute('aria-label') || '').toLowerCase().includes('navigation')
      );

      return {
        url: location.pathname,
        canvas: rect(canvas),
        inspector: rect(inspector),
        composer: rect(composer),
        workspace: rect(workspace),
        rail: rect(rail),
        workspaceColumns: workspace ? getComputedStyle(workspace).gridTemplateColumns : null,
        mainCount: all('main').length,
        mainIdCount: all('#main-content').length,
        primaryNavCount: primaryNavs.length,
        primaryNavLabels: primaryNavs.map((n) => n.getAttribute('aria-label')),
        docScrollWidth: document.documentElement.scrollWidth,
        docClientWidth: document.documentElement.clientWidth,
        bodyScrollWidth: document.body.scrollWidth,
        workspaceMounted: Boolean(workspace),
        authThreshold: Boolean(q('[data-testid="auth-threshold-signin"]')),
        testIdentityBanner: Boolean(q('[data-testid="test-identity-banner"]')),
        stubIdentity: Boolean(q('[data-test-identity="stub"]')),
        weaverCanvasSnapshot: Boolean(q('[data-testid="weaver-canvas-snapshot"]')),
        weaverCanvasReadout: Boolean(q('[data-testid="weaver-canvas-readout"]')),
        weaverCanvasUnknown: Boolean(q('[data-testid="weaver-canvas-unknown"]')),
        missionWorkspace: Boolean(missionWorkspace),
        missionNextDecision: missionNextDecision ? {
          rect: rect(missionNextDecision),
          scrollWidth: missionNextDecision.scrollWidth,
          clientWidth: missionNextDecision.clientWidth,
        } : null,
        mutations: window.__ao005Mutations ?? null,
      };
    }
    """


def check(metrics: dict, viewport: dict, route: dict, require_authenticated: bool) -> list[str]:
    """Return a list of failures for one (route, viewport). Empty means pass."""
    failures: list[str] = []
    width = viewport["width"]

    if metrics["mainCount"] != 1:
        failures.append(f"expected exactly 1 <main>, found {metrics['mainCount']}")
    if metrics["mainIdCount"] != 1:
        failures.append(f"expected exactly 1 #main-content, found {metrics['mainIdCount']}")
    # The shell owns exactly two primary-navigation landmarks (desktop + mobile).
    # A third would be a second navigation system; zero would be no navigation.
    if metrics["primaryNavCount"] != 2:
        failures.append(
            f"expected exactly 2 shell-owned primary navigation landmarks, "
            f"found {metrics['primaryNavCount']} {metrics['primaryNavLabels']}"
        )

    overflow = metrics["docScrollWidth"] - metrics["docClientWidth"]
    if overflow > 1:
        failures.append(f"horizontal overflow: {overflow}px")

    # A render loop is caught here: the DOM never settles.
    mutations = metrics["mutations"]
    if mutations is not None and mutations > MAX_SETTLED_MUTATIONS:
        failures.append(
            f"DOM did not settle: {mutations} mutations > {MAX_SETTLED_MUTATIONS} (render loop?)"
        )

    if require_authenticated:
        if metrics["authThreshold"]:
            failures.append("protected route rendered its auth threshold, not the surface")
        if not metrics["testIdentityBanner"]:
            failures.append("test-identity banner absent — not an authenticated render")
        if metrics["stubIdentity"]:
            failures.append("stub identity present in an authenticated run")

    if route.get("requires_canvas_readout"):
        if not metrics["weaverCanvasSnapshot"]:
            failures.append("Weaver canvas panel did not mount")
        if metrics["weaverCanvasUnknown"]:
            failures.append("Weaver canvas returned an incomplete or malformed payload")
        elif not metrics["weaverCanvasReadout"]:
            failures.append("Weaver canvas did not hydrate from the authenticated API read")

    if route.get("requires_mission_workspace"):
        if not metrics["missionWorkspace"]:
            failures.append("Engineering Lab Mission Control did not mount")
        if not metrics["missionNextDecision"]:
            failures.append("Engineering Lab Next decision panel did not mount")
        else:
            panel_overflow = metrics["missionNextDecision"]["scrollWidth"] - metrics["missionNextDecision"]["clientWidth"]
            if panel_overflow > 1:
                failures.append(f"Mission Control Next decision panel has horizontal overflow: {panel_overflow}px")

    if not metrics["workspaceMounted"]:
        failures.append("workspace not mounted — layout unmeasured")
        return failures

    canvas = metrics["canvas"]
    inspector = metrics["inspector"]
    if not canvas:
        failures.append("canvas region missing")
        return failures

    # The workspace grid must have exactly two tracks (canvas + inspector) at
    # the inline-inspector breakpoint. Below it the inspector is a sheet, so a
    # single-column grid is correct. A third track is the obsolete
    # navigation-rail column the regression left.
    if route["grid"] and width >= INSPECTOR_BREAKPOINT and metrics["workspaceColumns"]:
        tracks = [t for t in metrics["workspaceColumns"].split(" ") if t.strip()]
        if len(tracks) != 2:
            failures.append(
                f"workspace grid has {len(tracks)} tracks ({metrics['workspaceColumns']}), expected 2"
            )

    if width >= INSPECTOR_BREAKPOINT:
        if canvas["w"] <= RAIL_WIDTH:
            failures.append(f"canvas collapsed to rail width: {canvas['w']}px <= {RAIL_WIDTH}px")
        if route["inspector"]:
            if not inspector:
                failures.append(f"inspector region missing at >={INSPECTOR_BREAKPOINT}px")
            else:
                if canvas["w"] <= inspector["w"]:
                    failures.append(
                        f"canvas ({canvas['w']}px) is not wider than inspector ({inspector['w']}px)"
                    )
                if abs(inspector["w"] - INSPECTOR_WIDTH) > 2:
                    failures.append(
                        f"inspector width {inspector['w']}px != declared {INSPECTOR_WIDTH}px"
                    )
        # The composer must sit inside the canvas, not offset by a phantom rail.
        composer = metrics["composer"]
        if route["composer_aligned"] and composer and abs(composer["x"] - canvas["x"]) > 40:
            failures.append(
                f"composer left edge {composer['x']} not aligned with canvas {canvas['x']}"
            )
    else:
        # Below the breakpoint the inspector is a sheet, not an inline column.
        if route["inspector"] and inspector and inspector["w"] > 0:
            failures.append(
                f"inspector rendered inline below the {INSPECTOR_BREAKPOINT}px breakpoint"
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-authenticated",
        action="store_true",
        help="Fail unless the protected route rendered under the disposable test identity.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Serve an already-running dev server instead of the static build.",
    )
    parser.add_argument(
        "--routes",
        default="/workspace",
        help="Comma-separated routes to measure (e.g. '/workspace,/arkana').",
    )
    parser.add_argument(
        "--identity-label",
        default="unauthenticated (no test identity configured)",
        help="How the report should describe the identity used.",
    )
    args = parser.parse_args()

    routes = [r.strip() for r in args.routes.split(",") if r.strip()]
    unknown = [r for r in routes if r not in ROUTES]
    if unknown:
        print(f"FAIL: unknown route(s) {unknown}; known: {sorted(ROUTES)}", file=sys.stderr)
        return 2

    if args.base_url:
        base = args.base_url.rstrip("/")
    else:
        if not DIST.exists():
            print(f"FAIL: no build at {DIST}; run `pnpm build` first", file=sys.stderr)
            return 2
        base = f"http://127.0.0.1:{serve()}"
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    all_failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for route_path in routes:
            route = ROUTES[route_path]
            for vp in VIEWPORTS:
                ctx_args = {"viewport": {"width": vp["width"], "height": vp["height"]}}
                if vp.get("dpr"):
                    ctx_args["device_scale_factor"] = vp["dpr"]
                if vp.get("touch"):
                    ctx_args["has_touch"] = True
                    ctx_args["is_mobile"] = True
                ctx = browser.new_context(**ctx_args)
                page = ctx.new_page()
                page_errors: list[str] = []
                page.on("pageerror", lambda e: page_errors.append(str(e)[:200]))
                page.add_init_script(INSTALL_MUTATION_COUNTER)
                page.goto(f"{base}{route_path}", wait_until="networkidle")
                # Let the mount settle, then read the mutation count. A loop
                # keeps mutating through this window and blows the bound.
                page.wait_for_timeout(1500)
                metrics = page.evaluate(measure_js(route), route)
                failures = check(metrics, vp, route, args.require_authenticated)
                if page_errors:
                    failures.append(f"page errors: {page_errors[:3]}")
                slug = route_path.strip("/").replace("/", "_") or "root"
                shot = OUT / f"{slug}_{vp['name']}.png"
                page.screenshot(path=str(shot), full_page=False)
                results.append(
                    {
                        "route": route_path,
                        "route_label": route["label"],
                        "viewport": vp["name"],
                        "identity": args.identity_label,
                        "metrics": metrics,
                        "failures": failures,
                        "screenshot": str(shot.relative_to(HERE)),
                    }
                )
                all_failures.extend(f"{route_path} {vp['name']}: {f}" for f in failures)
                ctx.close()
        browser.close()

    report = {
        "generated_by": "render_check_layout.py",
        "routes": routes,
        "identity_label": args.identity_label,
        "authenticated_requested": args.require_authenticated,
        "results": results,
        "failures": all_failures,
        "verdict": "PASS" if not all_failures else "FAIL",
    }
    (OUT / "layout_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({f"{r['route']} {r['viewport']}": r["metrics"] for r in results}, indent=2))
    print()
    if all_failures:
        print("FAILURES:")
        for f in all_failures:
            print(" -", f)
        return 1
    print("PASS: all routes and viewports satisfy the layout contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
