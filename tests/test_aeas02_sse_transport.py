"""AEAS-02 — SSE transport correctness at the byte boundary.

The AEAS-01 Gate 3 acceptance captured, off the live wire, an EventStream whose
frame delimiters were the two literal characters backslash + "n" (0x5C 0x6E)
rather than a line feed (0x0A). The operator surface splits frames on a real
blank line, so it parsed zero events while the Events pane was satisfied by a
REST refresh. That is the defect these guards pin.

Every assertion below is on *bytes actually yielded by the endpoint*, never on
how the source looks. The captured malformed payload is retained as a negative
control so the defect stays reproducible.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import require_auth
from api.lab_routes import router

FIXTURE = Path(__file__).parent / "fixtures" / "aeas" / "sse-wire-captured-malformed.bin"

SUBJECT = "test-subject-aeas-02"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: {"uid": SUBJECT, "email": "aeas@test.invalid"}
    return TestClient(app)


def _session_id(client: TestClient) -> str:
    agent = client.post(
        "/api/lab/engineering/agents",
        json={
            "role": "WEAVER",
            "display_name": "AEAS-02 boundary agent",
            "capabilities": ["READ", "OBSERVE", "PROPOSE"],
            "write_allowed": False,
        },
    )
    assert agent.status_code == 200, agent.text
    session = client.post(
        "/api/lab/engineering/sessions",
        json={
            "workspace_ref": "workspace-aeas-02",
            "agent_id": agent.json()["agent_id"],
            "objective": "Establish SSE framing at the byte boundary.",
        },
    )
    assert session.status_code == 200, session.text
    return session.json()["session_id"]


def _first_frame_bytes(session_id: str) -> bytes:
    """Drain the endpoint's own streaming generator until the first data frame.

    The route function is called directly so the assertion is on the exact bytes
    the endpoint yields, with no test-client transport in between.
    """
    import asyncio

    from api.lab_routes import engineering_event_stream

    async def collect() -> tuple[bytes, str, str]:
        response = await engineering_event_stream(
            session_id, {"uid": SUBJECT, "email": "aeas@test.invalid"}
        )
        buf = b""
        chunks = 0
        async for chunk in response.body_iterator:
            buf += chunk.encode("utf-8") if isinstance(chunk, str) else chunk
            chunks += 1
            # Bounded so a malformed emitter fails the assertion instead of
            # spinning on keepalives forever.
            if b"data: " in buf and buf.endswith(b"\n\n"):
                break
            if chunks >= 4 or len(buf) > 16384:
                break
        return buf, response.media_type, response.headers.get("cache-control", "")

    body, media_type, cache_control = asyncio.run(collect())
    assert media_type == "text/event-stream"
    assert "no-transform" in cache_control  # a proxy must not buffer the stream
    return body


# -- emitter helpers ---------------------------------------------------------

def test_frame_helper_terminates_with_real_line_feeds():
    from api.lab_routes import _sse_frame

    frame = _sse_frame("agent", '{"a": 1}')
    assert frame.endswith("\n\n"), repr(frame)
    assert "\\n" not in frame, "literal backslash-n framing is not a frame boundary"


def test_comment_helper_terminates_with_real_line_feeds():
    from api.lab_routes import _sse_comment

    for text in ("connected", "keepalive"):
        comment = _sse_comment(text)
        assert comment == f": {text}\n\n"
        assert "\\n" not in comment


# -- byte boundary: the live endpoint ----------------------------------------

def test_event_stream_emits_real_lf_bytes_not_literal_backslash_n():
    """The load-bearing guard: actual bytes off the endpoint."""
    client = _client()
    body = _first_frame_bytes(_session_id(client))

    assert b"\n\n" in body, f"no real LF frame boundary in {body!r}"
    assert b"\\n\\n" not in body, f"literal backslash-n framing present in {body!r}"
    assert body.lstrip().startswith(b": connected"), repr(body)
    assert b"event: agent" in body, repr(body)


def test_event_stream_frames_are_parseable_by_a_conformant_parser():
    """A conformant SSE reader must recover the native event id."""
    import json

    client = _client()
    body = _first_frame_bytes(_session_id(client)).decode("utf-8")

    frames = [chunk for chunk in body.split("\n\n") if chunk.strip()]
    data_lines = [
        line[6:]
        for frame in frames
        for line in frame.split("\n")
        if line.startswith("data: ")
    ]
    assert data_lines, f"no data frame recovered from {body!r}"
    record = json.loads(data_lines[0])
    assert record["event_id"].startswith("AEV-")
    assert record["event_type"] == "SESSION_CREATED"
    assert record["sequence"] == 1


# -- negative control: the captured AEAS-01 payload ---------------------------

def test_captured_malformed_payload_is_retained_as_a_negative_control():
    """The exact bytes that escaped during AEAS-01 Gate 3 must stay reproducible."""
    raw = FIXTURE.read_bytes()
    assert raw, "fixture missing"
    assert b"\\n\\n" in raw, "captured payload no longer exhibits the defect"
    assert b"\n\n" not in raw, "captured payload is no longer malformed"


def test_captured_payload_parses_to_zero_frames():
    """Proof the harness detects the defect it claims to detect."""
    import json

    raw = FIXTURE.read_bytes().decode("utf-8")
    data_lines = [
        line[6:]
        for frame in raw.split("\n\n")
        for line in frame.split("\n")
        if line.startswith("data: ")
    ]
    assert data_lines == [], "malformed payload unexpectedly yielded frames"
    # Sanity: the payload really does carry the two native events.
    assert "AEV-19fecaf97608" in raw and "AEV-1559753b3eef" in raw
    assert json.loads(raw.split("data: ", 1)[1].split("\\n", 1)[0])["sequence"] == 1


def test_fixture_carries_no_credential_bearing_material():
    """Committed fixture must be secret-free."""
    import re

    raw = FIXTURE.read_bytes()
    assert not re.search(rb"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}", raw), "JWT present"
    assert not re.search(rb"AIza[A-Za-z0-9_-]{30,}", raw), "API key present"
    assert not re.search(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw), "email present"
    assert not re.search(rb"[Bb]earer\s+[A-Za-z0-9._-]{10,}", raw), "bearer token present"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
