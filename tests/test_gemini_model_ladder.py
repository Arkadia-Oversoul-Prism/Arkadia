"""One Gemini text-model ladder, and no single-model Gemini text call site.

The defect this guards: ``api/ceo_chat_routes.py``, both routes in
``api/arkana_signal_routes.py`` and ``api/ims_products.py`` each pinned one model
identifier and issued one request, so one unavailable model turned the whole
surface into a 5xx or a permanent error string while the sibling surfaces
degraded to the next model. The repository also carried five independent copies
of the ladder, one of which had already drifted.

Two properties are asserted:

* exactly one module defines the ladder, and every module that builds a Gemini
  text-generation URL imports it;
* no Gemini text-generation URL carries a hardcoded model segment.

Each detector has a negative control fed the pre-repair shape, so the guard
cannot be disarmed by rewriting the call sites it is meant to judge.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MODULE = "kernel/gemini_models.py"

# Pinned so a change to the ladder is a visible, reviewable change rather than a
# silent widening or narrowing of every surface's fallback set.
RECORDED_LADDER = (
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
)

GEMINI_HOST = "generativelanguage.googleapis.com"
TEXT_ENDPOINTS = (":generateContent", ":streamGenerateContent")
LADDER_NAME = "GEMINI_MODELS"
CANONICAL_IMPORT_MODULE = "kernel.gemini_models"

_HARDCODED_MODEL_URL_RE = re.compile(r"models/gemini-[A-Za-z0-9.\-]+")


# ── detectors (fed real files and synthetic controls alike) ───────────────────

def speaks_gemini_text(source: str) -> bool:
    """True when the module constructs a Gemini text-generation request."""
    return GEMINI_HOST in source and any(e in source for e in TEXT_ENDPOINTS)


def hardcoded_model_urls(source: str) -> list[str]:
    """Gemini URL fragments that name a model as a literal instead of a value."""
    return _HARDCODED_MODEL_URL_RE.findall(source)


def imports_canonical_ladder(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module == CANONICAL_IMPORT_MODULE:
            if any(alias.name == LADDER_NAME for alias in node.names):
                return True
    return False


def ladder_definitions(source: str) -> list[str]:
    """Module-level names assigned a ladder (an assignment, not an import)."""
    names: list[str] = []
    for node in ast.parse(source).body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id == LADDER_NAME:
                names.append(target.id)
    return names


def tracked_sources() -> list[str]:
    """The guard's domain: every tracked Python module under api/ and kernel/."""
    out = subprocess.run(
        ["git", "ls-files", "--", "api", "kernel"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(p for p in out if p.endswith(".py"))


def _read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def _gemini_text_modules() -> list[str]:
    return [p for p in tracked_sources() if speaks_gemini_text(_read(p))]


# ── the ladder itself ─────────────────────────────────────────────────────────

def test_the_canonical_ladder_is_the_recorded_one():
    from kernel.gemini_models import GEMINI_MODELS

    assert tuple(GEMINI_MODELS) == RECORDED_LADDER


def test_the_ladder_has_exactly_one_definition():
    definers = [p for p in tracked_sources() if ladder_definitions(_read(p))]

    assert definers == [CANONICAL_MODULE], (
        f"the ladder must be defined once, in {CANONICAL_MODULE}; "
        f"import it instead of re-declaring it (found: {definers})"
    )


def test_every_gemini_text_module_imports_the_ladder():
    offenders = [p for p in _gemini_text_modules() if not imports_canonical_ladder(_read(p))]

    assert offenders == [], (
        "these modules build a Gemini text request without the canonical ladder: "
        f"{offenders}"
    )


def test_no_gemini_text_url_hardcodes_a_model():
    offenders = {p: hardcoded_model_urls(_read(p)) for p in _gemini_text_modules()}
    offenders = {p: v for p, v in offenders.items() if v}

    assert offenders == {}, (
        "a Gemini text URL must take its model from the ladder, not a literal: "
        f"{offenders}"
    )


# ── behaviour: one unavailable model must not fail the surface ────────────────

class _StubResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("stub", request=None, response=None)

    def json(self) -> dict:
        return self._payload


class _StubClient:
    """Serves 404 for every model except those in ``available``."""

    def __init__(self, available: dict[str, str]):
        self.available = available
        self.attempted: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kwargs):
        model = url.split("/models/", 1)[1].split(":", 1)[0]
        self.attempted.append(model)
        if model not in self.available:
            return _StubResponse(404, {})
        text = self.available[model]
        return _StubResponse(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


class _StubRequest:
    def __init__(self, body: dict):
        self._body = body

    async def json(self) -> dict:
        return self._body


@pytest.mark.asyncio
async def test_ceo_chat_degrades_to_the_next_model(monkeypatch):
    from api import ceo_chat_routes as route

    client = _StubClient({"gemini-2.0-flash": "hello from the fallback"})
    monkeypatch.setattr(route.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(route, "GOOGLE_API_KEY", "test-key")

    result = await route.ceo_chat(
        _StubRequest({"message": "hi"}), user={"uid": "test-uid"}
    )

    assert result["reply"] == "hello from the fallback"
    assert result["model"] == "gemini-2.0-flash"
    assert client.attempted == list(RECORDED_LADDER), (
        "the route must walk the ladder in order until a model answers"
    )


@pytest.mark.asyncio
async def test_ceo_chat_negative_control_a_single_model_still_fails(monkeypatch):
    """Feed the pre-repair shape: one pinned model, no fallback."""
    from api import ceo_chat_routes as route

    client = _StubClient({"gemini-2.0-flash": "unreachable"})
    monkeypatch.setattr(route.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(route, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(route, "GEMINI_MODELS", ("gemini-2.0-flash-exp",))

    with pytest.raises(HTTPException) as excinfo:
        await route.ceo_chat(_StubRequest({"message": "hi"}), user={"uid": "test-uid"})
    assert excinfo.value.status_code == 503


@pytest.mark.asyncio
async def test_arkana_signal_respond_degrades_to_the_next_model(monkeypatch):
    from api import arkana_signal_routes as route

    client = _StubClient({route.GEMINI_MODELS[-1]: "a reply from the fallback"})
    monkeypatch.setattr(route.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(route, "GOOGLE_API_KEY", "test-key")

    result = await route.arkana_signal_respond(
        _StubRequest({"signal": {}, "audio_base64": "AAAA"})
    )

    assert result["response"]["text"] == "a reply from the fallback"
    assert client.attempted == list(route._SIGNAL_MODELS)


@pytest.mark.asyncio
async def test_arkana_signal_respond_negative_control_a_single_model_still_fails(monkeypatch):
    from api import arkana_signal_routes as route

    client = _StubClient({})
    monkeypatch.setattr(route.httpx, "AsyncClient", lambda **kw: client)
    monkeypatch.setattr(route, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(route, "_SIGNAL_MODELS", ("gemini-3.8-flash",))

    with pytest.raises(HTTPException) as excinfo:
        await route.arkana_signal_respond(
            _StubRequest({"signal": {}, "audio_base64": "AAAA"})
        )
    assert excinfo.value.status_code == 502


# ── detector controls ─────────────────────────────────────────────────────────

def test_detector_flags_a_hardcoded_model_url():
    pre_repair = (
        'GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/'
        'gemini-1.5-flash:generateContent"\n'
    )

    assert hardcoded_model_urls(pre_repair) == ["models/gemini-1.5-flash"]


def test_detector_flags_a_text_call_site_without_the_ladder():
    pre_repair = (
        "async def go(key):\n"
        '    url = f"https://generativelanguage.googleapis.com/v1beta/models/'
        'gemini-3.8-flash:generateContent?key={key}"\n'
        "    return url\n"
    )

    assert speaks_gemini_text(pre_repair) is True
    assert imports_canonical_ladder(pre_repair) is False


def test_detector_flags_a_second_ladder_definition():
    second_copy = 'GEMINI_MODELS = [\n    "gemini-2.5-flash",\n]\n'

    assert ladder_definitions(second_copy) == ["GEMINI_MODELS"]


def test_detectors_are_silent_on_a_correct_module():
    repaired = (
        "from kernel.gemini_models import GEMINI_MODELS\n"
        "\n"
        "async def go(key, payload):\n"
        "    for model in GEMINI_MODELS:\n"
        '        url = f"https://generativelanguage.googleapis.com/v1beta/models/'
        '{model}:generateContent?key={key}"\n'
        "    return url\n"
    )

    assert speaks_gemini_text(repaired) is True
    assert imports_canonical_ladder(repaired) is True
    assert hardcoded_model_urls(repaired) == []
    assert ladder_definitions(repaired) == []
