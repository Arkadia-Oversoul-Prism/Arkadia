"""HTTP error contract: a 5xx must not return the uncaught exception's text.

An uncaught exception's message is not public copy. It can carry filesystem
paths, SQL fragments, provider internals and configuration values, and it is
returned to whoever can reach the route. Measured on ``main`` ``bb19aabd``,
before this guard existed::

    $ # knowledge.pipeline.ingest patched to raise
    $ #   RuntimeError("sqlite3.OperationalError: unable to open database file /srv/app/vault/private/secret-index.db")
    POST /api/knowledge/ingest -> 500
    {"detail":"sqlite3.OperationalError: unable to open database file /srv/app/vault/private/secret-index.db"}

Sixteen 5xx sites in ``api/knowledge_routes.py`` were built that way, on routes
that are anonymously reachable (the router resolves identity *optionally*), and
the response was produced without logging the cause — so the operator lost the
diagnostic at the same moment the caller received it.

The second half of the contract is the reason the first half is safe: a 5xx that
hides the cause must **log** it. ``api/economic_seam_routes.py`` already returned
stable copy ("… inspect server logs …") and never wrote to a log at all, so the
instruction pointed at an empty record. Both halves are judged here.

The invariant, stated over the API surface:

1. No 5xx ``detail`` may be built from the exception the handler caught, unless
   the site carries the explicit ``curated-diagnostic`` marker — the provider
   layer raises curated configuration copy ("OPENAI_API_KEY not configured") that
   the caller genuinely needs.
2. A hidden cause must reach the log, which is asserted by *behaviour* (a canary
   in the exception message must appear in the captured log and must not appear
   in the response), not by matching source text.
3. The recorded disclosure inventory may only shrink: an unlisted module may not
   introduce a site, and a repaired module must be removed from the record.

Deliberately not repaired here (recorded in ``RECORDED_DISCLOSURES``):
``api/main.py`` and ``api/ceo_chat_routes.py`` are edited by an open pull request,
``api/lab_routes.py`` is an authority surface in ``tests/architecture/LAYER_MAP.py``
whose repair is sovereign-gated, and the remaining modules are a separate bounded
change. Discovery does not authorize a wider sweep.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api"

#: A site may return curated exception copy only when it says so at the site.
CURATED_MARKER = "curated-diagnostic"

#: 5xx sites still built from the caught exception's text. This record may only
#: shrink; see the module docstring for why each module is deferred.
RECORDED_DISCLOSURES: dict[str, int] = {
    # An open pull request edits this module's Gemini call path.
    "api/ceo_chat_routes.py": 1,
    # Admitted surface, but its model ladder is a separate bounded change.
    "api/arkana_signal_routes.py": 2,
    # Payment-provider error text; the provider message may carry a request id.
    "api/ims_products.py": 1,
    # Authority surface (tests/architecture/LAYER_MAP.py) — sovereign-gated.
    "api/lab_routes.py": 2,
    # Boot module, edited by an open pull request; budget-constrained.
    "api/main.py": 6,
    "api/plan_routes.py": 1,
    "api/source_routes.py": 2,
}

#: Modules this change repaired; they must measure zero, not "recorded".
REPAIRED_MODULES = ("api/knowledge_routes.py", "api/economic_seam_routes.py")


# ---------------------------------------------------------------------------
# Detector — module level, so the negative controls exercise the same code the
# live assertions use.
# ---------------------------------------------------------------------------


def _detail_references(detail: ast.expr, exception_name: str) -> bool:
    """Whether a ``detail=`` expression is built from the caught exception."""
    return any(
        isinstance(node, ast.Name) and node.id == exception_name
        for node in ast.walk(detail)
    )


def _is_server_error(call: ast.Call) -> bool:
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
    if name != "HTTPException":
        return False
    status = next((k.value for k in call.keywords if k.arg == "status_code"), None)
    return (
        isinstance(status, ast.Constant)
        and isinstance(status.value, int)
        and status.value >= 500
    )


def disclosed_details(source: str) -> list[tuple[int, int, str]]:
    """``(lineno, status, detail_source)`` for every leaking 5xx site in *source*.

    A site is a ``raise HTTPException(status_code=5xx, detail=<expr>)`` inside an
    ``except … as <name>`` handler where ``<expr>`` references ``<name>``. A site
    whose raise line or the three lines above it carry :data:`CURATED_MARKER` is
    an explicit, reviewed exception and is not reported.
    """
    tree = ast.parse(source)
    lines = source.split("\n")
    found: list[tuple[int, int, str]] = []

    def marked(lineno: int) -> bool:
        start = max(1, lineno - 3)
        return any(CURATED_MARKER in lines[i - 1] for i in range(start, lineno + 1))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            if handler.name is None:
                continue
            for call in (n for n in ast.walk(handler) if isinstance(n, ast.Call)):
                if not _is_server_error(call):
                    continue
                detail = next((k.value for k in call.keywords if k.arg == "detail"), None)
                if detail is None or not _detail_references(detail, handler.name):
                    continue
                if marked(call.lineno):
                    continue
                status = next(k.value.value for k in call.keywords if k.arg == "status_code")
                found.append(
                    (call.lineno, status, ast.get_source_segment(source, detail) or "")
                )
    return found


def module_disclosures() -> dict[str, int]:
    """Every leaking site under ``api/``, counted per module."""
    counts: dict[str, int] = {}
    for path in sorted(API_DIR.rglob("*.py")):
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        hits = disclosed_details(path.read_text(encoding="utf-8"))
        if hits:
            counts[relative] = len(hits)
    return counts


# ---------------------------------------------------------------------------
# Source-level invariants
# ---------------------------------------------------------------------------


def test_detector_flags_the_pre_repair_shape():
    """Negative control: the measured pre-repair handler must be reported."""
    pre_repair = (
        "async def route():\n"
        "    try:\n"
        "        return pipeline()\n"
        "    except Exception as e:\n"
        '        raise HTTPException(status_code=500, detail=str(e))\n'
    )
    assert disclosed_details(pre_repair) == [(5, 500, "str(e)")]


def test_detector_flags_an_interpolated_form():
    """The second shape in the corpus: an f-string carrying the cause."""
    pre_repair = (
        "def route():\n"
        "    try:\n"
        "        return send()\n"
        "    except RuntimeError as exc:\n"
        '        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}")\n'
    )
    assert [site[1] for site in disclosed_details(pre_repair)] == [502]


def test_detector_is_silent_on_the_curated_marker():
    """Positive control: a marked curated diagnostic is a decision, not a leak."""
    curated = (
        "def route():\n"
        "    try:\n"
        "        return send()\n"
        "    except RuntimeError as e:\n"
        "        # curated-diagnostic: the caller needs the configuration copy.\n"
        '        raise HTTPException(status_code=503, detail=str(e))\n'
    )
    assert disclosed_details(curated) == []


def test_detector_ignores_client_errors():
    """A 4xx may carry the validation message; only 5xx is the defect class."""
    client_error = (
        "def route():\n"
        "    try:\n"
        "        parse()\n"
        "    except ValueError as e:\n"
        '        raise HTTPException(status_code=400, detail=str(e))\n'
    )
    assert disclosed_details(client_error) == []


@pytest.mark.parametrize("module", REPAIRED_MODULES)
def test_repaired_modules_do_not_return_the_exception_text(module):
    source = (ROOT / module).read_text(encoding="utf-8")
    assert disclosed_details(source) == []


def test_the_recorded_inventory_may_only_shrink():
    """No module may exceed its recorded count; a repaired module is removed.

    ``measured <= recorded`` is the ratchet: a new site in an unlisted module
    (recorded as 0) fails, and a repair must lower the record in the same change.
    """
    measured = module_disclosures()
    growth = {
        module: count
        for module, count in measured.items()
        if count > RECORDED_DISCLOSURES.get(module, 0)
    }
    assert growth == {}, f"new exception-text disclosures: {growth}"


def test_the_record_does_not_describe_repaired_debt():
    """A recorded module that now measures zero is stale and must be pruned."""
    measured = module_disclosures()
    stale = [module for module in RECORDED_DISCLOSURES if measured.get(module, 0) == 0]
    assert stale == [], f"recorded modules with no remaining disclosure: {stale}"


def test_the_repaired_modules_are_not_recorded_as_debt():
    assert set(REPAIRED_MODULES).isdisjoint(RECORDED_DISCLOSURES)


# ---------------------------------------------------------------------------
# Behavioural invariants — the cause is hidden AND logged
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app, raise_server_exceptions=False)


def test_a_failing_knowledge_route_hides_the_cause_and_logs_it(client, monkeypatch, caplog):
    """The measured defect: the response carried the path, the log carried nothing."""
    import knowledge.pipeline

    canary = "/srv/app/vault/private/secret-index.db"
    calls: list[str] = []

    def boom(**kwargs):
        calls.append("called")
        raise RuntimeError(f"sqlite3.OperationalError: unable to open database file {canary}")

    monkeypatch.setattr(knowledge.pipeline, "ingest", boom)
    caplog.set_level(logging.ERROR, logger="arkadia.knowledge_routes")

    response = client.post("/api/knowledge/ingest", json={"title": "t", "content": "c"})

    assert calls, "the route did not reach the patched pipeline"
    assert response.status_code == 500
    assert canary not in response.text, "the internal cause was returned to the caller"
    assert "inspect server logs" in response.text
    assert canary in caplog.text, "the hidden cause was not logged"


def test_the_curated_provider_diagnostic_is_still_returned(client, monkeypatch):
    """Hiding internal causes must not hide the configuration copy operators use."""
    import providers.router

    def unavailable(**kwargs):
        raise RuntimeError("OPENAI_API_KEY not configured")

    monkeypatch.setattr(providers.router, "send", unavailable)

    response = client.post(
        "/api/knowledge/providers/send",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_API_KEY not configured"


def test_a_failing_economic_seam_scan_logs_the_cause(client, monkeypatch, caplog):
    """The route said "inspect server logs" while writing none."""
    import api.economic_seam_routes as routes
    from api.auth import require_sovereign
    from api.main import app

    canary = "/srv/app/data/economic_seams.db is locked"

    def boom():
        raise RuntimeError(canary)

    monkeypatch.setattr(routes, "scan_once", boom)
    app.dependency_overrides[require_sovereign] = lambda: {"uid": "test", "access_level": 3}
    caplog.set_level(logging.ERROR, logger="arkadia.economic_seam_routes")
    try:
        response = client.post("/api/economic-seams/scan")
    finally:
        app.dependency_overrides.pop(require_sovereign, None)

    assert response.status_code == 502
    assert canary not in response.text
    assert canary in caplog.text, "the cause behind the generic 502 was not logged"
