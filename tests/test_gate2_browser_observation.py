"""Gate 2 browser-rendered UI observation harness — fitness tests.

These are source-level and pure-function tests. They do NOT require a browser:
the live probe is exercised by running the script. What is proven here is that

  * the anchor list is not stale (every anchor still exists in the frontend tree),
  * the classifier actually has teeth (negative controls),
  * the benign-console exemption is scoped to an understood cause, not blanket,
  * the harness is read-only and holds no credential.
"""

from pathlib import Path

from scripts.gate2_browser_observation import (
    EXPECTED_BENIGN,
    ROUTES,
    classify,
    source_anchors_present,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gate2_browser_observation.py"


def _obs(route: str, body: str, **over) -> dict:
    base = {
        "route": route,
        "status": 200,
        "err": None,
        "bodyLen": len(body),
        "bodyLower": body.lower(),
        "consoleErrors": [],
        "pageErrors": [],
        "failedRequests": [],
    }
    base.update(over)
    return base


def _body_with_anchors(route: str) -> str:
    return " ".join(ROUTES[route][0])


# ── anchor integrity ─────────────────────────────────────────────────────────


def test_every_anchor_still_exists_in_frontend_source():
    present = source_anchors_present()
    missing = sorted(a for a, ok in present.items() if not ok)
    assert missing == [], f"stale anchors (removed from source): {missing}"


def test_anchors_are_lowercase_ascii():
    """Deployed text is uppercased by CSS and may contain unicode dashes, so an
    anchor that is not lowercase ASCII would produce false failures."""
    for route, (anchors, _prov) in ROUTES.items():
        for a in anchors:
            assert a == a.lower(), f"{route}: anchor not lowercase: {a!r}"
            assert a.isascii(), f"{route}: anchor not ascii: {a!r}"


def test_every_route_declares_provenance():
    for route, (anchors, prov) in ROUTES.items():
        assert anchors, f"{route} has no anchors"
        assert prov.strip(), f"{route} has no provenance"


def test_critical_routes_are_covered():
    for route in ("/", "/solariun", "/solspire", "/nexus", "/oracle", "/spiral-codex"):
        assert route in ROUTES, f"critical route not observed: {route}"


# ── classifier teeth (negative controls) ─────────────────────────────────────


def test_fully_rendered_route_is_observed():
    verdict, failures, _info = classify(_obs("/nexus", _body_with_anchors("/nexus")))
    assert verdict == "OBSERVED"
    assert failures == []


def test_missing_anchor_fails():
    verdict, failures, _info = classify(_obs("/nexus", "nothing rendered here"))
    assert verdict == "FAILED"
    assert any("missing anchors" in f for f in failures)


def test_non_200_fails():
    verdict, failures, _info = classify(_obs("/nexus", _body_with_anchors("/nexus"), status=500))
    assert verdict == "FAILED"
    assert any("HTTP 500" in f for f in failures)


def test_page_error_fails():
    verdict, failures, _info = classify(
        _obs("/nexus", _body_with_anchors("/nexus"), pageErrors=["Cannot read properties of undefined"])
    )
    assert verdict == "FAILED"
    assert any("pageErrors" in f for f in failures)


def test_failed_request_fails():
    verdict, failures, _info = classify(
        _obs("/nexus", _body_with_anchors("/nexus"), failedRequests=["/x.js :: net::ERR_FAILED"])
    )
    assert verdict == "FAILED"
    assert any("failedRequests" in f for f in failures)


def test_unexpected_console_error_fails():
    verdict, failures, _info = classify(
        _obs(
            "/nexus",
            _body_with_anchors("/nexus"),
            consoleErrors=[{"text": "TypeError: boom", "url": "https://alias/assets/x.js"}],
        )
    )
    assert verdict == "FAILED"
    assert any("unexpected console errors" in f for f in failures)


# ── benign exemption is scoped ───────────────────────────────────────────────


def test_known_benign_console_noise_is_informational_not_failure():
    verdict, failures, info = classify(
        _obs(
            "/spiral-codex",
            _body_with_anchors("/spiral-codex"),
            consoleErrors=[
                {
                    "text": "Failed to load resource: the server responded with a status of 404 ()",
                    "url": "https://arkadia-kw64.onrender.com/api/codex/categories",
                }
            ],
        )
    )
    assert verdict == "OBSERVED"
    assert failures == []
    assert info and "expected-benign" in info[0]


def test_benign_exemption_does_not_mask_a_different_404():
    """The exemption matches the understood route only -- an unrelated 404 must
    still fail, otherwise the exemption would be a blanket suppression."""
    verdict, failures, _info = classify(
        _obs(
            "/spiral-codex",
            _body_with_anchors("/spiral-codex"),
            consoleErrors=[
                {
                    "text": "Failed to load resource: the server responded with a status of 404 ()",
                    "url": "https://arkadia-kw64.onrender.com/api/some/other/route",
                }
            ],
        )
    )
    assert verdict == "FAILED"
    assert any("unexpected console errors" in f for f in failures)


def test_benign_entry_is_documented():
    for route, why in EXPECTED_BENIGN.items():
        assert route.startswith("/api/"), route
        assert len(why.strip()) > 20, f"{route} exemption lacks an explanation"


# ── read-only / no credential ────────────────────────────────────────────────


def test_harness_is_read_only_and_credential_free():
    src = _SCRIPT.read_text()
    assert "Authorization" not in src, "harness must not send credentials"
    assert "git push" not in src
    assert "git commit" not in src
    for verb in ('method="POST"', "method='POST'", "PUT", "PATCH", "DELETE"):
        assert verb not in src, f"harness must not perform {verb}"
