"""Browser acceptance for the conversational workspace (AO-001 Phase 2).

Drives real Chromium at desktop and mobile device viewports against the served
application. Asserts the things a DOM-landmark claim cannot: that every route
renders, that no route overflows horizontally, and — where the surface is
reachable without an identity — that the workspace regions actually render.

The workspace is a protected surface, so an unauthenticated run correctly shows
the sign-in threshold. That is recorded as the real state rather than worked
around: the script reports `auth_threshold` and skips the structural checks it
cannot honestly make.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-151.0.7922.138/chrome"
BASE = "http://127.0.0.1:8000"
OUT = Path("/workspace/qa_shots/workspace")
OUT.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("workspace", "/workspace"),
    ("home", "/"),
    ("arkana", "/arkana"),
    ("projects", "/projects"),
    ("engineering-lab", "/engineering-lab"),
    ("weaver", "/weaver"),
    ("knowledge", "/knowledge"),
    ("settings", "/settings"),
    ("solariun", "/solariun"),
    ("novanet", "/novanet"),
    ("about", "/about"),
]

report = {"desktop": [], "mobile": [], "workspace_checks": {}, "console_errors": []}


def run(viewport, label, is_mobile):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport=viewport,
            device_scale_factor=3 if is_mobile else 1,
            is_mobile=is_mobile,
            has_touch=is_mobile,
        )
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        for name, path in ROUTES:
            page.goto(BASE + path, wait_until="networkidle")
            page.wait_for_timeout(400)
            report[label].append(
                {
                    "route": path,
                    "overflow": page.evaluate(
                        "() => document.documentElement.scrollWidth > window.innerWidth + 1"
                    ),
                    "scrollWidth": page.evaluate("() => document.documentElement.scrollWidth"),
                    "title": page.title(),
                    "auth_threshold": page.locator('[data-testid="auth-threshold-signin"]').count(),
                    "shell": page.locator('[data-testid="workspace-shell"]').count(),
                }
            )
            page.screenshot(path=str(OUT / f"{label}-{name}.png"), full_page=True)

        if not is_mobile:
            page.goto(BASE + "/workspace", wait_until="networkidle")
            page.wait_for_timeout(500)
            checks = {
                "auth_threshold": page.locator('[data-testid="auth-threshold-signin"]').count(),
                "shell": page.locator('[data-testid="workspace-shell"]').count(),
                "nav_workspace": page.locator('[data-testid="nav-workspace"]').count(),
                "aria_current": page.locator('[aria-current="page"]').count(),
            }
            if checks["shell"]:
                checks.update(
                    {
                        "rail": page.locator(".cg-rail").count(),
                        "inspector": page.locator('[data-testid="workspace-inspector"]').count(),
                        "welcome": page.locator('[data-testid="workspace-welcome"]').count(),
                        "composer": page.locator('[data-testid="workspace-composer-input"]').count(),
                        "tokens_total": page.locator('[data-testid^="workspace-token-"]').count(),
                        "tokens_disabled": page.locator(
                            '[data-testid^="workspace-token-"][disabled]'
                        ).count(),
                        "lifecycle": page.locator('[data-testid="workspace-lifecycle"]').count(),
                        "no_auth_notice": page.locator(
                            '[data-testid="workspace-no-authorization"]'
                        ).count(),
                    }
                )
                page.locator('[data-testid="workspace-token-knowledge"]').click()
                page.wait_for_timeout(200)
                checks["token_scopes_capability"] = page.locator(
                    '[data-testid="workspace-active-capability"]'
                ).count()
                checks["composer_value"] = page.locator(
                    '[data-testid="workspace-composer-input"]'
                ).input_value()
            report["workspace_checks"] = checks

        report["console_errors"] = errors[:20]
        browser.close()


run({"width": 1440, "height": 900}, "desktop", False)
run({"width": 390, "height": 844}, "mobile", True)

print(json.dumps(report, indent=2))
