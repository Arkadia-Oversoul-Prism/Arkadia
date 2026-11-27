"""The served-asset manifest records bytes, and only the bytes it was given.

The manifest exists because revision identity (`/api/version`) and served
artifact identity are different claims: a deployment can name the right source
and still hand a browser something else. These tests pin the extraction and the
assembly without touching the network, and each detector carries a control so a
silent regression cannot pass as agreement.
"""
import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import served_asset_manifest as manifest  # noqa: E402

# Shaped from the document the canonical origin actually serves: build output
# under /assets/, plus the runtime config, icon and font links that are not it.
SERVED_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <link rel="icon" type="image/svg+xml" href="/arkadia-mark.svg" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet" />
    <script type="module" crossorigin src="/assets/index-CYGHeCpJ.js"></script>
    <link rel="modulepreload" crossorigin href="/assets/vendor-react-nf7bT_Uh.js">
    <link rel="modulepreload" crossorigin href="/assets/vendor-firebase-DNJjg0gV.js">
    <link rel="stylesheet" crossorigin href="/assets/index-BJojPKi_.css">
  </head>
  <body>
    <div id="root"></div>
    <script src="/firebase-config.js"></script>
  </body>
</html>
"""

EXPECTED_ASSETS = [
    "/assets/index-CYGHeCpJ.js",
    "/assets/vendor-react-nf7bT_Uh.js",
    "/assets/vendor-firebase-DNJjg0gV.js",
    "/assets/index-BJojPKi_.css",
]


def test_extracts_every_declared_build_asset_in_document_order():
    assert manifest.declared_assets(SERVED_HTML) == EXPECTED_ASSETS


def test_runtime_config_icon_and_external_links_are_not_build_output():
    declared = manifest.declared_assets(SERVED_HTML)
    assert "/firebase-config.js" not in declared
    assert "/arkadia-mark.svg" not in declared
    assert not [p for p in declared if p.startswith("http")]


def test_duplicate_references_are_collapsed_and_order_is_preserved():
    html = (
        '<script src="/assets/b.js"></script>'
        '<link href="/assets/a.css">'
        '<script src="/assets/b.js"></script>'
    )
    assert manifest.declared_assets(html) == ["/assets/b.js", "/assets/a.css"]


@pytest.mark.parametrize(
    "reference,expected",
    [
        ("./assets/x.js", "/assets/x.js"),
        ("assets/x.js", "/assets/x.js"),
        ("/assets/x.js", "/assets/x.js"),
        ("/firebase-config.js", None),
        ("https://example.invalid/assets/x.js", None),
        ("//cdn.invalid/assets/x.js", None),
        ("data:text/javascript,1", None),
        ("#main", None),
        ("", None),
    ],
)
def test_reference_normalisation(reference, expected):
    assert manifest._asset_path(reference) == expected


def test_negative_control_a_document_without_build_output_declares_nothing():
    """The detector must not invent assets, or every origin would look complete."""
    html = '<html><head><link rel="icon" href="/favicon.ico"></head><body></body></html>'
    assert manifest.declared_assets(html) == []


def test_observe_hashes_the_bytes_that_were_served_and_asks_as_a_browser():
    payloads = {
        "/": (200, SERVED_HTML.encode(), "text/html; charset=utf-8"),
        "/assets/index-CYGHeCpJ.js": (200, b"console.log(1)\n", "text/javascript"),
        "/assets/vendor-react-nf7bT_Uh.js": (200, b"react", "text/javascript"),
        "/assets/vendor-firebase-DNJjg0gV.js": (200, b"firebase", "text/javascript"),
        "/assets/index-BJojPKi_.css": (200, b":root{}", "text/css"),
    }
    calls = []

    def fake_fetch(url, accept, timeout):
        calls.append((url, accept))
        path = url.removeprefix("https://origin.invalid")
        return payloads[path]

    result = manifest.observe("https://origin.invalid/", fetch=fake_fetch)

    assert result["origin"] == "https://origin.invalid"
    assert result["document"]["sha256"] == hashlib.sha256(SERVED_HTML.encode()).hexdigest()
    assert [a["path"] for a in result["assets"]] == EXPECTED_ASSETS
    assert [a["sha256"] for a in result["assets"]] == [
        hashlib.sha256(payloads[p][1]).hexdigest() for p in EXPECTED_ASSETS
    ]
    assert [a["bytes"] for a in result["assets"]] == [len(payloads[p][1]) for p in EXPECTED_ASSETS]
    # The document is fetched as a navigation; assets are not HTML.
    assert calls[0] == ("https://origin.invalid/", manifest.BROWSER_ACCEPT)
    assert all(accept == manifest.ASSET_ACCEPT for _, accept in calls[1:])


def test_observe_records_a_failed_asset_instead_of_dropping_it():
    """A missing chunk is the interesting case; omitting it would hide the defect."""
    def fake_fetch(url, accept, timeout):
        if url.endswith(".js"):
            return 404, b"not found", "text/plain"
        return 200, SERVED_HTML.encode(), "text/html"

    result = manifest.observe("https://origin.invalid", fetch=fake_fetch)

    failed = [a for a in result["assets"] if a["status"] == 404]
    assert [a["path"] for a in failed] == [
        "/assets/index-CYGHeCpJ.js",
        "/assets/vendor-react-nf7bT_Uh.js",
        "/assets/vendor-firebase-DNJjg0gV.js",
    ]


def test_manifest_makes_no_parity_claim():
    """The note is the guard against reading a hash as acceptance."""
    result = manifest.observe(
        "https://origin.invalid",
        fetch=lambda url, accept, timeout: (200, SERVED_HTML.encode(), "text/html"),
    )
    assert "not a parity oracle" in result["note"]


def test_the_runtime_probe_records_the_manifest():
    """The probe must emit the block it promises, or the record is unreachable."""
    source = (REPO_ROOT / "scripts" / "production_runtime_probe.py").read_text(encoding="utf-8")
    assert "served_asset_manifest.observe(BASE" in source
    assert '"served_assets": {}' in source
