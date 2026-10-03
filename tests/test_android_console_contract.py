"""The native Arkadia Console client must satisfy the SolSpire server contract.

`arkadia-android/.../ConsoleApi.kt` issues the mobile surface's writes and reads against
the canonical SolSpire API. When the client's JSON body drifts from the request model the
route validates against, the failure is silent at build time (the payload is assembled at
runtime with `org.json`) and only appears as a `422` on a physical device.

These tests pin the mobile write path to the live request models and the read path to the
routes the served app actually exposes, so client/server drift fails in CI instead of on
the sovereign's phone.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

CONSOLE_API = (
    Path(__file__).resolve().parents[1]
    / "arkadia-android/app/src/main/kotlin/com/arkadia/os/ConsoleApi.kt"
)


def test_capture_payload_satisfies_the_workevent_request_model() -> None:
    """`emitCapture` must send every field `CreateWorkEventRequest` requires.

    Negative control: the payload as it stood before the fix (no `occurred_at`) is
    rejected by the model, proving this test detects the defect it claims to detect.
    """
    from solspire.workevent_router import CreateWorkEventRequest

    without_timestamp = {
        "event_type": "CAPTURED",
        "status": "RECORDED",
        "schema_version": "1",
        "artifact_refs": [],
        "state_after_ref": "Mobile observation",
        "work_ref": "captured text",
    }
    with pytest.raises(Exception):
        CreateWorkEventRequest(**without_timestamp)

    accepted = dict(without_timestamp, occurred_at=time.time())
    model = CreateWorkEventRequest(**accepted)
    assert model.occurred_at > 0


def test_console_client_sends_the_required_timestamp() -> None:
    """Source-level pin: the Kotlin body must carry `occurred_at`."""
    source = CONSOLE_API.read_text(encoding="utf-8")
    body = source[source.index("emitCapture"):]
    assert '.put("occurred_at"' in body, (
        "ConsoleApi.emitCapture must include occurred_at; "
        "CreateWorkEventRequest.occurred_at is required"
    )


def _served_pattern(path: str) -> re.Pattern[str]:
    """Turn an OpenAPI path into a regex that matches a concrete request path."""
    parts = [re.escape(segment) for segment in path.split("/")]
    return re.compile("/".join("[^/]+" if p.startswith(r"\{") else p for p in parts) + r"$")


def test_console_client_paths_exist_on_the_served_app() -> None:
    """Every endpoint literal in the client must resolve to a served route."""
    from api.main import app

    patterns = [_served_pattern(path) for path in app.openapi()["paths"]]
    source = CONSOLE_API.read_text(encoding="utf-8")
    fetched = {
        match.split("?")[0]
        for match in re.findall(r'"(/(?:solspire|api)/[^"]*)"', source)
    }
    assert fetched, "no endpoint literals found in ConsoleApi.kt"

    missing = sorted(
        path for path in fetched if not any(p.match(path) for p in patterns)
    )
    assert not missing, f"ConsoleApi references routes the app does not serve: {missing}"
