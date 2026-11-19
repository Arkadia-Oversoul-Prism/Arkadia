"""The mission-workspace harness must not race the surface it measures.

``web/arkadia_console/exercise_mission_workspace.py`` drives the real
Engineering Lab mission path in a browser and asserts the substrate's
behaviour. Two of its assertions were *timing-dependent* rather than
behaviour-dependent, so the same commit could pass or fail:

1. **The canonical session-view read.** The workspace polls
   ``GET /sessions/{id}`` every ``EXECUTE_POLL_MS`` (1500 ms) while an execute
   request is in flight. The harness captured that endpoint with
   ``page.expect_response``, which resolves on the *first* matching response —
   frequently the pre-execute poll, whose session is still ``AUTHORIZED`` with
   no runs and no evidence. The assertion then reported
   ``canonical session view did not reach READY_FOR_REVIEW: AUTHORIZED`` even
   though the substrate had reached ``READY_FOR_REVIEW``.

2. **The authorization timeline.** The surface appends its
   ``originated_by human`` note only after its own post-authorize refresh
   resolves, which can land after the ``AUTHORIZED`` state is already visible.
   Sampling the timeline once could miss the note.

Both are harness defects, not product defects: the substrate was correct in
every observed run. These tests pin the *determinism* of the harness so the
race cannot be reintroduced, and they pin that the assertions themselves were
not weakened to make the gate green.

Measured evidence for the diagnosis (run 44461878090, job 135350372926):

* ``PASS: all routes and viewports satisfy the layout contract`` — the layout
  contract in the same step passed; only the mission flow failed.
* ``"session_state_after_execution": "READY_FOR_REVIEW"`` and
  ``"run_state": "VERIFYING"`` — the surface reached the review boundary.
* ``"canonical_session_view": {"session_state": "AUTHORIZED", "run_states": [],
  "evidence_ids": [], "event_types": ["SESSION_CREATED",
  "SESSION_TRANSITION"]}`` — the captured payload was the pre-execute poll.
* ``"api_execute_statuses": [400, 200]`` — the authorization boundary held.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "web" / "arkadia_console" / "exercise_mission_workspace.py"
WORKSPACE = REPO / "web" / "arkadia_console" / "src" / "components" / "lab" / "MissionWorkspace.tsx"


def _read(path: Path) -> str:
    assert path.exists(), f"missing {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


def _function_source(source: str, name: str) -> str:
    """Return the source of a top-level function, or fail."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing top-level function {name}()")


# -- the race that produced the false failure ---------------------------------


def test_session_view_is_read_explicitly_not_captured_from_a_poll():
    """The canonical view must be read after the surface settles.

    Capturing ``GET /sessions/{id}`` with ``expect_response`` races the
    workspace's own 1500 ms poll. The harness must instead read the view
    explicitly once the rendered state has settled.
    """
    harness = _read(HARNESS)

    # The racy capture must be gone: no expect_response waiting on the GET.
    assert not re.search(
        r"expect_response\(\s*\n\s*lambda response: response\.request\.method == \"GET\"",
        harness,
    ), (
        "the harness must not capture the session view with expect_response; the "
        "workspace polls that endpoint, so the first match is often the "
        "pre-execute poll and the assertion becomes a race"
    )

    # The explicit reader must exist and target the canonical endpoint.
    reader = _function_source(harness, "_read_canonical_session_view")
    assert "/api/lab/engineering/sessions/" in reader, (
        "the explicit reader must read the canonical session-view endpoint"
    )
    assert "arkadia_token" in reader, (
        "the explicit reader must authenticate with the surface's own bearer token"
    )

    # And it must actually be used for the assertions.
    assert "_read_canonical_session_view(page, session_id)" in harness, (
        "the harness must read the canonical view through the explicit reader"
    )


def test_session_view_read_happens_after_the_surface_settles():
    """The explicit read must be ordered after the rendered state settles.

    Reading the view before the surface has applied the execute result would
    reintroduce the same race in a different form.
    """
    harness = _read(HARNESS)
    settle = harness.find("includes('READY_FOR_REVIEW')")
    read = harness.find("_read_canonical_session_view(page, session_id)")
    assert settle != -1, "the harness must wait for the rendered review boundary"
    assert read != -1, "the harness must read the canonical view"
    assert settle < read, (
        "the canonical view must be read only after the surface has settled at "
        "READY_FOR_REVIEW; reading earlier can observe a pre-execute poll"
    )


def test_authorization_timeline_waits_for_the_note():
    """The human-origin note is appended asynchronously; the harness must wait.

    The surface records ``originated_by human`` after its post-authorize
    refresh resolves. A single sample of the timeline can miss it.
    """
    harness = _read(HARNESS)
    assert "originated_by human" in harness, "the assertion itself must remain"
    # A wait_for_function must guard the note before the failure is recorded.
    note_wait = harness.find("includes('originated_by human')")
    assert note_wait != -1, (
        "the harness must wait for the authorization note rather than sampling "
        "the timeline once"
    )
    failure = harness.find('failures.append("authorization record did not report human origin")')
    assert failure != -1, "the assertion must still be able to fail"
    assert note_wait < failure, (
        "the wait must precede the failure so a slow note is not reported as a "
        "missing human origin"
    )


# -- the assertions must not have been weakened -------------------------------


def test_the_substrate_assertions_are_still_present():
    """The repair must not have removed or loosened any substrate assertion.

    Every property the harness proved before the repair must still be proved.
    """
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
    assert "return 0 if not failures else 1" in harness, (
        "the harness must still exit non-zero when any assertion fails"
    )


def test_the_harness_still_requires_an_authenticated_identity():
    """The repair must not have relaxed the authenticated-identity requirement."""
    harness = _read(HARNESS)
    assert 'data-testid="test-identity-banner"' in harness
    assert 'data-testid="auth-threshold-signin"' in harness, (
        "the harness must still refuse a render that stopped at the sign-in threshold"
    )


# -- the surface behaviour the harness measures -------------------------------


def test_the_workspace_polls_the_session_view_during_execute():
    """The poll is why the capture raced; it must still exist.

    This is the mechanism that made ``expect_response`` unreliable. If the poll
    were removed the race would disappear for the wrong reason, so the poll is
    pinned here: the harness fix must be robust to it, not dependent on its
    absence.
    """
    workspace = _read(WORKSPACE)
    assert "EXECUTE_POLL_MS" in workspace, "the execute poll must still exist"
    assert "setInterval" in workspace, "the poll must still be interval-driven"
    assert "getSessionView(sessionId)" in workspace, (
        "the poll must still read the canonical session view"
    )


def test_the_workspace_reaches_ready_for_review_after_execute():
    """The surface must still settle at the review boundary the harness asserts."""
    workspace = _read(WORKSPACE)
    assert "READY_FOR_REVIEW" in workspace, (
        "the surface must still present the READY_FOR_REVIEW boundary"
    )
    assert "refreshView(session.session_id)" in workspace, (
        "the surface must still refresh its view after execute settles"
    )
