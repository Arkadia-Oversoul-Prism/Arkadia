"""Arkadia Voice — Phase 5 intent tests (bounded deterministic parser).

Covers the required vocabulary (ASK / SEARCH / CREATE / MODIFY / EXECUTE),
structured entity extraction, human-only refusal, confidence provenance, and
the rule that unknown input stays UNKNOWN instead of being guessed.
"""
from __future__ import annotations

from solspire.voice_intent import parse_intent

EVENT = "VE-TEST"


def parse(text: str):
    return parse_intent(text, EVENT)


# ── vocabulary ───────────────────────────────────────────────────────────────

def test_create_project_with_called_name():
    intent = parse("Create a project called Eden Pilot")
    assert intent.action == "CREATE"
    assert intent.entities["entity"] == "PROJECT"
    assert intent.entities["name"] == "Eden Pilot"
    assert intent.confidence == 1.0
    assert intent.source_event_id == EVENT
    assert intent.requested_effect == "CREATE_ENTITY"
    assert intent.canonical_intent_type == "Project"  # canonical router reused


def test_create_project_with_trailing_name():
    intent = parse("create project Eden Pilot")
    assert intent.action == "CREATE"
    assert intent.entities["name"] == "Eden Pilot"


def test_create_without_a_name_stays_incomplete_not_guessed():
    intent = parse("create project")
    assert intent.action == "CREATE"
    assert "name" not in intent.entities
    assert intent.confidence == 0.6  # action matched, entity missing


def test_modify_rename_extracts_target_and_new_value():
    intent = parse("rename project alpha to beta")
    assert intent.action == "MODIFY"
    assert intent.entities["target"] == "alpha"
    assert intent.entities["new_value"] == "beta"
    assert intent.entities["field"] == "name"


def test_modify_archive_maps_to_status_field():
    intent = parse("archive the project called Old Thing")
    assert intent.action == "MODIFY"
    assert intent.entities["field"] == "status"
    assert intent.entities["new_value"] == "archived"
    assert intent.entities["target"] == "Old Thing"


def test_execute_run_maps_to_fs_list_path():
    intent = parse("run the listing for vault")
    assert intent.action == "EXECUTE"
    assert intent.entities["operation"] == "fs_list"
    assert intent.entities["path"] == "vault"


def test_execute_without_path_defaults_to_workspace_root():
    intent = parse("run a listing")
    assert intent.action == "EXECUTE"
    assert intent.entities["path"] == "."


def test_send_maps_to_transfer_with_document_and_recipient():
    intent = parse("Send the report to Jessica")
    assert intent.action == "EXECUTE"
    assert intent.entities["operation"] == "transfer"
    assert intent.entities["entity"] == "DOCUMENT"
    assert intent.entities["target"] == "report"
    assert intent.entities["recipient"] == "Jessica"
    assert intent.confidence == 1.0


def test_send_without_recipient_is_incomplete():
    intent = parse("Send the report")
    assert intent.action == "EXECUTE"
    assert "recipient" not in intent.entities
    assert intent.confidence == 0.6


def test_search_extracts_query():
    intent = parse("find the report about potatoes")
    assert intent.action == "SEARCH"
    assert intent.entities["query"] == "the report about potatoes"
    assert intent.requested_effect == "SEARCH_KNOWLEDGE"


def test_ask_question_is_recognised():
    intent = parse("What is the status of Arkadia?")
    assert intent.action == "ASK"
    assert intent.entities["query"]
    assert intent.requested_effect == "ANSWER_QUESTION"


def test_ask_interrogative_start_without_question_mark():
    intent = parse("how do I resync the vault")
    assert intent.action == "ASK"


# ── unknown stays unknown ────────────────────────────────────────────────────

def test_unmatched_transcript_is_unknown_and_never_guessed():
    intent = parse("purple monkey dishwasher")
    assert intent.action == "UNKNOWN"
    assert intent.entities == {}
    assert intent.confidence is None
    assert intent.requested_effect == "NONE"


def test_empty_transcript_is_unknown():
    intent = parse("")
    assert intent.action == "UNKNOWN"
    assert intent.confidence is None


def test_whitespace_only_transcript_is_unknown():
    assert parse("   \n\t ").action == "UNKNOWN"


# ── human-only refusal (Engineering Lab canonical policy) ────────────────────

def test_merge_is_refused_as_human_only():
    intent = parse("merge the pull request")
    assert intent.entities["human_only"] is True
    assert intent.requested_effect == "REFUSED_HUMAN_ONLY"
    assert intent.confidence == 1.0


def test_deploy_is_refused_as_human_only():
    intent = parse("deploy to production")
    assert intent.entities["human_only"] is True
    assert intent.requested_effect == "REFUSED_HUMAN_ONLY"


def test_human_only_refusal_is_checked_before_action_parsing():
    # "create ... deploy" must still be refused, not turned into a CREATE.
    intent = parse("create a project and deploy it")
    assert intent.requested_effect == "REFUSED_HUMAN_ONLY"


# ── provenance ───────────────────────────────────────────────────────────────

def test_intent_carries_parser_and_canonical_type_provenance():
    intent = parse("find the quarterly numbers")
    assert intent.parser == "rule_based"
    assert intent.canonical_intent_type  # non-empty canonical IntentType


def test_confidence_is_rule_coverage_not_a_model_score():
    assert parse("create project alpha").confidence == 1.0
    assert parse("create project").confidence == 0.6
    assert parse("nonsense").confidence is None


def test_intent_ids_are_unique():
    ids = {parse("create project x").intent_id for _ in range(20)}
    assert len(ids) == 20
