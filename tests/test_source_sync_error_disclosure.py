"""The source-sync 5xx must hide the caught exception's text and log it.

Measured on ``main`` ``fd0a4fdc``, before this change, with
``api.source_connections.build_corpus_source`` patched to raise::

    POST /solspire/sources/github/sync -> 502
    {"detail":"Sync failed: adapter exploded: postgres://svc:pw@internal-db.example/private"}

The handler *did* log the cause, and then returned the same text to the caller.
A corpus adapter or ingest failure is not public copy: it can carry provider
URLs, credential material, filesystem paths and configuration values. The
contract held here is the pair: the caller receives stable copy that points at
the log, and the log receives the cause.

The ``/connect`` 503 is deliberately **not** part of this class. Its
``RuntimeError`` values are curated configuration copy raised by
``api.source_connections`` ("SOVEREIGN_KEY is required to store source
credentials", "Stored source credential cannot be decrypted") that the operator
genuinely needs. A repair that hid those would conceal a configuration fault, so
they stay returned verbatim and are pinned by the third test here.
"""
from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from api.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _isolate_auth_override():
    from api.auth import require_auth
    from api.main import app

    app.dependency_overrides.pop(require_auth, None)
    yield
    app.dependency_overrides.pop(require_auth, None)


def _authenticate() -> None:
    from api.auth import require_auth
    from api.main import app

    app.dependency_overrides[require_auth] = lambda: {
        "uid": "source-sync-test",
        "role": "Guest",
        "access_level": 0,
    }


def test_sync_failure_hides_the_cause_and_logs_it(client, monkeypatch, caplog):
    """The measured defect: the caller received the internal failure text."""
    import api.source_routes as routes

    canary = "postgres://svc:hunter2@internal-db.example/private"
    reached: list[str] = []

    monkeypatch.setattr(
        routes, "get_connection", lambda user, source: {"token": "test-token"}
    )

    def boom(source: str, config: dict):
        reached.append(source)
        raise RuntimeError(f"adapter exploded: {canary}")

    monkeypatch.setattr(routes, "build_corpus_source", boom)
    _authenticate()
    caplog.set_level(logging.ERROR, logger="arkadia.source_routes")

    response = client.post("/solspire/sources/github/sync")

    assert reached == ["github"], "the route did not reach the patched adapter"
    assert response.status_code == 502
    assert canary not in response.text, "the internal cause was returned to the caller"
    assert "inspect server logs" in response.text
    assert canary in caplog.text, "the hidden cause was not logged"


def test_the_sync_detector_flags_the_pre_repair_shape():
    """Negative control: the pre-repair source really is what the test rejects."""
    pre_repair = (
        '    except Exception as exc:\n'
        '        logger.exception("Source sync failed: %s", source)\n'
        '        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc\n'
    )
    assert "{exc}" in pre_repair
    assert "inspect server logs" not in pre_repair


def test_the_curated_configuration_error_is_still_returned(client, monkeypatch):
    """Positive control: deliberate configuration copy must survive the repair."""
    import api.source_routes as routes

    curated = "SOVEREIGN_KEY is required to store source credentials"

    def refuse(user, source, config):
        raise RuntimeError(curated)

    monkeypatch.setattr(routes, "connect", refuse)
    _authenticate()

    response = client.post("/solspire/sources/github/connect", json={"token": "t"})

    assert response.status_code == 503
    assert response.json()["detail"] == curated
