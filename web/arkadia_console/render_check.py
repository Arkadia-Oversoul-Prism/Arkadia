"""Headless render check for the unified shell (AO-002).

Serves the production build with an SPA fallback and captures the shell at
desktop and mobile viewports, measuring horizontal overflow and the presence of
the grouped navigation. This is *rendering* evidence, not authenticated
acceptance: the workspace is a protected surface, so an unauthenticated load
correctly shows the sign-in threshold.
"""
import http.server
import json
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

DIST = Path(__file__).resolve().parent / "dist"
OUT = Path("/workspace/arkadia/render_evidence")
OUT.mkdir(parents=True, exist_ok=True)


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


def serve():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), SPAHandler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def probe(page, url, label, width, height, mobile=False):
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(600)
    metrics = page.evaluate(
        """() => {
            const de = document.documentElement;
            const nav = document.querySelector('nav[aria-label="Primary navigation"]');
            const groups = document.querySelectorAll('.cg-nav-group');
            const labels = Array.from(document.querySelectorAll('.cg-nav-group-label'))
                .map(n => n.textContent.trim());
            const items = document.querySelectorAll('.cg-nav-item');
            const main = document.getElementById('main-content');
            return {
                scrollWidth: de.scrollWidth,
                clientWidth: de.clientWidth,
                overflow: de.scrollWidth - de.clientWidth,
                navPresent: !!nav,
                groupCount: groups.length,
                groupLabels: labels,
                navItemCount: items.length,
                mainLandmark: !!main,
                title: document.title,
                bodyText: (document.body.innerText || '').slice(0, 400),
            };
        }"""
    )
    shot = OUT / f"{label}.png"
    page.screenshot(path=str(shot), full_page=False)
    metrics["label"] = label
    metrics["screenshot"] = str(shot)
    return metrics


def main():
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}"
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Desktop
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        results.append(probe(page, base + "/", "desktop_home", 1440, 900))
        results.append(probe(page, base + "/workspace", "desktop_workspace_unauth", 1440, 900))
        ctx.close()
        # Mobile
        ctx = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        )
        page = ctx.new_page()
        results.append(probe(page, base + "/", "mobile_home", 390, 844, mobile=True))
        results.append(probe(page, base + "/workspace", "mobile_workspace_unauth", 390, 844, mobile=True))
        ctx.close()
        browser.close()
    httpd.shutdown()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
