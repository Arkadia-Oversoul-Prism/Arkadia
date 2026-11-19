"""The canonical session-view read must assert its HTTP status.

``f4f372ff`` replaced the racy ``expect_response`` capture with an explicit
read, but the capture object was also what carried ``.status``. The assertion
``if session_view_response.status != 200`` was deleted with it and never
re-established: the reader still returned ``status``, the call site discarded
it.

That is a real weakening. A ``401`` or ``500`` response can still carry a JSON
body with the expected keys, so a harness that reads the body without checking
the status would accept an unauthenticated or failed read as a valid canonical
view and report PASS.

These tests pin the status assertion at three levels:

* behaviour \u2014 the pure predicate accepts 200 and rejects 401/500;
* wiring \u2014 the call site evaluates the predicate against the explicit read
  before extracting the body;
* preservation \u2014 the eight substrate assertions, the fail-closed exit, the
  authenticated-identity requirement and the poll all remain intact.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "web" / "arkadia_console" / "exercise_mission_workspace.py"
WORKSPACE = (
    REPO / "web" / "arkadia_console" / "src" / "components" / "lab" / "MissionWorkspace.tsx"
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


def _load_harness_module():
    """Import the harness module without executing ``main()``.

    The module imports ``playwright`` at top level, which is not installed in
    every test environment. The status predicate is pure, so it is loaded from
    source with a stub for the browser dependency.
    """
    spec = importlib.util.spec_from_file_location("_exercise_mission_workspace", HARNESS)
    assert spec and spec.loader, "could not build a module spec for the harness"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        if "playwright" not in str(exc):
            raise
        pytest.skip("playwright is not installed in this environment")
    return module


# -- behaviour: the predicate itself ------------------------------------------


def test_http_200_passes():
    """A 200 read is a valid canonical view and must not record a failure."""
    module = _load_harness_module()
    assert module._canonical_session_view_status_failure({"status": 200, "body": {}}) is None


def test_http_401_fails():
    """An unauthenticated read must be a failure, not a silently accepted body."""
    module = _load_harness_module()
    failure = module._canonical_session_view_status_failure(
        {"status": 401, "body": {"session": {"state": "READY_FOR_REVIEW"}}}
    )
    assert failure is not None, "a 401 read must record a failure"
    assert "401" in failure
    assert "200" in failure


def test_http_500_fails():
    """A server error must be a failure even if the body looks well-formed."""
    module = _load_harness_module()
    failure = module._canonical_session_view_status_failure(
        {"status": 500, "body": {"session": {"state": "READY_FOR_REVIEW"}}}
    )
    assert failure is not None, "a 500 read must record a failure"
    assert "500" in failure


def test_a_missing_status_is_not_treated_as_success():
    """Absent status must fail closed rather than default to a pass."""
    module = _load_harness_module()
    assert module._canonical_session_view_status_failure({"body": {}}) is not None


# -- wiring: the call site must use the explicit read -------------------------


def test_the_status_assertion_is_evaluated_against_the_explicit_read():
    """The status must come from ``_read_canonical_session_view``, not a capture.

    This is the exact defect: the read result was subscripted straight to
    ``["body"]``, discarding the status the reader had already returned.
    """
    harness = _read(HARNESS)

    # The defective form must be gone.
    assert '_read_canonical_session_view(page, session_id)["body"]' not in harness, (
        "the harness must not discard the read result's status by subscripting "
        "straight to the body"
    )

    # The full result must be preserved and the predicate applied to it.
    assert "session_view_read = _read_canonical_session_view(page, session_id)" in harness
    assert "_canonical_session_view_status_failure(session_view_read)" in harness, (
        "the status assertion must be evaluated against the explicit read result"
    )

    # And the body must be extracted from the preserved result, after the check.
    assert 'session_view_payload = session_view_read.get("body")' in harness

    status_check = harness.index("_canonical_session_view_status_failure(session_view_read)")
    body_extract = harness.index('session_view_payload = session_view_read.get("body")')
    assert status_check < body_extract, (
        "the status must be asserted before the body is extracted"
    )


def test_the_reader_still_returns_the_status():
    """The reader must keep returning status alongside the body."""
    harness = _read(HARNESS)
    tree = ast.parse(harness)
    reader = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_read_canonical_session_view"
        ),
        None,
    )
    assert reader is not None, "missing _read_canonical_session_view()"
    source = ast.get_source_segment(harness, reader) or ""
    assert "status: response.status" in source, (
        "the reader must return the HTTP status so the call site can assert it"
    )


# -- preservation: nothing else was weakened ----------------------------------


def test_the_eight_substrate_assertions_remain():
    """Every substrate assertion the harness proved before must still be proved."""
    harness = _read(HARNESS)
    required = [
        "canonical session view did not reach READY_FOR_REVIEW",
        "canonical session view did not expose the VERIFYING run",
        "canonical session view did not expose the run evidence",
        "authorization record did not report human origin",
        "pre-authorization refusal did not report the canonical SESSION != AUTHORIZATION boundary",
        "the trace did not preserve the human-acceptance boundary",
        "the run evidence reference did not resolve to a server-returned evidence record",
        "canonical substrate events missing from the session view",
    ]
    missing = [item for item in required if item not in harness]
    assert not missing, f"assertions were removed or loosened: {missing}"


def test_the_harness_still_fails_closed():
    """A failure must still produce a non-zero exit and a FAIL verdict."""
    harness = _read(HARNESS)
    assert 'evidence["verdict"] = "PASS" if not failures else "FAIL"' in harness
    assert "return 0 if not failures else 1" in harness


def test_the_harness_still_requires_an_authenticated_identity():
    """The authenticated-identity requirement must be untouched."""
    harness = _read(HARNESS)
    assert 'data-testid="test-identity-banner"' in harness
    assert 'data-testid="auth-threshold-signin"' in harness


def test_the_poll_is_still_present():
    """The fix must be robust to the poll, not dependent on its absence."""
    workspace = _read(WORKSPACE)
    assert "EXECUTE_POLL_MS" in workspace
    assert "setInterval" in workspace
    assert "getSessionView(sessionId)" in workspace


def test_no_assertion_was_skipped_or_marked_xfail():
    """The harness must not have gained a skip or xfail escape hatch."""
    harness = _read(HARNESS)
    assert not re.search(r"\bpytest\.(skip|xfail)\b", harness), (
        "the harness must not skip or xfail an assertion"
    )
