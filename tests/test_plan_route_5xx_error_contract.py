"""``POST /api/plan/run`` must not disclose its internal failure cause to the caller.

Plan execution is a consequential kernel operation: it runs the planner and then
executes the resulting steps. When a step failed, the handler raised

    raise HTTPException(status_code=500, detail=str(e))

so the caller received the caught exception's text — kernel internals, tool
output, filesystem paths — and the handler logged nothing, so the operator lost
the cause at the moment the caller was told it.

That is the class the repository is closing file by file (`api/main.py` in #729,
`api/knowledge_routes.py` in #718, `api/source_routes.py` in #735). Those
detectors are each scoped to their own file, so this instance would have
survived all three; `api/plan_routes.py` is touched by no other open change.

The detector below is an AST scan, not a text match: a 5xx ``HTTPException``
whose ``detail`` references the exception bound by its own ``except`` clause.
The two controls prove the detector can fail (pre-repair shape) and can stay
silent (a repaired handler, and a 4xx echo, which is a caller-caused message
and not server-side evidence).
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.auth import require_auth
from api.main import app

ROOT = Path(__file__).resolve().parents[1]
PLAN_ROUTES = ROOT / "api" / "plan_routes.py"

MARKER = "INTERNAL-MARKER-4c1f7d"

PRE_REPAIR = """
try:
    result = execute_plan(plan)
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
"""

PRE_REPAIR_FSTRING = """
try:
    result = execute_plan(plan)
except Exception as exc:
    raise HTTPException(status_code=502, detail=f"Plan execution failed: {exc}")
"""

REPAIRED = """
try:
    result = execute_plan(plan)
except Exception:
    logger.exception("plan execution failed")
    raise HTTPException(
        status_code=500,
        detail="Plan execution failed; inspect server logs for internal details.",
    )
"""

CALLER_CAUSED = """
try:
    body = await request.json()
except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
"""


def _handler_statements(handler: ast.ExceptHandler):
    """Every node in the handler's own scope, excluding nested function bodies."""
    stack = list(handler.body)
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                continue
            stack.append(child)


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _call_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def echo_sites(source: str, filename: str = "<source>") -> list[str]:
    """5xx responses whose body references the exception bound by their handler."""
    findings: list[str] = []
    for handler in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(handler, ast.ExceptHandler) or not handler.name:
            continue
        caught = handler.name
        for node in _handler_statements(handler):
            if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
                continue
            call = node.exc
            if _call_name(call.func) != "HTTPException":
                continue
            status = _keyword(call, "status_code")
            if not (isinstance(status, ast.Constant) and isinstance(status.value, int)):
                continue
            if status.value < 500:
                continue
            detail = _keyword(call, "detail")
            if detail is None:
                continue
            if any(
                isinstance(n, ast.Name) and n.id == caught for n in ast.walk(detail)
            ):
                findings.append(
                    f"{filename}:{node.lineno} status {status.value} echoes `{caught}`"
                )
    return findings


def test_the_live_plan_route_discloses_no_cause():
    assert echo_sites(PLAN_ROUTES.read_text(encoding="utf-8"), "api/plan_routes.py") == []


def test_detector_flags_the_measured_pre_repair_shape():
    """Negative control: the detector must fail on the shape this change repairs."""
    assert echo_sites(PRE_REPAIR), "the detector did not report the pre-repair shape"
    assert echo_sites(PRE_REPAIR_FSTRING), "the detector missed the f-string variant"


def test_detector_stays_silent_on_a_repaired_handler_and_a_4xx_echo():
    """Positive control: silence is only meaningful if the detector can be silent."""
    assert echo_sites(REPAIRED) == []
    # A 4xx echoes a caller-caused message; it is not server-side evidence.
    assert echo_sites(CALLER_CAUSED) == []


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_dependency_overrides():
    app.dependency_overrides.pop(require_auth, None)
    yield
    app.dependency_overrides.pop(require_auth, None)


def _authenticated():
    return {"uid": "planner", "role": "Guest", "access_level": 0}


def test_a_failing_step_returns_500_without_the_internal_cause(client, monkeypatch, caplog):
    import kernel.planner as planner

    def _boom(_plan):
        raise RuntimeError(MARKER)

    monkeypatch.setattr(planner, "plan_or_fallback", lambda *_a, **_k: {"steps": []})
    monkeypatch.setattr(planner, "validate_plan", lambda _plan: (True, ""))
    monkeypatch.setattr(planner, "execute_plan", _boom)

    app.dependency_overrides[require_auth] = _authenticated
    with caplog.at_level(logging.ERROR, logger="api.plan_routes"):
        response = client.post("/api/plan/run", json={"input": "do the thing"})

    assert response.status_code == 500
    assert MARKER not in response.text
    assert "inspect server logs" in response.json()["detail"]

    # The operator keeps the cause the caller was not given.
    assert MARKER in caplog.text
