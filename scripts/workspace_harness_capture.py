"""Capture the conversational workspace UI from the QA harness.

The harness mounts the REAL `WorkspacePage` component from the canonical
frontend. It is not the application and not an authenticated session — the auth
gate is simply not part of this entry point. Every image it produces is labelled
as harness evidence, never as an authenticated acceptance run.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-151.0.7922.138/chrome"
BASE = "http://127.0.0.1:5199"
OUT = Path("/workspace/qa_shots/workspace")
OUT.mkdir(parents=True, exist_ok=True)

report = {}


def capture(viewport, label, is_mobile):
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

        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(900)

        checks = {
            "shell": page.locator('[data-testid="workspace-shell"]').count(),
            "welcome": page.locator('[data-testid="workspace-welcome"]').count(),
            "composer": page.locator('[data-testid="workspace-composer-input"]').count(),
            "tokens_total": page.locator('[data-testid^="workspace-token-"]').count(),
            "tokens_disabled": page.locator('[data-testid^="workspace-token-"][disabled]').count(),
            "lifecycle": page.locator('[data-testid="workspace-lifecycle"]').count(),
            "no_auth_notice": page.locator('[data-testid="workspace-no-authorization"]').count(),
            "overflow": page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth + 1"
            ),
            "scrollWidth": page.evaluate("() => document.documentElement.scrollWidth"),
        }

        # Scope a capability through the composer and confirm the chip appears.
        page.locator('[data-testid="workspace-token-knowledge"]').click()
        page.wait_for_timeout(250)
        checks["token_scopes_capability"] = page.locator(
            '[data-testid="workspace-active-capability"]'
        ).count()
        checks["composer_value"] = page.locator(
            '[data-testid="workspace-composer-input"]'
        ).input_value()
        page.screenshot(path=str(OUT / f"harness-{label}-scoped.png"), full_page=True)

        # Reset to the welcome state for the primary shot. On mobile the rail is
        # correctly hidden (display:none), so the reset is done through the rail
        # sheet instead of the inline button.
        if is_mobile:
            page.locator('[data-testid="workspace-open-rail"]').click()
            page.wait_for_timeout(350)
            checks["rail_sheet"] = page.locator("#cg-rail-sheet").count()
            page.screenshot(path=str(OUT / f"harness-{label}-rail-sheet.png"))
            page.locator('[data-testid="workspace-new-conversation"]').click()
            page.wait_for_timeout(300)
            page.locator('[data-testid="workspace-close-rail"]').click()
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"harness-{label}-welcome.png"), full_page=True)
            page.locator('[data-testid="workspace-open-inspector"]').click()
            page.wait_for_timeout(350)
            checks["inspector_sheet"] = page.locator("#cg-inspector-sheet").count()
            page.screenshot(path=str(OUT / f"harness-{label}-inspector-sheet.png"))
        else:
            page.locator('[data-testid="workspace-new-conversation"]').click()
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"harness-{label}-welcome.png"), full_page=True)

        checks["console_errors"] = errors[:10]
        report[label] = checks
        browser.close()


capture({"width": 1440, "height": 900}, "desktop", False)
capture({"width": 390, "height": 844}, "mobile", True)
print(json.dumps(report, indent=2))
