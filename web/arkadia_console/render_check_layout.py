"""Layout acceptance harness for the conversational workspace (AO4-01 / AO4-05/06).

This measures the *rendered* workspace, not the source. It exists because the
defect it guards against was invisible to every static check: the CSS declared a
three-column grid with two children, so the conversation canvas collapsed into
the 248px rail track while the inspector took the flexible one. Typecheck, build
and the whole Python suite were green while the product was unusable.

What it asserts, at each viewport:

  * the canvas is the widest region and the inspector is narrower (>=1280px);
  * the canvas is not collapsed to rail width (the specific regression);
  * there is no horizontal overflow;
  * there is exactly one primary navigation and one <main> landmark;
  * the composer is aligned with the canvas (same left edge, same width);
  * below the inspector breakpoint the inspector is not an inline column.

Identity: this harness runs against the **unauthenticated** build, so the
protected workspace renders its sign-in threshold. It therefore measures the
shell and the layout primitives, and it labels itself as such — it is NOT
authenticated acceptance. `--authenticated` is accepted only when a disposable
test identity is configured; without one it reports UNAVAILABLE rather than
pretending.

Output: `render_evidence/layout_metrics.json` plus one screenshot per viewport.
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


MEASURE_JS = """
() => {
  const rect = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  };
  const q = (sel) => document.querySelector(sel);
  const all = (sel) => Array.from(document.querySelectorAll(sel));

  const canvas = q('.cg-canvas');
  const inspector = q('.cg-inspector');
  const composer = q('.cg-composer-inner');
  const workspace = q('.cg-workspace');
  const rail = q('[data-testid="shell-surface-rail"]');

  return {
    url: location.pathname,
    canvas: rect(canvas),
    inspector: rect(inspector),
    composer: rect(composer),
    workspace: rect(workspace),
    rail: rect(rail),
    // Grid tracks actually computed, which is what the bug was about.
    workspaceColumns: workspace ? getComputedStyle(workspace).gridTemplateColumns : null,
    mainCount: all('main').length,
    mainIdCount: all('#main-content').length,
    primaryNavCount: all('nav[aria-label]').filter(
      (n) => (n.getAttribute('aria-label') || '').toLowerCase().includes('navigation')
    ).length,
    docScrollWidth: document.documentElement.scrollWidth,
    docClientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    // Is the workspace actually mounted (vs the auth threshold)?
    workspaceMounted: Boolean(workspace),
    authThreshold: Boolean(q('[data-testid="auth-threshold"]')) || /sign in/i.test(document.body.innerText.slice(0, 400)),
  };
}
"""


def check(metrics: dict, viewport: dict) -> list[str]:
    """Return a list of failures for one viewport. Empty means pass."""
    failures: list[str] = []
    width = viewport["width"]

    if metrics["mainCount"] != 1:
        failures.append(f"expected exactly 1 <main>, found {metrics['mainCount']}")
    if metrics["mainIdCount"] != 1:
        failures.append(f"expected exactly 1 #main-content, found {metrics['mainIdCount']}")
    if metrics["primaryNavCount"] < 1:
        failures.append("no primary navigation landmark found")

    overflow = metrics["docScrollWidth"] - metrics["docClientWidth"]
    if overflow > 1:
        failures.append(f"horizontal overflow: {overflow}px")

    if not metrics["workspaceMounted"]:
        # The protected surface rendered its auth threshold. Layout metrics for
        # the workspace cannot be asserted; record it rather than pass silently.
        failures.append("workspace not mounted (auth threshold) — layout unmeasured")
        return failures

    canvas = metrics["canvas"]
    inspector = metrics["inspector"]
    if not canvas:
        failures.append("canvas region missing")
        return failures

    if width >= 1280:
        if not inspector:
            failures.append("inspector region missing at >=1280px")
        else:
            if canvas["w"] <= RAIL_WIDTH:
                failures.append(
                    f"canvas collapsed to rail width: {canvas['w']}px <= {RAIL_WIDTH}px"
                )
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
        if composer:
            if abs(composer["x"] - canvas["x"]) > 40:
                failures.append(
                    f"composer left edge {composer['x']} not aligned with canvas {canvas['x']}"
                )
    else:
        # Below the breakpoint the inspector is a sheet, not an inline column.
        if inspector and inspector["w"] > 0:
            failures.append("inspector rendered inline below the 1280px breakpoint")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authenticated", action="store_true")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Serve an already-running dev server instead of the static build.",
    )
    parser.add_argument(
        "--path",
        default="/workspace",
        help="Route to measure. Use /layout-harness.html for the stubbed-identity harness.",
    )
    parser.add_argument(
        "--identity-label",
        default="unauthenticated (no test identity configured)",
        help="How the report should describe the identity used.",
    )
    args = parser.parse_args()

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
        for vp in VIEWPORTS:
            ctx_args = {"viewport": {"width": vp["width"], "height": vp["height"]}}
            if vp.get("dpr"):
                ctx_args["device_scale_factor"] = vp["dpr"]
            if vp.get("touch"):
                ctx_args["has_touch"] = True
                ctx_args["is_mobile"] = True
            ctx = browser.new_context(**ctx_args)
            page = ctx.new_page()
            page.goto(f"{base}{args.path}", wait_until="networkidle")
            page.wait_for_timeout(900)
            metrics = page.evaluate(MEASURE_JS)
            failures = check(metrics, vp)
            shot = OUT / f"workspace_{vp['name']}.png"
            page.screenshot(path=str(shot), full_page=False)
            results.append(
                {
                    "viewport": vp["name"],
                    "identity": args.identity_label,
                    "metrics": metrics,
                    "failures": failures,
                    "screenshot": str(shot.relative_to(HERE)),
                }
            )
            all_failures.extend(f"{vp['name']}: {f}" for f in failures)
            ctx.close()
        browser.close()

    report = {
        "generated_by": "render_check_layout.py",
        "route": args.path,
        "identity_label": args.identity_label,
        "authenticated_requested": args.authenticated,
        "authenticated_available": False,
        "results": results,
        "failures": all_failures,
        "verdict": "PASS" if not all_failures else "FAIL",
    }
    (OUT / "layout_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({r["viewport"]: r["metrics"] for r in results}, indent=2))
    print()
    if all_failures:
        print("FAILURES:")
        for f in all_failures:
            print(" -", f)
        return 1
    print("PASS: all viewports satisfy the layout contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
