"""Bootstrap tests: routing, dry-run, no merge, M01 selection without hardcoding."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from weaver.engineering_router import EngineeringRouter, select_next_move
from weaver.engineering_worker import EngineeringWorker
from weaver.execution_adapter import ForbiddenMergeAdapter, NullExecutionAdapter


ROOT = Path(__file__).resolve().parents[1]
TRAJ = ROOT / "docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml"


def _synthetic_trajectory(tmp_path: Path, moves: list[dict]) -> Path:
    """A routable trajectory that does not depend on the live trajectory's completion state.

    The live trajectory is a moving target: once every move is accepted the router
    correctly returns NO_LEGAL_MOVE, which would make any assertion about a selected
    move unfalsifiable. Routing-algorithm tests must therefore supply their own moves.
    """
    path = tmp_path / "SYNTHETIC-TRAJECTORY.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "trajectory": {
                    "id": "TEST-TRAJECTORY",
                    "status": "authorized-for-review-gated-execution",
                    "max_active_moves": 1,
                },
                "moves": moves,
            }
        )
    )
    return path


def test_trajectory_loads():
    data = yaml.safe_load(TRAJ.read_text())
    assert data["trajectory"]["id"] == "ARKADIA-TRUTHFULNESS-01"
    assert data["trajectory"]["max_active_moves"] == 1
    assert len(data["moves"]) >= 9


def test_router_selects_m01_from_current_state():
    data = yaml.safe_load(TRAJ.read_text())
    # Isolate: force all moves pending for routing algorithm check
    for m in data["moves"]:
        m["status"] = "pending"
    move, _ = select_next_move(data)
    assert move is not None
    assert move["id"] == "M01"


def test_router_does_not_select_m02_while_m01_pending():
    data = yaml.safe_load(TRAJ.read_text())
    for m in data["moves"]:
        m["status"] = "pending"
    move, _ = select_next_move(data)
    assert move["id"] != "M02"


def test_m02_blocked_until_m01_complete():
    data = yaml.safe_load(TRAJ.read_text())
    for m in data["moves"]:
        m["status"] = "pending"
    move, _ = select_next_move(data, completion_index={"M01": "accepted"})
    assert move is not None
    # With M01 accepted via index, first legal is M02 (depends_on M01)
    assert move["id"] == "M02"


def test_blocked_dependency_skips_move(tmp_path):
    # T02 depends on T01; neither complete → never select T02 first.
    # The dependent is listed FIRST so the router must actively skip it on the unmet
    # dependency rather than returning the prerequisite by list order.
    # IDs live in a T* namespace so they cannot collide with the live trajectory's
    # M* ACCEPT.json completion index, which the router also reads.
    traj = _synthetic_trajectory(
        tmp_path,
        [
            {"id": "T02", "name": "dependent", "status": "pending",
             "depends_on": ["T01"], "spec": "spec.md"},
            {"id": "T01", "name": "prerequisite", "status": "pending",
             "depends_on": [], "spec": "spec.md"},
        ],
    )
    data = yaml.safe_load(traj.read_text())
    move, _ = select_next_move(data)
    assert move is not None
    assert move["id"] != "T02"
    assert move["id"] == "T01"


def test_no_legal_move_when_all_accepted():
    data = yaml.safe_load(TRAJ.read_text())
    idx = {m["id"]: "accepted" for m in data["moves"]}
    move, blockers = select_next_move(data, completion_index=idx)
    assert move is None
    assert blockers


def test_dry_run_evidence(tmp_path):
    """Dry-run writes both evidence artifacts and never selects a non-move.

    Uses a synthetic routable trajectory so the assertion holds whether or not the
    live trajectory still has a legal move. The live trajectory's own terminal state
    is asserted separately in test_live_trajectory_dry_run_is_truthful.
    """
    traj = _synthetic_trajectory(
        tmp_path,
        [{"id": "T01", "name": "bootstrap", "status": "pending",
          "depends_on": [], "spec": "spec.md"}],
    )
    r = EngineeringRouter(
        repo_root=ROOT, session_id="test-session-dry", dry_run=True, trajectory_path=traj
    )
    out = r.run()
    assert out["status"] == "READY_FOR_REVIEW"
    assert out["next_move"] is not None
    assert out["next_move"]["id"] == "T01"
    assert out["dry_run"] is True
    evidence = Path(out["evidence_path"])
    assert evidence.is_file()
    human = evidence.parent / "WEAVER-ENGINEERING-RUN.md"
    assert human.is_file()
    # Must be an exact line, not a substring: "Next Legal Move: T01" would otherwise
    # satisfy a substring check even if the "Move:" line were wrong.
    assert "Move: T01" in human.read_text().splitlines()


def test_live_trajectory_dry_run_is_truthful():
    """The router's report on the LIVE trajectory must agree with its own evidence file.

    Accepts either outcome (a legal move, or NO_LEGAL_MOVE once every move is accepted)
    but requires the two artifacts to be mutually consistent and the status to be one
    the scheduler treats as a clean stop.
    """
    r = EngineeringRouter(repo_root=ROOT, session_id="test-live-dry", dry_run=True)
    out = r.run()
    assert out["status"] in ("READY_FOR_REVIEW", "NO_LEGAL_MOVE")
    human = Path(out["evidence_path"]).parent / "WEAVER-ENGINEERING-RUN.md"
    assert human.is_file()
    lines = human.read_text().splitlines()
    move_id = (out["next_move"] or {}).get("id", "NONE")
    assert f"Move: {move_id}" in lines
    assert f"Status: {out['status']}" in lines
    if out["status"] == "NO_LEGAL_MOVE":
        assert out["next_move"] is None
        assert out["blockers"]


def test_worker_stops_at_review_no_merge():
    w = EngineeringWorker(repo_root=str(ROOT), session_id="test-worker", dry_run=True)
    out = w.run()
    assert out.get("merge") is False
    assert out.get("deploy") is False
    assert out.get("continues_to_next_move") is False
    assert out.get("worker") in ("STOPPED_AT_REVIEW", "STOPPED")


def test_null_adapter_refuses_live_execution():
    adapter = NullExecutionAdapter()
    from weaver.execution_adapter import ExecutionRequest

    r = adapter.execute(
        ExecutionRequest(move_id="M01", plan={}, dry_run=False, repo_root=".")
    )
    assert r.ok is False


def test_forbidden_merge_adapter():
    f = ForbiddenMergeAdapter()
    with pytest.raises(RuntimeError, match="human-only"):
        f.merge()
    with pytest.raises(RuntimeError, match="human-only"):
        f.deploy()


def test_scheduler_workflow_exists_and_has_concurrency():
    wf = (ROOT / ".github/workflows/arkadia-engineering-scheduler.yml").read_text()
    assert "workflow_dispatch" in wf
    assert "schedule:" in wf
    assert "arkadia-engineering-session" in wf
    assert "cancel-in-progress: false" in wf
    assert "contents: read" in wf


def test_m01_not_hardcoded_in_router_source():
    src = (ROOT / "weaver/engineering_router.py").read_text()
    # Must not contain a forced first_run → M01 branch
    assert "if first_run" not in src
    assert 'run M01' not in src
