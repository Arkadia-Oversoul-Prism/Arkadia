"""Pin the ARK-01 signal producer to its contract without `jsonschema`.

`tests/test_arkana_signal_schema_conformance.py` validates the exact object the
route emits against the frozen schema, but it reaches the validator through
`pytest.importorskip("jsonschema")`, so in any environment that lacks the library
the guard silently disappears. Measured on this tree:

    PYTHONPATH=<no jsonschema> pytest tests/test_arkana_signal_schema_conformance.py -q
    # 2 passed, 14 skipped  -- every conformance assertion skipped

CI has no job that pins the ARK-01 route and installs `jsonschema`, so the pin
that was added to satisfy "the schema is decoration without a producer pin" was
itself decoration. This is the same lesson `tests/test_trajectory_schema_conformance.py`
was written to record: a guard that can be skipped for a missing install is
decoration; it must run under `pip install pytest` alone.

This guard is **stdlib-only**. It reads the schema with `json` and validates the
route's emitted object with a small validator that implements exactly the subset
of JSON Schema the ARK-01 contract uses:

* `type` (including the `["string", "null"]` union and `["number", "null"]`),
* `required`, `properties`, `additionalProperties: false` or a subschema,
* `enum`, `const`, `minimum`, `maximum`, `minLength`,
* `items`, `$ref` to `#/$defs/...`, `$defs`.

`format` is annotation-only in draft 2020-12 (`json.loads` never vetoes a string),
so it is listed as understood but not enforced.

The subset is stated rather than asserted to be complete; the schema file is
checked against it by `test_the_stdlib_validator_covers_every_keyword_the_schema_uses`,
so a schema rewrite that introduces an unsupported keyword fails here instead of
passing vacuously.

Negative controls prove the validator witnesses the pre-fix defects — a `null`
in the number-only confidence map and a candidate missing the required `status` —
and a positive control proves it accepts the shape the route now emits.
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

# JSON Schema keywords this guard understands. Anything else in the schema is a
# contract this validator would ignore, so the coverage test below fails closed.
_SUPPORTED_KEYWORDS = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "enum",
    "const",
    "minimum",
    "maximum",
    "minLength",
    "items",
    "$ref",
    "$defs",
    # Annotation-only in draft 2020-12; understood, deliberately not enforced.
    "format",
}


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _resolve(schema: dict, root: dict) -> dict:
    ref = schema.get("$ref")
    if ref is None:
        return schema
    if not ref.startswith("#/"):
        raise ValueError(f"only local $ref is supported, got {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _type_ok(instance, declared) -> bool:
    types = declared if isinstance(declared, list) else [declared]
    for name in types:
        if name == "null" and instance is None:
            return True
        if name == "boolean" and isinstance(instance, bool):
            return True
        if name == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
            return True
        if name == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
            return True
        if name == "string" and isinstance(instance, str):
            return True
        if name == "object" and isinstance(instance, dict):
            return True
        if name == "array" and isinstance(instance, list):
            return True
    return False


def _validate(instance, schema, root, path="$"):
    """Return a list of (path, message) violations. Stdlib-only, subset validator."""
    errors: list[tuple[str, str]] = []

    if "$ref" in schema:
        schema = _resolve(schema, root)

    if "const" in schema and instance != schema["const"]:
        errors.append((path, f"expected const {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append((path, f"not in enum {schema['enum']}"))
    if "type" in schema and not _type_ok(instance, schema["type"]):
        errors.append((path, f"expected type {schema['type']}, got {type(instance).__name__}"))

    if isinstance(instance, str) and "minLength" in schema and len(instance) < schema["minLength"]:
        errors.append((path, f"shorter than minLength {schema['minLength']}"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append((path, f"below minimum {schema['minimum']}"))
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append((path, f"above maximum {schema['maximum']}"))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append((f"{path}.{key}", "missing required property"))
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(_validate(value, properties[key], root, f"{path}.{key}"))
            elif additional is False:
                errors.append((f"{path}.{key}", "additional property not allowed"))
            elif isinstance(additional, dict):
                errors.extend(_validate(value, additional, root, f"{path}.{key}"))

    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            errors.extend(_validate(value, schema["items"], root, f"{path}[{index}]"))

    return errors


def _errors(instance) -> list[tuple[str, str]]:
    return sorted(_validate(instance, _load_schema(), _load_schema()))


def _iter_schema_keywords(node):
    """Yield every keyword name used anywhere in the schema."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("properties", "$defs"):
                # Both are name -> schema maps: the names are not keywords.
                for sub in value.values():
                    yield from _iter_schema_keywords(sub)
                continue
            yield key
            yield from _iter_schema_keywords(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_schema_keywords(item)


# ---------------------------------------------------------------------------
# The guard runs without `jsonschema`: this module never imports it.
# ---------------------------------------------------------------------------

def test_guard_does_not_import_jsonschema():
    """The whole point: this pin must survive an environment without the library."""
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "importorskip":
                imported.add("<importorskip>")
    assert "jsonschema" not in imported
    assert "<importorskip>" not in imported


def test_the_stdlib_validator_covers_every_keyword_the_schema_uses():
    """A schema rewrite that adds an unsupported keyword must fail here, not pass."""
    used = set(_iter_schema_keywords(_load_schema()))
    unsupported = used - _SUPPORTED_KEYWORDS
    assert not unsupported, (
        f"the schema uses keywords this stdlib validator ignores: {sorted(unsupported)}; "
        "extend the validator or the pin would pass vacuously"
    )


# ---------------------------------------------------------------------------
# The route's emitted object conforms, under the stdlib validator.
# ---------------------------------------------------------------------------

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
    model_text = "{}"

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kwargs):
        envelope = {"candidates": [{"content": {"parts": [{"text": type(self).model_text}]}}]}
        return _FakeResponse(envelope)


@pytest.fixture
def route_env(monkeypatch):
    import api.arkana_signal_routes as routes

    monkeypatch.setattr(routes, "GOOGLE_API_KEY", "test-key-not-a-credential", raising=False)
    monkeypatch.setattr(routes.httpx, "AsyncClient", _FakeAsyncClient, raising=False)
    return routes


def _ingest_body(**extra):
    body = {
        "audio_base64": base64.b64encode(b"fake-audio").decode(),
        "mime_type": "audio/webm",
        "session_id": "session_test",
        "signal_id": "sig_test",
        "duration_ms": 1200,
    }
    body.update(extra)
    return body


def test_builder_output_conforms():
    assert _errors(_minimal_signal()) == []


def test_builder_output_conforms_when_model_omits_confidence():
    signal = _minimal_signal(derived={"transcript": "hello"})
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {}
    assert signal["interpretation"]["transcript"]["confidence"] is None


def test_builder_normalizes_a_candidate_without_status():
    signal = _minimal_signal(derived={"intent_candidates": [{"value": "play"}]})
    assert _errors(signal) == []
    assert signal["interpretation"]["intent_candidates"][0]["status"] == "unknown"


def test_builder_rejects_illegal_confidence_readings():
    for raw in (None, True, "0.5", -0.2, 1.5):
        signal = _minimal_signal(derived={"transcript_confidence": raw})
        assert _errors(signal) == []
        expected = raw if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
        if expected is not None:
            expected = max(0.0, min(1.0, float(expected)))
        assert signal["interpretation"]["confidence"].get("transcript") == expected


@pytest.mark.asyncio
async def test_route_emits_a_conforming_signal(route_env):
    payload = await arkana_signal_ingest(_FakeRequest(_ingest_body()))
    assert _errors(payload["signal"]) == []
    assert payload["signal"]["schema"] == "arkana.signal"


@pytest.mark.asyncio
async def test_route_normalizes_ordinary_model_output(route_env):
    route_env.httpx.AsyncClient = type(
        "_Client",
        (_FakeAsyncClient,),
        {
            "model_text": '{"transcript": "play the song", "transcript_confidence": null, '
            '"intent_candidates": [{"value": "play the song"}]}'
        },
    )
    payload = await arkana_signal_ingest(_FakeRequest(_ingest_body()))
    signal = payload["signal"]
    assert _errors(signal) == []
    assert signal["interpretation"]["confidence"] == {}
    assert signal["interpretation"]["intent_candidates"][0]["status"] == "unknown"


# ---------------------------------------------------------------------------
# Negative controls: the stdlib validator witnesses the pre-fix shapes.
# ---------------------------------------------------------------------------

def test_negative_control_null_confidence_map_is_rejected():
    signal = _minimal_signal(derived={"transcript": "hi", "transcript_confidence": None})
    signal["interpretation"]["confidence"]["transcript"] = None  # pre-fix write
    errors = _errors(signal)
    assert any(path == "$.interpretation.confidence.transcript" for path, _ in errors), errors


def test_negative_control_candidate_without_status_is_rejected():
    signal = _minimal_signal()
    signal["interpretation"]["intent_candidates"] = [{"value": "no status"}]
    errors = _errors(signal)
    assert any(path == "$.interpretation.intent_candidates[0].status" for path, _ in errors), errors


def test_negative_control_missing_required_top_level_field_is_rejected():
    signal = _minimal_signal()
    del signal["provenance"]
    errors = _errors(signal)
    assert any(path == "$.provenance" for path, _ in errors), errors


def test_negative_control_additional_top_level_property_is_rejected():
    signal = _minimal_signal()
    signal["extra"] = 1
    errors = _errors(signal)
    assert any(path == "$.extra" for path, _ in errors), errors


def test_positive_control_accepts_a_handwritten_minimal_object():
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
