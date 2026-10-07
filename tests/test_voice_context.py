"""Arkadia Voice — Phase 6 context resolution tests.

Proves the four required resolution states against canonical substrate state:

    KNOWN        exactly one owned referent
    AMBIGUOUS    multiple candidates → CLARIFY, never a guess
    UNKNOWN      no referent → name it explicitly
    UNAUTHORIZED referent exists but belongs to another subject

Also proves the CLARIFY loop: an operator disambiguation re-resolves the same
intent to KNOWN without re-capturing audio.
"""
from __future__ import annotations

import uuid

import pytest

from solspire.voice_context import resolve_context
from solspire.voice_intent import parse_intent


@pytest.fixture()
def voice_db(tmp_path, monkeypatch):
    db = str(tmp_path / "voice_ctx.db")
    import solspire.eden_ops as eo
    import solspire.project_manager as projm
    import solspire.proposal_manager as pm
    import solspire.voice_store as vs
    import solspire.workevent_manager as wem
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew

    for mod in (vs, wm, pm, wem, projm, eo, ew):
        monkeypatch.setattr(mod, "_DB_PATH", db)
    return db


def _intent(text: str):
    return parse_intent(text, "VE-CTX")


def _project(name: str, owner_uid: str | None = None):
    from solspire.project_manager import get_project_manager
    return get_project_manager().create(name, owner_uid=owner_uid)


def _note(title: str, note_type: str, user_id: str):
    from knowledge.pipeline import ingest
    return ingest(title=title, content=f"{title} — contextual note body",
                  note_type=note_type, user_id=user_id,
                  auto_tag=False, auto_embed=False, auto_link=False)


# ── CREATE ───────────────────────────────────────────────────────────────────

def test_create_with_fresh_name_is_known(voice_db):
    name = f"Voice Fresh {uuid.uuid4().hex[:10]}"
    context = resolve_context(_intent(f"create project called {name}"), "uid-a")
    assert context.resolution_status == "KNOWN"
    assert context.resolved_entities["name"] == name
    assert context.ambiguities == []
    assert context.source_event_id == "VE-CTX"


def test_create_with_existing_name_is_ambiguous_not_guessed(voice_db):
    name = f"Voice Collision {uuid.uuid4().hex[:10]}"
    project = _project(name, owner_uid="uid-a")
    context = resolve_context(_intent(f"create project called {name}"), "uid-a")
    assert context.resolution_status == "AMBIGUOUS"
    assert context.ambiguities[0]["reason"] == "NAME_COLLISION"
    assert any(c["id"] == project.id for c in context.candidate_entities["existing_projects"])


def test_create_without_name_is_unknown(voice_db):
    context = resolve_context(_intent("create project"), "uid-a")
    assert context.resolution_status == "UNKNOWN"
    assert context.ambiguities[0]["field"] == "name"
    assert context.ambiguities[0]["reason"] == "MISSING"


# ── MODIFY ───────────────────────────────────────────────────────────────────

def test_modify_single_owned_project_is_known(voice_db):
    name = f"Voice Solo {uuid.uuid4().hex[:10]}"
    project = _project(name, owner_uid="uid-a")
    context = resolve_context(_intent(f"rename project {name} to Renamed"), "uid-a")
    assert context.resolution_status == "KNOWN"
    assert context.resolved_entities["project"]["id"] == project.id


def test_modify_multiple_matches_is_ambiguous(voice_db):
    token = uuid.uuid4().hex[:8]
    _project(f"Voice Twin A {token}", owner_uid="uid-a")
    _project(f"Voice Twin B {token}", owner_uid="uid-a")
    context = resolve_context(_intent("rename project Voice Twin to Nope"), "uid-a")
    assert context.resolution_status == "AMBIGUOUS"
    assert context.ambiguities[0]["reason"] == "MULTIPLE_MATCHES"
    assert len(context.ambiguities[0]["candidates"]) >= 2


def test_modify_unknown_target_is_unknown(voice_db):
    context = resolve_context(
        _intent(f"rename project Voice Ghost {uuid.uuid4().hex[:8]} to X"), "uid-a")
    assert context.resolution_status == "UNKNOWN"
    assert context.ambiguities[0]["reason"] == "NO_MATCH"


def test_modify_missing_target_is_unknown(voice_db):
    context = resolve_context(_intent("rename project"), "uid-a")
    assert context.resolution_status == "UNKNOWN"
    assert context.ambiguities[0]["reason"] == "MISSING"


def test_modify_foreign_owned_project_is_unauthorized(voice_db):
    name = f"Voice Foreign {uuid.uuid4().hex[:10]}"
    _project(name, owner_uid="someone-else")
    context = resolve_context(_intent(f"rename project {name} to X"), "uid-a")
    assert context.resolution_status == "UNAUTHORIZED"
    assert context.ambiguities[0]["reason"] == "NOT_OWNED_BY_SUBJECT"


# ── EXECUTE ──────────────────────────────────────────────────────────────────

def test_execute_fs_list_resolves_path(voice_db):
    context = resolve_context(_intent("run the listing for vault"), "uid-a")
    assert context.resolution_status == "KNOWN"
    assert context.resolved_entities["path"] == "vault"
    assert context.resolved_entities["operation"] == "fs_list"


# ── SEARCH / ASK (informational) ─────────────────────────────────────────────

def test_search_is_known_and_lists_matches(voice_db):
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    token = uuid.uuid4().hex[:10]
    _note(f"Voice Query Doc {token}", "note", uid)
    context = resolve_context(_intent(f"find Voice Query Doc {token}"), uid)
    assert context.resolution_status == "KNOWN"
    assert context.resolved_entities["matches"] >= 1
    assert context.candidate_entities["matches"]


def test_ask_is_informational_and_known(voice_db):
    context = resolve_context(_intent("what is the vault policy?"), "uid-a")
    assert context.resolution_status == "KNOWN"
    assert context.resolved_entities["query"]


# ── transfer: the mission's "send the report to Jessica" case ────────────────

def test_transfer_with_multiple_reports_is_ambiguous(voice_db):
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    token = uuid.uuid4().hex[:10]
    _note(f"Voice Report {token} Alpha", "report", uid)
    _note(f"Voice Report {token} Beta", "report", uid)
    _note(f"Voice Jessica {token}", "person", uid)
    context = resolve_context(
        _intent(f"Send the report to Voice Jessica {token}"), uid)
    assert context.resolution_status == "AMBIGUOUS"
    fields = {a["field"] for a in context.ambiguities}
    assert "target" in fields
    assert len(context.candidate_entities["documents"]) >= 2


def test_transfer_clarification_resolves_to_known(voice_db):
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    token = uuid.uuid4().hex[:10]
    _note(f"Voice Report {token} Alpha", "report", uid)
    _note(f"Voice Report {token} Beta", "report", uid)
    _note(f"Voice Jessica {token}", "person", uid)
    intent = _intent(f"Send the report to Voice Jessica {token}")

    ambiguous = resolve_context(intent, uid)
    assert ambiguous.resolution_status == "AMBIGUOUS"

    resolved = resolve_context(
        intent, uid, {"target": f"Voice Report {token} Alpha"})
    assert resolved.resolution_status == "KNOWN"
    assert resolved.resolved_entities["document"]["label"].endswith("Alpha")
    assert resolved.resolved_entities["person"]["label"] == f"Voice Jessica {token}"


def test_transfer_with_multiple_recipients_is_ambiguous_on_recipient(voice_db):
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    token = uuid.uuid4().hex[:10]
    doc = _note(f"Voice Report {token} Solo", "report", uid)
    _note(f"Voice Jessica {token} One", "person", uid)
    _note(f"Voice Jessica {token} Two", "person", uid)
    assert doc
    context = resolve_context(_intent(f"Send the report to Voice Jessica {token}"), uid)
    assert context.resolution_status == "AMBIGUOUS"
    fields = {a["field"] for a in context.ambiguities}
    assert "recipient" in fields


def test_transfer_with_unknown_recipient_is_unknown(voice_db):
    uid = f"uid-{uuid.uuid4().hex[:8]}"
    token = uuid.uuid4().hex[:10]
    _note(f"Voice Report {token} Solo", "report", uid)
    context = resolve_context(
        _intent(f"Send the report to Voice Nobody {token}"), uid)
    assert context.resolution_status == "UNKNOWN"
    assert any(a["field"] == "recipient" for a in context.ambiguities)


# ── unknown intent ───────────────────────────────────────────────────────────

def test_unknown_intent_yields_unknown_context(voice_db):
    context = resolve_context(_intent("purple monkey dishwasher"), "uid-a")
    assert context.resolution_status == "UNKNOWN"
    assert context.ambiguities[0]["reason"] == "UNKNOWN_INTENT"
