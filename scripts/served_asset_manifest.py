#!/usr/bin/env python3
"""Record which asset bytes the canonical origin serves.

The revision probe (`/api/version`) binds a deployment to a source revision. It
says nothing about the artifact the origin actually hands a browser, so this
helper records that artifact: the document it serves at `/`, the asset paths the
document declares, and the sha256 of each asset response.

It records facts and makes no parity judgement. Build output is
environment-dependent, so a hash difference is not by itself divergence and a
match is not acceptance.

Read-only: `GET` only, no mutation verbs, no credentials, no token printed.
"""
from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request

BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
ASSET_ACCEPT = "*/*"
USER_AGENT = "Arkadia-Served-Asset-Manifest/1.0"

# Only build output is interesting; a document also references runtime files
# (`/firebase-config.js`), icons and fonts, which are not the compiled bundle.
_ASSET_DIR = "/assets/"

_REF = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
_EXTERNAL = ("http://", "https://", "//", "data:", "#")


def _asset_path(value: str) -> str | None:
    """Return the origin-absolute asset path, or None when the reference is not one."""
    value = value.strip()
    if not value or value.startswith(_EXTERNAL):
        return None
    value = value.removeprefix("./")
    if not value.startswith("/"):
        value = "/" + value
    if _ASSET_DIR not in value:
        return None
    return value


def declared_assets(html: str) -> list[str]:
    """Asset paths the document declares, de-duplicated in document order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for reference in _REF.findall(html):
        path = _asset_path(reference)
        if path is None or path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return ordered


def fetch(url: str, accept: str, timeout: float = 20.0) -> tuple[int, bytes, str]:
    """Return ``(status, body, content_type)``; a non-2xx status is data, not an error."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "") or ""
    except urllib.error.HTTPError as error:
        headers = getattr(error, "headers", None)
        content_type = headers.get("Content-Type", "") if headers else ""
        return error.code, error.read(), content_type or ""


def observe(origin: str, timeout: float = 20.0, fetch=fetch) -> dict:
    """Capture the served document and every asset it declares."""
    base = origin.rstrip("/")
    status, body, content_type = fetch(base + "/", BROWSER_ACCEPT, timeout)
    html = body.decode("utf-8", "replace")
    assets = []
    for path in declared_assets(html):
        asset_status, asset_body, asset_type = fetch(base + path, ASSET_ACCEPT, timeout)
        assets.append(
            {
                "path": path,
                "status": asset_status,
                "bytes": len(asset_body),
                "sha256": hashlib.sha256(asset_body).hexdigest(),
                "content_type": asset_type,
            }
        )
    return {
        "origin": base,
        "document": {
            "path": "/",
            "status": status,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "content_type": content_type,
        },
        "assets": assets,
        "note": (
            "Served bytes only. Build output is environment-dependent, so this "
            "manifest is not a parity oracle in either direction."
        ),
    }


if __name__ == "__main__":
    import json
    import os
    import sys

    print(json.dumps(observe(os.environ.get("ARKADIA_PRODUCTION_ORIGIN", "https://arkadia-qzu4.onrender.com")), indent=2))
    sys.exit(0)
