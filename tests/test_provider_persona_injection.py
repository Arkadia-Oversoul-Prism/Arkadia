"""Pass 05 — prove the providers/router.py → knowledge.db de-inversion.

1. Architectural invariant: providers/router.py no longer imports knowledge.db
   (source-level check — the same dependency the architecture fitness tests
   enforce, asserted here directly so this seam has a focused guard).
2. Behavioral preservation: persona prompt resolution still works through the
   injected composition-root resolver, against a REAL knowledge.db SQLite
   database (no mocks), including the missing-persona and error fallbacks.
"""
from __future__ import annotations

import os

import pytest

import providers.router as router
from knowledge import db as knowledge_db


# ── 1. Architectural invariant ────────────────────────────────────────────────

def test_router_has_no_knowledge_import():
    """providers/router.py must not reference the knowledge layer at all."""
    src = open(os.path.join(os.path.dirname(router.__file__), "router.py")).read()
    assert "knowledge.db" not in src
    assert "from knowledge" not in src
    assert "import knowledge" not in src


def test_resolver_defaults_to_none_without_injection(monkeypatch):
    monkeypatch.setattr(router, "_persona_resolver", None)
    assert router._resolve_persona_prompt("Architect") is None


# ── 2. Behavioral preservation against a real knowledge.db ───────────────────

@pytest.fixture
def real_persona_db(tmp_path, monkeypatch):
    db_path = tmp_path / "arkadia.db"
    monkeypatch.setattr(knowledge_db, "_DB_PATH", db_path)
    knowledge_db.execute(
        "INSERT INTO personas (name, system_prompt) VALUES (?, ?)",
        ("Pass05Sentinel", "You are the Pass05 sentinel."),
    )
    return db_path


def test_composition_root_resolver_reads_real_db(real_persona_db):
    """The production resolver (api.knowledge_routes.resolve_persona_system_prompt,
    wired into the router by api/main.py) resolves from a real knowledge.db."""
    from api.knowledge_routes import resolve_persona_system_prompt

    router.configure_persona_resolver(resolve_persona_system_prompt)
    try:
        assert router._resolve_persona_prompt("Pass05Sentinel") == "You are the Pass05 sentinel."
        # Missing persona → None (row-absent fallback preserved)
        assert router._resolve_persona_prompt("Nonexistent") is None
    finally:
        router.configure_persona_resolver(None)


def test_resolver_exception_falls_back_to_none(monkeypatch):
    """A raising resolver degrades to None — same contract as the old
    inline try/except around the knowledge.db query."""
    def boom(name: str):
        raise RuntimeError("db unavailable")

    router.configure_persona_resolver(boom)
    try:
        assert router._resolve_persona_prompt("Architect") is None
    finally:
        router.configure_persona_resolver(None)


def test_send_prefers_explicit_system_prompt(monkeypatch):
    """persona_name must not override an explicit system_prompt (old behavior)."""
    monkeypatch.setattr(router, "_persona_resolver", lambda name: "SHOULD NOT BE USED")
    captured = {}

    class FakeProvider:
        def authenticate(self):
            return True

        def capabilities(self):
            return ["chat"]

        def send(self, msgs, system_prompt=None, temperature=0.7, max_tokens=2048):
            captured["system_prompt"] = system_prompt
            return None

    monkeypatch.setattr(router, "select_provider", lambda preferred=None: FakeProvider())
    router.send(
        [{"role": "user", "content": "hi"}],
        system_prompt="explicit",
        persona_name="Architect",
    )
    assert captured["system_prompt"] == "explicit"
