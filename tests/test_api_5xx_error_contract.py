"""A 5xx response must not carry the exception's own text, and must log it.

Measured on the canonical deployment before this guard (main `fd0a4fdc`, whose
`/api/version` reported the same revision)::

    GET /api/codex/github-tree -> 502
    {"error":"Client error '401 Unauthorized' for url
     'https://api.github.com/repos/.../git/trees/main?recursive=1'"}

The handler was ``except Exception as e: return JSONResponse(502, {"error": str(e)})``
— no log, and the body named the internal upstream host and the credential
state. Three further handlers in ``api/main.py`` did the same on 500/502.

The detector below is source-level and runs over the live file, so a new
handler that echoes its exception fails this guard instead of shipping.
"""

from __future__ import annotations

import ast
import asyncio
import logging
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = REPO_ROOT / "api" / "main.py"

RESPONSE_CALLS = {"JSONResponse", "HTTPException"}


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _status_code(node: ast.Call) -> int | None:
    for kw in node.keywords:
        if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, int):
                return kw.value.value
    return None


def _carries(node: ast.AST, name: str) -> bool:
    """True when ``node`` reads the bound exception, directly or interpolated."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == name:
            return True
        if isinstance(child, ast.FormattedValue):
            for inner in ast.walk(child.value):
                if isinstance(inner, ast.Name) and inner.id == name:
                    return True
    return False


def disclosures(source: str) -> list[str]:
    """Return one description per 5xx response that echoes its exception."""
    tree = ast.parse(source)
    found: list[str] = []
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler) or not handler.name:
            continue
        for node in ast.walk(ast.Module(body=handler.body, type_ignores=[])):
            if not isinstance(node, ast.Call):
                continue
            if _call_name(node) not in RESPONSE_CALLS:
                continue
            status = _status_code(node)
            if status is None or status < 500:
                continue
            payload = [kw.value for kw in node.keywords if kw.arg in {"content", "detail"}]
            payload += [arg for arg in node.args if isinstance(arg, ast.Dict)]
            if any(_carries(part, handler.name) for part in payload):
                found.append(
                    f"line {node.lineno}: {_call_name(node)}({status}) echoes "
                    f"'{handler.name}'"
                )
    return found


# ── The live surface ──────────────────────────────────────────────────────────

def test_api_main_5xx_handlers_do_not_echo_the_exception():
    source = MAIN_PY.read_text(encoding="utf-8")
    assert disclosures(source) == [], (
        "a 5xx response returns the exception's own text; use "
        "api.http_failure.internal_failure_detail instead"
    )


def test_the_repaired_sites_use_the_shared_helper():
    source = MAIN_PY.read_text(encoding="utf-8")
    for operation in (
        "Oracle resonance",
        "Spiral Codex GitHub tree",
        "TTS synthesis",
        "Tool execution",
        "Personal note ingestion",
        "Oracle reply",
        "Spawn enqueue",
    ):
        assert f'_internal_failure_detail("{operation}")' in source, operation
    # The ingest route names the file the caller asked for, so it interpolates.
    assert '_internal_failure_detail(f"Ingest of {file_name!r}")' in source


# ── Negative control: the pre-repair shape must be detected ───────────────────

PRE_REPAIR = '''
async def github_tree():
    try:
        return await fetch()
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
'''

PRE_REPAIR_RAISE = '''
def run(tool, payload):
    try:
        return tool.run(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed: {exc}")
'''


def test_detector_flags_the_pre_repair_shape():
    assert disclosures(PRE_REPAIR), "the detector misses the measured defect"
    assert disclosures(PRE_REPAIR_RAISE), "the detector misses interpolated echoes"


def test_detector_is_silent_on_repaired_and_out_of_scope_shapes():
    repaired = '''
def run(tool, payload):
    try:
        return tool.run(payload)
    except Exception:
        raise HTTPException(status_code=500, detail=internal_failure_detail("Tool execution"))
'''
    # A 4xx echoes a caller-caused message, which is not server-side evidence.
    client_error = '''
def run(value):
    try:
        return parse(value)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
'''
    assert disclosures(repaired) == []
    assert disclosures(client_error) == []


# ── Behaviour: the measured route, driven with a failing collaborator ─────────

def test_github_tree_502_keeps_the_cause_in_the_log(monkeypatch, caplog):
    from api import main as api_main

    upstream = (
        "Client error '401 Unauthorized' for url "
        "'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1'"
    )

    async def refuse():
        raise RuntimeError(upstream)

    monkeypatch.setattr(api_main, "_fetch_github_tree", refuse)
    with caplog.at_level(logging.ERROR, logger="arkadia"):
        response = asyncio.run(api_main.github_tree())

    assert response.status_code == 502
    body = response.body.decode()
    assert "api.github.com" not in body
    assert "401" not in body
    assert "Spiral Codex GitHub tree failed" in body
    assert any("Spiral Codex GitHub tree failed" in r.getMessage() for r in caplog.records), (
        "the cause was neither returned nor logged"
    )
