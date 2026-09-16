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
    # Force M01 done via completion index only
    move, _ = select_next_move(data, completion_index={"M01": "accepted"})
    assert move is not None
    assert move["id"] == "M07" or move["id"] == "M02" or move["id"] == "M04"
    # M02 depends on M01 — after M01 accepted, M02 is legal; M07 has no deps also pending
    # First in list order among legal: M02 (after M01), M04 depends M01, M07 no deps
    # Order in YAML: M01 done, M02 legal, should pick M02
    assert move["id"] == "M02"


def test_blocked_dependency_skips_move():
    data = yaml.safe_load(TRAJ.read_text())
    # M05 depends on M04; neither complete → never select M05 first
    move, _ = select_next_move(data)
    assert move["id"] != "M05"


def test_no_legal_move_when_all_accepted():
    data = yaml.safe_load(TRAJ.read_text())
    idx = {m["id"]: "accepted" for m in data["moves"]}
    move, blockers = select_next_move(data, completion_index=idx)
    assert move is None
    assert blockers


def test_dry_run_evidence(tmp_path, monkeypatch):
    # run against real repo root for trajectory files
    r = EngineeringRouter(repo_root=ROOT, session_id="test-session-dry", dry_run=True)
    out = r.run()
    assert out["status"] == "READY_FOR_REVIEW"
    assert out["next_move"]["id"] in ("M01", "M02A", "M07")
    assert out["dry_run"] is True
    evidence = Path(out["evidence_path"])
    assert evidence.is_file()
    human = evidence.parent / "WEAVER-ENGINEERING-RUN.md"
    assert human.is_file()
    assert "M01" in human.read_text()


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
