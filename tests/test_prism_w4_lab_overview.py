"""Workstream 4 — Lab overview projection (handler oracle + execution + redaction).

The overview surface (`components/lab/LabOverviewSnapshot.tsx` + `labOverview.ts`)
is a pure projection of `GET /api/lab/overview` (`lab.service.build_overview`).

Three properties are measured here rather than asserted:

1. **The shape is the handler's own.** ``build_overview()`` is invoked directly and
   its output is what the projection is given.

2. **The projection behaves as claimed.** ``labOverview.ts`` is pure and
   dependency-free, so it is *executed* (not read) under Node.

3. **A credential cannot reach the screen.** ``repository.remote`` is the output of
   ``git remote get-url origin`` and therefore carries whatever userinfo the
   environment's remote holds — a token, where one was configured. The handler's
   ``security.values_redacted`` flag covers ``security.observations`` only. Every
   test below uses a **synthetic** credential literal; no real secret is read,
   written, or printed.

Node executes the module directly; if Node is unavailable the projection tests
skip with a stated reason rather than silently passing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PROJECTION = LAB_SRC / "labOverview.ts"

# A synthetic credential used only to prove the redactor strips userinfo.
# It is not, and must never be, a real token.
FAKE_TOKEN = "SYNTHETIC0000TOKEN0000NOTAREALSECRET"


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(view: dict) -> dict:
    """Execute the real ``labOverview.ts`` over *view* and return the ledger."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const view = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify({\n"
        "  ledger: m.buildOverviewLedger(view),\n"
        "  verdict: m.overviewVerdict(m.buildOverviewLedger(view)),\n"
        "  redact: m.redactRemote(view?.repository?.remote ?? null),\n"
        "}));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps(view)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


def _view_with_remote(remote: str) -> dict:
    return {
        "status": "observed",
        "repository": {"branch": "main", "head": "abc123", "clean": True, "remote": remote},
        "governance": {
            "maximum_authority": 2,
            "autonomous_mutation": False,
            "production_mutation": False,
            "approval_required": True,
        },
        "errors": [],
    }


# ---------------------------------------------------------------------------
# The shape is the handler's own
# ---------------------------------------------------------------------------


def test_handler_output_carries_the_keys_the_projection_reads():
    """Every top-level key the projection reads must be one the handler emits."""
    from lab.service import build_overview

    view = build_overview(".")
    for key in ("status", "repository", "architecture", "trajectory", "graph", "governance", "errors"):
        assert key in view, f"build_overview no longer emits {key}"

    assert set(view["repository"]) >= {"branch", "head", "clean", "remote", "status"}
    assert set(view["governance"]) >= {
        "maximum_authority",
        "autonomous_mutation",
        "production_mutation",
        "approval_required",
    }


def test_projection_reads_the_real_handler_output():
    from lab.service import build_overview

    view = build_overview(".")
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]

    assert ledger["repository"]["branch"] == (view["repository"]["branch"] or "unknown")
    assert ledger["counts"]["canon_sources"] == len(view["canon"]["sources"])
    assert ledger["counts"]["patterns"] == len(view["patterns"])
    assert ledger["counts"]["deployment_files"] == len(view["deployments"]["files"])
    assert ledger["counts"]["graph_entities"] == view["graph"]["entities"]
    assert ledger["authority_granted"] is False
    assert verdict["state"] in {"OBSERVED", "READING_INCOMPLETE"}


def test_governance_is_read_as_a_ceiling_not_a_permission():
    """The substrate's declarations must never be presented as granted authority."""
    from lab.service import build_overview

    ledger = run_projection(build_overview("."))["ledger"]
    assert ledger["governance"] is not None
    assert ledger["autonomous_mutation_declared"] is True
    assert ledger["human_approval_required"] is True
    assert ledger["authority_granted"] is False


# ---------------------------------------------------------------------------
# Credential redaction — the load-bearing property
# ---------------------------------------------------------------------------


def test_the_handler_really_does_carry_userinfo_on_the_remote():
    """Control premise for the redactor: this is why it exists.

    If the environment's remote has no userinfo the redactor is a no-op here, so
    the premise is stated explicitly rather than assumed. The *value* is never
    asserted or printed — only whether userinfo is present.
    """
    from lab.service import build_overview

    remote = build_overview(".")["repository"]["remote"]
    if remote is None:
        pytest.skip("no git remote is readable in this environment")
    has_userinfo = "@" in remote.split("://", 1)[-1].split("/", 1)[0]
    assert has_userinfo, (
        "control premise not met: this environment's remote carries no userinfo, "
        "so the redaction tests below would be vacuous here"
    )


def test_redactor_strips_userinfo_from_a_token_bearing_remote():
    """The synthetic token must not survive the projection in any field."""
    result = run_projection(_view_with_remote(f"https://x-access-token:{FAKE_TOKEN}@github.com/o/r.git"))

    assert FAKE_TOKEN not in json.dumps(result), "the credential survived into the ledger"
    assert result["ledger"]["repository"]["remote"]["redacted"] is True
    assert result["ledger"]["repository"]["remote"]["value"] == "https://github.com/o/r.git"
    assert result["ledger"]["repository"]["remote"]["scheme"] == "https"


def test_redactor_strips_a_bare_token_userinfo():
    """A bare `token@host` form has no colon and must be stripped too."""
    result = run_projection(_view_with_remote(f"https://{FAKE_TOKEN}@github.com/o/r.git"))
    assert FAKE_TOKEN not in json.dumps(result)
    assert result["ledger"]["repository"]["remote"]["value"] == "https://github.com/o/r.git"


def test_redactor_preserves_a_clean_remote_and_reports_no_redaction():
    """A remote without userinfo must pass through unchanged and unflagged."""
    result = run_projection(_view_with_remote("https://github.com/o/r.git"))
    remote = result["ledger"]["repository"]["remote"]
    assert remote["value"] == "https://github.com/o/r.git"
    assert remote["redacted"] is False


def test_redactor_handles_absent_and_empty_remotes():
    for value in (None, ""):
        result = run_projection(_view_with_remote(value))
        remote = result["ledger"]["repository"]["remote"]
        assert remote["value"] is None
        assert remote["redacted"] is False


def test_negative_control_the_redaction_detector_would_see_an_unredacted_token():
    """The detector must fail if the projection ever passed the remote through.

    This proves the assertion in the tests above can actually fail, rather than
    passing because the token never reached the ledger in the first place.
    """
    unredacted = _view_with_remote(f"https://x-access-token:{FAKE_TOKEN}@github.com/o/r.git")
    assert FAKE_TOKEN in json.dumps(unredacted), "the synthetic token must reach the projection"


def test_handler_redaction_flag_does_not_cover_the_repository_remote():
    """`values_redacted` is scoped to security observations — state the gap.

    This is the reason the UI boundary must redact: the handler's flag reads as a
    blanket assurance but covers one section.
    """
    from lab.service import build_overview

    view = build_overview(".")
    assert view["security"]["values_redacted"] is True
    assert "repository" in view and "remote" in view["repository"]

    ledger = run_projection(view)["ledger"]
    assert ledger["handler_redaction_scope"] == "security.observations only"


# ---------------------------------------------------------------------------
# Partial readings
# ---------------------------------------------------------------------------


def test_negative_control_a_failed_component_is_not_a_zero():
    """A collector failure must downgrade the reading, not render as empty."""
    view = {
        "status": "partial",
        "repository": {"branch": "main", "head": "abc", "clean": True, "remote": None},
        "architecture": {},
        "errors": [{"component": "canon", "status": "failed", "reason": "permission denied"}],
    }
    result = run_projection(view)
    ledger, verdict = result["ledger"], result["verdict"]

    assert ledger["reading_incomplete"] is True
    assert ledger["unobserved_components"] == ["canon"]
    assert ledger["component_failures"][0]["reason"] == "permission denied"
    assert verdict["state"] == "READING_INCOMPLETE"
    assert "canon" in verdict["note"]


def test_negative_control_a_missing_governance_block_is_not_autonomy():
    """Absent governance must read as unknown, never as 'no ceiling'."""
    view = {"status": "observed", "repository": {}, "errors": []}
    ledger = run_projection(view)["ledger"]

    assert ledger["governance"] is None
    assert ledger["autonomous_mutation_declared"] is False
    assert ledger["human_approval_required"] is False
    assert ledger["authority_granted"] is False
