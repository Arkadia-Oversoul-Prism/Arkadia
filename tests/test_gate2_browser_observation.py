"""Gate 2 browser-rendered UI observation harness — fitness tests.

These are source-level and pure-function tests. They do NOT require a browser:
the live probe is exercised by running the script. What is proven here is that

  * the anchor list describes the application the canonical origin serves, and is
    not stale (every anchor still exists in that app's tree),
  * the route table is bound to the console's own surface declaration rather than
    to a retired frontend,
  * a stale list is reported as STALE instead of scoring a healthy application
    as failing (fail closed),
  * the classifier actually has teeth (negative controls),
  * the benign-console exemption is scoped to an understood cause, not blanket,
  * the harness is read-only and holds no credential.

The route/anchor table used to describe the archived Prism frontend. Prism was
archived at `c081d200` and the canonical origin now serves `web/arkadia_console`,
so the table is bound to the console surface declaration here: a future repoint
that drifts back to a retired app fails these tests instead of silently producing
a false production alarm.
"""

import json
import re
from pathlib import Path

from scripts.gate2_browser_observation import (
    ANCHOR_APP,
    EXPECTED_BENIGN,
    ROUTES,
    classify,
    main,
    source_anchors_present,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gate2_browser_observation.py"
_SURFACES = _ROOT / "web" / "arkadia_console" / "src" / "lib" / "surfaces.ts"

# A literal that exists only in the archived Prism frontend. Used as the
# discriminating control for the anchor-source scope.
_PRISM_ONLY_LITERAL = "become one continuous field"
_PRISM_SRC = _ROOT / "archive" / "frontend" / "arkadia-prism" / "web" / "public_prism" / "src"


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


def _declared_surfaces() -> dict[str, bool]:
    """`path -> requiresAuth`, parsed from the console's one surface table."""
    src = _SURFACES.read_text()
    declared: dict[str, bool] = {}
    for block in re.split(r"\n  \{\n", src):
        path = re.search(r'path:\s*"([^"]+)"', block)
        if path:
            declared[path.group(1)] = "requiresAuth: true" in block
    return declared


def _app_corpus(root: Path) -> str:
    corpus = []
    for p in root.rglob("*"):
        if p.suffix in (".ts", ".tsx"):
            corpus.append(p.read_text(encoding="utf-8", errors="ignore").lower())
    return "\n".join(corpus)


# ── anchor integrity ─────────────────────────────────────────────────────────


def test_every_anchor_still_exists_in_frontend_source():
    present = source_anchors_present()
    missing = sorted(a for a, ok in present.items() if not ok)
    assert missing == [], f"stale anchors (removed from source): {missing}"


def test_anchors_are_lowercase_ascii():
    """Deployed text is uppercased by CSS and may contain unicode dashes, so an
    anchor that is not lowercase ASCII would produce false failures."""
    for route, (anchors, _prov, _state) in ROUTES.items():
        for a in anchors:
            assert a == a.lower(), f"{route}: anchor not lowercase: {a!r}"
            assert a.isascii(), f"{route}: anchor not ascii: {a!r}"


def test_every_route_declares_provenance_and_state():
    for route, (anchors, prov, state) in ROUTES.items():
        assert anchors, f"{route} has no anchors"
        assert prov.strip(), f"{route} has no provenance"
        assert state in ("public", "auth_threshold"), f"{route}: unknown state {state!r}"


# ── the table describes the served app, not a retired one ────────────────────


def test_anchor_app_is_the_active_console():
    assert ANCHOR_APP.replace("\\", "/") == "web/arkadia_console"


def test_every_route_is_a_declared_console_surface():
    """A route the console does not declare cannot be a rendering failure."""
    declared = _declared_surfaces()
    assert declared, "surface table parsed to nothing — the parser is wrong"
    undeclared = sorted(r for r in ROUTES if r not in declared)
    assert undeclared == [], f"routes not declared by the console surface table: {undeclared}"


def test_route_render_state_matches_the_surface_auth_flag():
    """A protected surface renders the shared sign-in threshold, not its own
    copy, so its anchor must expect the threshold."""
    declared = _declared_surfaces()
    for route, (_anchors, _prov, state) in ROUTES.items():
        expected = "auth_threshold" if declared[route] else "public"
        assert state == expected, f"{route}: declared {expected} but table says {state}"


def test_both_render_states_are_covered():
    states = {state for _a, _p, state in ROUTES.values()}
    assert states == {"public", "auth_threshold"}, f"render states not covered: {states}"


def test_the_retired_prism_routes_are_gone():
    """Negative control: the table used to probe the archived Prism app."""
    for retired in ("/oracle", "/nexus", "/spiral-codex", "/solspire"):
        assert retired not in ROUTES, f"retired Prism route still probed: {retired}"


def test_anchor_source_is_the_console_not_the_archive():
    """The freshness oracle must read the served app. The control is only
    discriminating if the literal really does live in the archive."""
    assert _PRISM_SRC.is_dir(), "archive Prism source missing — control unusable"
    assert _PRISM_ONLY_LITERAL in _app_corpus(_PRISM_SRC)
    assert _PRISM_ONLY_LITERAL not in _app_corpus(_ROOT / ANCHOR_APP)


# ── staleness fails closed ───────────────────────────────────────────────────


def test_stale_anchor_list_fails_closed(monkeypatch, capsys):
    """A stale table is a harness defect, not a production finding: it must
    report STALE and refuse to score, rather than failing every route."""
    monkeypatch.setitem(
        ROUTES, "/", (["a literal that exists in no frontend"], "synthetic", "public")
    )
    rc = main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["browser_rendered_ui"] == "STALE"
    assert "a literal that exists in no frontend" in payload["stale_anchors"]
    assert payload["routes"] == {}, "a stale table must not score any route"


def test_a_current_table_is_not_reported_stale(capsys):
    """Negative control for the guard above: it must not be trivially true."""
    main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale_anchors"] == []
    assert payload["browser_rendered_ui"] != "STALE"


# ── classifier teeth (negative controls) ─────────────────────────────────────


def test_fully_rendered_route_is_observed():
    verdict, failures, _info = classify(_obs("/", _body_with_anchors("/")))
    assert verdict == "OBSERVED"
    assert failures == []


def test_missing_anchor_fails():
    verdict, failures, _info = classify(_obs("/", "nothing rendered here"))
    assert verdict == "FAILED"
    assert any("missing anchors" in f for f in failures)


def test_non_200_fails():
    verdict, failures, _info = classify(_obs("/", _body_with_anchors("/"), status=500))
    assert verdict == "FAILED"
    assert any("HTTP 500" in f for f in failures)


def test_page_error_fails():
    verdict, failures, _info = classify(
        _obs("/", _body_with_anchors("/"), pageErrors=["Cannot read properties of undefined"])
    )
    assert verdict == "FAILED"
    assert any("pageErrors" in f for f in failures)


def test_failed_request_fails():
    verdict, failures, _info = classify(
        _obs("/", _body_with_anchors("/"), failedRequests=["/x.js :: net::ERR_FAILED"])
    )
    assert verdict == "FAILED"
    assert any("failedRequests" in f for f in failures)


def test_unexpected_console_error_fails():
    verdict, failures, _info = classify(
        _obs(
            "/",
            _body_with_anchors("/"),
            consoleErrors=[{"text": "TypeError: boom", "url": "https://alias/assets/x.js"}],
        )
    )
    assert verdict == "FAILED"
    assert any("unexpected console errors" in f for f in failures)


# ── benign exemption is scoped ───────────────────────────────────────────────


def test_known_benign_console_noise_is_informational_not_failure():
    verdict, failures, info = classify(
        _obs(
            "/novanet",
            _body_with_anchors("/novanet"),
            consoleErrors=[
                {
                    "text": "Failed to load resource: the server responded with a status of 404 ()",
                    "url": "https://arkadia-qzu4.onrender.com/api/codex/categories",
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
            "/novanet",
            _body_with_anchors("/novanet"),
            consoleErrors=[
                {
                    "text": "Failed to load resource: the server responded with a status of 404 ()",
                    "url": "https://arkadia-qzu4.onrender.com/api/some/other/route",
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


def test_no_retired_deployment_host_is_referenced():
    """The canonical origin is the Render alias. A retired host in the harness
    would make its evidence bind to a deployment that no longer exists."""
    src = _SCRIPT.read_text()
    assert "arkadia-kw64" not in src


# ── read-only / no credential ────────────────────────────────────────────────


def test_harness_is_read_only_and_credential_free():
    src = _SCRIPT.read_text()
    assert "Authorization" not in src, "harness must not send credentials"
    assert "git push" not in src
    assert "git commit" not in src
    for verb in ('method="POST"', "method='POST'", "PUT", "PATCH", "DELETE"):
        assert verb not in src, f"harness must not perform {verb}"
