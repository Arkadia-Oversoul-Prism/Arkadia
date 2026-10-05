from pathlib import Path

from weaver.attention_bus import (
    AttentionEvent,
    JsonlAttentionOutbox,
    build_engineering_attention_event,
    classify_event,
)


def test_human_authority_routes_to_tasks_keep_and_push():
    event = AttentionEvent(
        event_id="EVT-1",
        event_type="AUTHORIZATION_REQUIRED",
        source="test",
        subject="proposal-1",
        human_authority_required=True,
        action_required=True,
        task_delivery=True,
        keep_delivery=True,
        push_delivery=True,
    )
    plan = classify_event(event)
    assert plan.channels == ("tasks", "keep", "push")
    assert plan.reason == "human authority boundary"


def test_routine_state_change_is_keep_only():
    event = AttentionEvent(
        event_id="EVT-2",
        event_type="FINDING_DISCOVERED",
        source="test",
        subject="opportunity-1",
        keep_delivery=True,
    )
    plan = classify_event(event)
    assert plan.channels == ("keep",)
    assert plan.reason == "recordable state change"


def test_outbox_is_idempotent_by_event_and_channel(tmp_path: Path):
    path = tmp_path / "attention.jsonl"
    outbox = JsonlAttentionOutbox(path)
    event = AttentionEvent(
        event_id="EVT-3",
        event_type="FINDING_DISCOVERED",
        source="test",
        subject="x",
        keep_delivery=True,
    )
    plan = classify_event(event)
    assert outbox.append(event, plan) is True
    assert outbox.append(event, plan) is False
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_engineering_result_becomes_downstream_attention_event():
    result = {
        "session_id": "engineering-1",
        "status": "READY_FOR_REVIEW",
        "next_move": {"id": "G12-A"},
        "evidence_path": "docs/control-plane/evidence/engineering-1/session-report.json",
    }
    event = build_engineering_attention_event(result)
    assert event.source == "weaver.engineering_worker"
    assert event.subject == "G12-A"
    assert event.human_authority_required is True
    assert event.task_delivery is True
    assert event.keep_delivery is True
    assert event.push_delivery is True
