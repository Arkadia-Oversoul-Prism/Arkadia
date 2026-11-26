"""Arkana streaming surface — key resolution and pool-reporting contract.

``api/arkana_stream_routes.py`` serves ``POST /api/commune/resonance/stream``, the SSE
path the console's Arkana surface reads. Its own comment says key resolution "mirrors the
non-streaming path (user -> pool -> env)", but measured at ``main`` ``bb19aabd`` nothing
pinned that, and the module carried a fallback that *looked* like one:

    from api.main import _get_current_user, GOOGLE_API_KEY
    ...
    except Exception:
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

``GOOGLE_API_KEY`` is never read in that function, so the ``except`` branch assigned a
dead local. A reader — or a later edit that assumed the name was live — would believe an
environment key had been applied on the error path when nothing was. The repair removes
the import and the dead assignment; the fallback that actually runs is the ``key_pool``
resolution two lines below, and this file binds it.

Three properties are pinned:

1. no ``GOOGLE_API_KEY`` is imported from ``api.main`` or assigned as a dead local;
2. the surface resolves through ``api.key_pool`` and reports both outcomes, so a cooling
   key is cooled and a working key is cleared (the pool contract the other chat surfaces
   hold);
3. a provider ``429`` actually reaches ``report_failure`` — behavioural, with the HTTP
   boundary patched and no mocking of the code under test.

Each detector is exercised by a negative control that feeds it the measured pre-repair
shape, plus a polarity control that a correct source must not be flagged.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "api" / "arkana_stream_routes.py"
STREAM_PATH = "/api/commune/resonance/stream"

_DEAD_KEY_IMPORT = re.compile(r"from\s+api\.main\s+import\s+[^\n]*\bGOOGLE_API_KEY\b")
_DEAD_KEY_ASSIGN = re.compile(r"^[ \t]*GOOGLE_API_KEY\s*=", re.MULTILINE)
_POOL_IMPORT = re.compile(r"from\s+api\.key_pool\s+import\s+([^\n]+)")


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _dead_key_fallbacks(src: str) -> list[str]:
    """Key-constant uses that are not a fallback: an unused import, a dead local."""
    defects: list[str] = []
    if _DEAD_KEY_IMPORT.search(src):
        defects.append("imports GOOGLE_API_KEY from api.main")
    if _DEAD_KEY_ASSIGN.search(src):
        defects.append("assigns GOOGLE_API_KEY as a local that is never read")
    return defects


def _pool_contract_defects(src: str) -> list[str]:
    """The key pool must be asked for a key and told each outcome."""
    names: set[str] = set()
    for match in _POOL_IMPORT.finditer(src):
        names.update(part.strip().split(" as ")[0] for part in match.group(1).split(","))
    return [n for n in ("acquire_key", "report_failure", "report_success") if n not in names]


def _source() -> str:
    return MODULE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Live contract
# ---------------------------------------------------------------------------


def test_streaming_route_is_served():
    """The path the console calls is a served route, on the method it uses."""
    from api.main import app

    paths = app.openapi()["paths"]
    assert STREAM_PATH in paths, f"{STREAM_PATH} is not served"
    assert "post" in paths[STREAM_PATH], f"{STREAM_PATH} does not accept POST"


def test_no_dead_key_fallback_in_the_live_module():
    defects = _dead_key_fallbacks(_source())
    assert defects == [], "misleading key fallback: " + ", ".join(defects)


def test_key_resolution_reports_to_the_pool():
    defects = _pool_contract_defects(_source())
    assert defects == [], "streaming surface does not use the pool: " + ", ".join(defects)


# ---------------------------------------------------------------------------
# Behavioural: a 429 reaches the pool
# ---------------------------------------------------------------------------


class _FakeResponse:
    status_code = 429

    async def aread(self) -> bytes:
        return b"quota exceeded"

    async def aiter_lines(self):
        return
        yield ""  # pragma: no cover - makes this an async generator


class _FakeStream:
    async def __aenter__(self) -> _FakeResponse:
        return _FakeResponse()

    async def __aexit__(self, *exc) -> bool:
        return False


class _FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    def stream(self, *args, **kwargs) -> _FakeStream:
        return _FakeStream()


@pytest.mark.asyncio
async def test_provider_429_cools_the_key(monkeypatch):
    import api.arkana_stream_routes as routes
    import api.key_pool as pool

    cooled: list[str] = []
    cleared: list[str] = []
    monkeypatch.setattr(routes, "httpx", types.SimpleNamespace(AsyncClient=_FakeClient))
    monkeypatch.setattr(pool, "acquire_key", lambda: None)
    monkeypatch.setattr(pool, "report_failure", cooled.append)
    monkeypatch.setattr(pool, "report_success", cleared.append)

    with pytest.raises(RuntimeError):
        async for _ in routes._stream_gemini(
            [{"role": "user", "content": "hello"}], "system", "TEST-KEY"
        ):
            pass

    assert cooled == ["TEST-KEY"], "a 429 must cool the key it was charged to"
    assert cleared == [], "a failing key must not be reported as a success"


# ---------------------------------------------------------------------------
# Negative and polarity controls
# ---------------------------------------------------------------------------

PRE_REPAIR = '''
    active_key = None
    user_id = None
    try:
        from api.main import _get_current_user, GOOGLE_API_KEY

        node_user = await _get_current_user(request)
    except Exception:
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
'''


def test_negative_control_flags_the_measured_pre_repair_shape():
    defects = _dead_key_fallbacks(PRE_REPAIR)
    assert len(defects) == 2, defects


def test_negative_control_flags_a_missing_report_failure():
    src = "from api.key_pool import acquire_key, report_success\n"
    assert _pool_contract_defects(src) == ["report_failure"]


def test_polarity_control_a_correct_source_is_not_flagged():
    src = (
        "from api.key_pool import acquire_key, report_failure, report_success\n"
        "active_key = acquire_key() or os.environ.get('GOOGLE_API_KEY', '')\n"
    )
    assert _dead_key_fallbacks(src) == []
    assert _pool_contract_defects(src) == []
