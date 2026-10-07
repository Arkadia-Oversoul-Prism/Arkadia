from growth.voice_of_belonging import ContentItem, ContentSource, due_slots, select_next_source


def source(source_id: str = "WORK-1") -> ContentSource:
    return ContentSource(
        source_id=source_id,
        provenance_refs=(f"knowledge://{source_id}",),
        thesis="You do not have to perform your significance here.",
    )


def test_cadence_is_deterministic_and_has_no_second_clock():
    assert [s.key for s in due_slots(0)] == ["MON_TRANSMISSION"]
    assert [s.key for s in due_slots(2)] == ["WED_WHISPER"]
    assert [s.key for s in due_slots(4)] == ["FRI_TRANSMISSION"]
    assert [s.key for s in due_slots(5)] == ["SAT_FIELD_NOTE"]


def test_source_selection_avoids_reuse():
    first = source("WORK-1")
    second = source("WORK-2")
    existing = [ContentItem("C-1", "VOICE_OF_BELONGING", first, "transmission")]
    assert select_next_source(sources=[first, second], existing=existing) is second


def test_publication_requires_human_approval():
    item = ContentItem("C-1", "VOICE_OF_BELONGING", source(), "transmission")
    item.transition("CANDIDATE")
    item.transition("DRAFT")
    item.transition("READY")

    try:
        item.transition("APPROVED")
    except ValueError as exc:
        assert "approval" in str(exc)
    else:
        raise AssertionError("approval without approval_ref must be rejected")

    item.transition("APPROVED", approval_ref="approval://human/1")
    assert item.externally_publishable is True
    item.transition("PUBLISHED")
    assert item.state == "PUBLISHED"


def test_ready_can_return_to_draft():
    item = ContentItem("C-1", "VOICE_OF_BELONGING", source(), "whisper")
    for state in ("CANDIDATE", "DRAFT", "READY"):
        item.transition(state)
    item.transition("DRAFT")
    assert item.state == "DRAFT"
