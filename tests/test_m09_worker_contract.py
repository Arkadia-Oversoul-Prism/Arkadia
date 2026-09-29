"""M09 — worker contract schema, instance, and lifecycle alignment."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from weaver.engineering_worker import CONTRACT_ID, LIFECYCLE_PHASES, EngineeringWorker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/control-plane/worker.contract.schema.json"
INSTANCE = ROOT / "docs/control-plane/worker.contract.json"
DOC = ROOT / "docs/control-plane/WORKER_CONTRACT.md"


def test_contract_artifacts_exist():
    assert SCHEMA.is_file()
    assert INSTANCE.is_file()
    assert DOC.is_file()


def test_instance_matches_contract_id():
    data = json.loads(INSTANCE.read_text())
    assert data["contract_id"] == "ARKADIA-WORKER-CONTRACT-v1"
    assert data["authority"]["merge"] == "human_only"
    assert data["authority"]["deploy"] == "human_only"
    assert data["authority"]["source"] == "architect"


def test_lifecycle_has_ten_phases():
    data = json.loads(INSTANCE.read_text())
    phases = [p["phase"] for p in data["lifecycle"]]
    assert phases == list(LIFECYCLE_PHASES)
    assert len(phases) == 10


def test_prohibitions_include_merge_deploy():
    data = json.loads(INSTANCE.read_text())
    assert "autonomous_merge" in data["prohibitions"]
    assert "autonomous_deploy" in data["prohibitions"]


def test_worker_emits_contract_and_stops():
    w = EngineeringWorker(repo_root=str(ROOT), session_id="m09-test", dry_run=True)
    out = w.run()
    assert out["contract_id"] == CONTRACT_ID
    assert out["merge"] is False
    assert out["deploy"] is False
    assert out["continues_to_next_move"] is False
    assert "TERMINATE" in out["phases_completed"]


def test_jsonschema_if_available():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text())
    data = json.loads(INSTANCE.read_text())
    jsonschema.validate(instance=data, schema=schema)


def test_doc_describes_authority_chain():
    text = DOC.read_text()
    assert "Architect" in text
    assert "Human Review" in text
    assert "NullExecutionAdapter" in text
