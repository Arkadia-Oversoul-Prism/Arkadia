"""The hourly stop must be *composed*: the worker's outcome reaches the sovereign.

Two guards already pin the halves of this chain, and neither pins the seam between
them:

* `tests/test_engineering_router_status_truthfulness.py` proves the router *names* an
  unrecognized move status instead of silently skipping it.
* `tests/test_attention_truthfulness.py` proves `build_engineering_attention_event`
  *classifies* a `NO_LEGAL_MOVE`-with-blockers result as a pushed HIGH `WEAVER_BLOCKED`.

Both call the two halves directly. Nothing drives `EngineeringWorker.run()` — the
function the hourly scheduler actually invokes — and reads the downstream attention
event off its result. So the chain could be broken at the seam (the worker not
calling the builder, not recording to the outbox, not putting the event on the
result) while both half-guards stayed green, and the hourly stop would go silent
exactly as the live `NO_LEGAL_MOVE` regression did.

These tests exercise that seam end-to-end against a synthetic trajectory, so they
hold regardless of the live trajectories' completion state and write only inside a
`tmp_path` sandbox — the repository tree is never touched.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from weaver.engineering_worker import EngineeringWorker

TRAJECTORY_ENV = "ARKADIA_ENGINEERING_TRAJECTORY"
CONTROL_PLANE = Path("docs/control-plane")


def _write_trajectory(root: Path, moves: list[dict]) -> Path:
    """A router-loadable trajectory plus the spec files its moves point at."""
    spec = root / "spec.md"
    spec.write_text("# synthetic move spec\n", encoding="utf-8")
    for move in moves:
        move.setdefault("name", move["id"])
        move.setdefault("spec", "spec.md")
    path = root / "TRAJECTORY-SYNTHETIC.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "trajectory": {
                    "id": "TEST-COMPOSITION",
                    "status": "authorized-for-review-gated-execution",
                },
                "moves": moves,
            }
        ),
        encoding="utf-8",
    )
    return path


def _run_worker(monkeypatch: pytest.MonkeyPatch, root: Path, trajectory: Path) -> dict:
    """Run the worker the way the scheduler does: via the trajectory env binding."""
    monkeypatch.setenv(TRAJECTORY_ENV, str(trajectory))
    worker = EngineeringWorker(repo_root=str(root), session_id="composition-test", dry_run=True)
    return worker.run()


def test_unrecognized_frontier_is_composed_into_a_pushed_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The router's named defect must survive the worker into a pushed event.

    This is the live G12-A/G12-C shape: a frontier move at a status the router does
    not recognize. The router names it; the worker must project that naming as a
    HIGH `WEAVER_BLOCKED` on the push channel, or the sovereign never sees the stop.
    """
    trajectory = _write_trajectory(
        tmp_path,
        [
            {"id": "F-A", "status": "merged_acceptance_pending"},
            {"id": "F-B", "status": "pending", "depends_on": ["F-A"]},
        ],
    )
    result = _run_worker(monkeypatch, tmp_path, trajectory)

    assert result["status"] == "NO_LEGAL_MOVE"
    assert any("unrecognized move status" in b for b in result["blockers"])

    event = result["attention_event"]
    assert event["event_type"] == "WEAVER_BLOCKED"
    assert event["severity"] == "HIGH"
    assert event["action_required"] is True
    assert event["push_delivery"] is True

    plan = result["attention_delivery_plan"]
    assert "push" in plan["channels"]
    assert result["attention_outbox_recorded"] is True


def test_composed_block_is_durable_in_the_outbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A pushed event that was not recorded is not durable, so it is not a stop.

    The worker must append the event to its outbox; the in-memory result alone
    cannot survive the session.
    """
    trajectory = _write_trajectory(
        tmp_path, [{"id": "F-A", "status": "merged_acceptance_pending"}]
    )
    _run_worker(monkeypatch, tmp_path, trajectory)

    outbox = tmp_path / CONTROL_PLANE / "evidence" / "attention-events.jsonl"
    assert outbox.is_file(), "the worker recorded no attention event"
    records = [json.loads(line) for line in outbox.read_text(encoding="utf-8").splitlines()]

    # One record per delivery channel (the outbox is idempotent by event_id:channel),
    # each carrying the same composed event.
    assert {r["channel"] for r in records} == {"tasks", "keep", "push"}
    assert len({r["delivery_key"] for r in records}) == len(records)
    for record in records:
        assert record["event"]["event_type"] == "WEAVER_BLOCKED"
        assert record["event"]["severity"] == "HIGH"


def test_clean_completion_stays_quiet_through_the_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Negative control: the composition must not turn a healthy end into noise.

    A terminal-only trajectory is a genuine clean stop. If the seam reported it as
    blocked — a detector that flags every `NO_LEGAL_MOVE` — the hourly loop would
    push a false alert every hour. This is what keeps the truthfulness assertions
    above from being satisfied by "always blocked".

    Re-materialized from a strict xfail once `select_next_move` gained the
    `CLEAN_STOP_BLOCKER` sentinel (gate07/router-clean-stop-contract-01). The clean
    stop is now the sentinel and nothing else, so the assertions below are the live
    invariant rather than a recorded defect.
    """
    trajectory = _write_trajectory(tmp_path, [{"id": "DONE", "status": "completed"}])
    result = _run_worker(monkeypatch, tmp_path, trajectory)

    assert result["status"] == "NO_LEGAL_MOVE"
    assert any("no legal pending move" in b for b in result["blockers"])

    event = result["attention_event"]
    assert event["event_type"] == "WEAVER_STATE_CHANGED"
    assert event["severity"] == "INFO"
    assert event["action_required"] is False
    assert "push" not in result["attention_delivery_plan"]["channels"]


def test_routable_move_still_reaches_the_review_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The fix must not disturb ordinary routing: a pending move stops at review.

    `READY_FOR_REVIEW` must keep `human_authority_required` and push delivery — the
    worker may not continue to the next move or merge.
    """
    trajectory = _write_trajectory(
        tmp_path, [{"id": "NEXT", "status": "pending", "depends_on": []}]
    )
    result = _run_worker(monkeypatch, tmp_path, trajectory)

    assert result["status"] == "READY_FOR_REVIEW"
    assert result["merge"] is False
    assert result["deploy"] is False
    assert result["continues_to_next_move"] is False

    event = result["attention_event"]
    assert event["human_authority_required"] is True
    assert event["action_required"] is True
    assert "push" in result["attention_delivery_plan"]["channels"]


def test_negative_control_seam_detector_flags_a_worker_that_skips_the_builder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The detector must fail on a worker that never consults the attention builder.

    `_record_attention` is the seam. If it stopped calling
    `build_engineering_attention_event` (e.g. a refactor that returned the route
    result unchanged), the event key would vanish and the assertions above would
    error. This control pins that the *absence* of the composed event is a detected
    defect, not a vacuous pass.
    """
    trajectory = _write_trajectory(
        tmp_path, [{"id": "F-A", "status": "merged_acceptance_pending"}]
    )
    monkeypatch.setenv(TRAJECTORY_ENV, str(trajectory))
    worker = EngineeringWorker(repo_root=str(tmp_path), session_id="control", dry_run=True)
    monkeypatch.setattr(
        worker, "_record_attention", lambda result: result, raising=True
    )
    result = worker.run()

    # The router still names the defect, but nothing projected it downstream.
    assert result["status"] == "NO_LEGAL_MOVE"
    assert "attention_event" not in result
    assert not (tmp_path / CONTROL_PLANE / "evidence" / "attention-events.jsonl").exists()


def test_guard_is_selected_and_executed_by_a_workflow() -> None:
    """A guard no workflow executes is decoration.

    `weaver/engineering_worker.py` is not in any other workflow's path filter, and
    `tests/test_attention_truthfulness.py` was pinned by PR #323 yet executed by no
    workflow at all — so the seam and its attention half could both regress with every
    gate green. This file must appear in both the `push` and `pull_request` filters of
    its workflow (a guard absent from the pull_request filter is judged by nothing
    until after the merge) and be executed by a step, not merely triggered.
    """
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github/workflows/weaver-mvp2-validation.yml").read_text(
        encoding="utf-8"
    )
    # PyYAML parses the bare key `on` as the boolean True.
    workflow = yaml.safe_load(text)
    trigger = workflow.get(True, workflow.get("on"))
    assert isinstance(trigger, dict)

    guards = (
        "tests/test_attention_truthfulness.py",
        "tests/test_worker_attention_composition.py",
    )
    for event in ("push", "pull_request"):
        paths = (trigger.get(event) or {}).get("paths") or []
        for guard in guards:
            assert guard in paths, f"{event} filter does not select {guard}"

    push_paths = (trigger.get("push") or {}).get("paths") or []
    pr_paths = (trigger.get("pull_request") or {}).get("paths") or []
    assert set(push_paths) == set(pr_paths), (
        "push and pull_request filters must be identical, or a PR can introduce "
        "a surface the boundary only judges after merge"
    )

    # Executed, not merely triggered: both files must be named in a run step.
    assert "Worker→attention composition seam guard" in text
    step = text.split("Worker→attention composition seam guard", 1)[1]
    for guard in guards:
        assert guard in step, f"the seam guard step does not execute {guard}"
