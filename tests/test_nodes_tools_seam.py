"""Pass 06 — prove the api/nodes.py → kernel.tools de-inversion.

1. Architectural invariant: api/nodes.py no longer imports the kernel layer.
2. Behavioral preservation: /api/codex/personal still reports the real
   registered-tool count through the injected composition-root counter,
   keeps the historical fallback (4) without injection, and survives a
   raising counter — all exercised through the REAL FastAPI route, no mocks
   of the boundary itself.
"""
from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.nodes as nodes


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(nodes.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_counter():
    saved = nodes._tools_counter
    yield
    nodes._tools_counter = saved


# ── 1. Architectural invariant ────────────────────────────────────────────────

def test_nodes_has_no_kernel_import():
    """AST-level check: api/nodes.py contains no import of the kernel layer
    (comments/docstrings mentioning kernel are fine — imports are not)."""
    import ast

    tree = ast.parse(open(nodes.__file__).read())
    for node_ in ast.walk(tree):
        if isinstance(node_, ast.Import):
            for a in node_.names:
                assert not a.name.startswith("kernel"), f"import {a.name}"
        elif isinstance(node_, ast.ImportFrom):
            assert not (node_.module or "").startswith("kernel"), (
                f"from {node_.module} import ..."
            )


# ── 2. Behavioral preservation through the real route ─────────────────────────

def test_codex_personal_uses_injected_counter(client):
    nodes.configure_tools_counter(lambda: 17)
    r = client.get("/api/codex/personal")
    assert r.status_code == 200
    assert r.json()["system"]["tools_count"] == 17


def test_codex_personal_fallback_without_injection(client):
    nodes._tools_counter = None
    r = client.get("/api/codex/personal")
    assert r.status_code == 200
    assert r.json()["system"]["tools_count"] == 4  # historical default


def test_codex_personal_survives_raising_counter(client):
    def boom():
        raise RuntimeError("kernel unavailable")

    nodes.configure_tools_counter(boom)
    r = client.get("/api/codex/personal")
    assert r.status_code == 200
    assert r.json()["system"]["tools_count"] == 4


def test_composition_root_wires_real_kernel_count(client):
    """wire_downstream_seams injects a counter backed by the REAL
    kernel.tools registry — the same value the old direct import produced."""
    from api.knowledge_routes import wire_downstream_seams
    from kernel.tools import list_tools

    wire_downstream_seams()
    r = client.get("/api/codex/personal")
    assert r.status_code == 200
    assert r.json()["system"]["tools_count"] == len(list_tools())
    assert r.json()["system"]["tools_count"] > 0
