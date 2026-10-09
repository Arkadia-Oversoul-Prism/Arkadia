"""Pin the ARK-01 signal producer to its frozen canonical schema.

`schemas/arkana/signal/1.0/arkana-signal.schema.json` is the canonical evidence
envelope for incoming Arkana signals and is admitted to the CP10 mutation
boundary, yet nothing referenced it from a test or a consumer. `POST
/api/arkana/signal/ingest` therefore emitted objects that failed their own
contract for ordinary model output:

* `interpretation.confidence` is a `number`-only map, but the route wrote
  `{"transcript": derived.get("transcript_confidence")}` -- a `null` when the
  model omitted the reading.
* `$defs/candidate` requires `status`, but `intent_candidates` / `references`
  were forwarded verbatim, so a candidate without a status was invalid.

These tests validate the exact object the route returns (the router endpoint is
called directly) plus the pure builder, against the real schema file, with a
negative control that proves the validator can witness the pre-fix shape and a
positive control that proves it accepts the shape the route now emits.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "arkana" / "signal" / "1.0" / "arkana-signal.schema.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.arkana_signal_routes import _build_signal, arkana_signal_ingest  # noqa: E402


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _errors(instance):
    return sorted(_validator().iter_errors(instance), key=lambda e: list(e.path))


def _minimal_signal(**overrides):
    base = dict(
        signal_id="sig_test",
        session_id="session_test",
        mime_type="audio/webm",
        duration_ms=1200,
        raw_hash="a" * 64,
        client_hash=None,
        client_streams={},
        derived={},
        model="gemini-3.8-flash",
    )
    base.update(overrides)
    return _build_signal(**base)


class _FakeRequest:
    """Minimal Request stand-in: the handler only calls `.json()`."""

    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Stub for the Gemini HTTP boundary only; returns canned model JSON."""

    model_text = "{}"

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kwargs):
        envelope = {
            "candidates": [
                {"content": {"parts": [{"text": type(self).model_text}]}}
            ]
        }
        return _FakeResponse(envelope)


@pytest.fixture
def route_env(monkeypatch):
    """Give the handler a key and stub only the external Gemini call."""
    import api.arkana_signal_routes as routes

    monkeypatch.setattr(routes, "GOOGLE_API_KEY", "test-key-not-a-credential", raising=False)
    monkeypatch.setattr(routes.httpx, "AsyncClient", _FakeAsyncClient, raising=False)
    return routes


def _ingest_body(*, duration_ms=1200, **extra):
    body = {
        "audio_base64": base64.b64encode(b"fake-audio").decode(),
        "mime_type": "audio/webm",
        "session_id": "session_test",
        "signal_id": "sig_test",
        "duration_ms": duration_ms,
    }
    body.update(extra)
    return body


# ---------------------------------------------------------------------------
# Conformance: the exact emitted object validates against the real schema.
# ---------------------------------------------------------------------------

def test_builder_output_conforms_with_empty_derivation():
    signal = _minimal_signal()
    assert _errors(signal) == []


def test_builder_output_conforms_when_model_omits_confidence():
    """An omitted transcript confidence must not write `null` into the map."""
    signal = _minimal_signal(derived={"transcript": "hello"})
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {}
    assert signal["interpretation"]["transcript"]["confidence"] is None


def test_builder_output_conforms_with_null_confidence():
    signal = _minimal_signal(
        derived={"transcript": "hi", "transcript_confidence": None}
    )
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {}


def test_builder_output_conforms_with_numeric_confidence():
    signal = _minimal_signal(
        derived={"transcript": "hi", "transcript_confidence": 0.42}
    )
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {"transcript": 0.42}


def test_builder_out_of_range_confidence_is_clamped_not_written_invalid():
    for raw, expected in ((1.9, 1.0), (-0.3, 0.0)):
        signal = _minimal_signal(derived={"transcript_confidence": raw})
        assert _errors(signal) == []
        assert signal["interpretation"]["confidence"] == {"transcript": expected}


def test_builder_candidates_gain_required_status():
    signal = _minimal_signal(
        derived={
            "intent_candidates": [{"value": "play music", "confidence": 0.4}],
            "references": [{"ref": "song://x"}],
        }
    )
    assert _errors(signal) == []
    assert signal["interpretation"]["intent_candidates"][0]["status"] == "unknown"
    assert signal["interpretation"]["references"][0]["status"] == "unknown"


def test_builder_preserves_a_valid_status_and_drops_non_objects():
    signal = _minimal_signal(
        derived={"intent_candidates": [{"status": "resolved", "value": "x"}, "junk", 7]}
    )
    assert _errors(signal) == []
    assert signal["interpretation"]["intent_candidates"] == [
        {"status": "resolved", "value": "x"}
    ]


def test_builder_rejects_an_unknown_status_value():
    signal = _minimal_signal(
        derived={"intent_candidates": [{"status": "definitely-not-in-enum"}]}
    )
    assert _errors(signal) == []
    assert signal["interpretation"]["intent_candidates"][0]["status"] == "unknown"


def test_builder_duration_is_integer_or_null():
    for raw, expected in ((900, 900), (-1, None), ("900", None), (None, None)):
        signal = _minimal_signal(duration_ms=raw)
        assert _errors(signal) == []
        assert signal["source"]["duration_ms"] == expected


# ---------------------------------------------------------------------------
# The route emits a conforming object through the handler itself.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_route_emits_a_schema_conforming_signal(route_env):
    payload = await arkana_signal_ingest(_FakeRequest(_ingest_body()))
    assert _errors(payload["signal"]) == []
    assert payload["signal"]["schema"] == "arkana.signal"
    assert payload["raw_audio_forwarded"] is True


@pytest.mark.asyncio
async def test_route_normalizes_ordinary_model_output(route_env):
    """The exact pre-fix failure shape must validate through the handler.

    The model returns a null transcript confidence and a candidate with no
    `status`; both are ordinary outputs, and both used to violate the schema.
    """
    route_env.httpx.AsyncClient = _fake_client_with(
        '{"transcript": "play the song", "transcript_confidence": null, '
        '"intent_candidates": [{"value": "play the song"}]}'
    )
    payload = await arkana_signal_ingest(_FakeRequest(_ingest_body()))
    signal = payload["signal"]
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {}
    assert signal["interpretation"]["intent_candidates"][0]["status"] == "unknown"


@pytest.mark.asyncio
async def test_route_rejects_an_invalid_audio_payload(route_env):
    """A malformed body must still fail closed; normalization is not a lax parse."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        await arkana_signal_ingest(_FakeRequest({"audio_base64": ""}))
    assert excinfo.value.status_code == 400


def _fake_client_with(model_text):
    class _Client(_FakeAsyncClient):
        pass

    _Client.model_text = model_text
    return _Client


# ---------------------------------------------------------------------------
# Negative control: the validator witnesses the pre-fix shape.
# ---------------------------------------------------------------------------

def test_negative_control_null_confidence_map_is_rejected():
    """Feeding the pre-fix construction to the validator must report a violation.

    This is the exact shape the route produced before the repair; if the
    validator did not flag it, the conformance assertions above would be vacuous.
    """
    signal = _minimal_signal(derived={"transcript": "hi", "transcript_confidence": None})
    signal["interpretation"]["confidence"]["transcript"] = None  # pre-fix write
    errors = _errors(signal)
    assert any(list(e.path) == ["interpretation", "confidence", "transcript"]
               for e in errors), errors


def test_negative_control_candidate_without_status_is_rejected():
    signal = _minimal_signal()
    signal["interpretation"]["intent_candidates"] = [{"value": "no status"}]
    errors = _errors(signal)
    assert any(list(e.path) == ["interpretation", "intent_candidates", 0]
               for e in errors), errors


def test_positive_control_validator_accepts_a_handwritten_minimal_object():
    """A schema-valid object must pass, so the validator is not rejecting all."""
    signal = {
        "schema": "arkana.signal",
        "schema_version": "1.0",
        "id": "sig",
        "session_id": "s",
        "created_at": "2026-10-09T00:00:00+00:00",
        "source": {"type": "microphone", "modality": "audio"},
        "raw": {"asset_ref": "client://x"},
        "streams": {},
        "interpretation": {"confidence": {"transcript": 0.5}},
        "provenance": {"derived_from": ["sig"]},
        "integrity": {"raw_preserved": True, "interpretation_is_derived": True},
    }
    assert _errors(signal) == []


def test_schema_file_is_the_canonical_contract():
    """The pinned schema must be the one the repository ships."""
    assert SCHEMA_PATH.is_file()
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert data["$id"] == "arkadia://schemas/arkana/signal/1.0"
    assert data["properties"]["schema"]["const"] == "arkana.signal"
