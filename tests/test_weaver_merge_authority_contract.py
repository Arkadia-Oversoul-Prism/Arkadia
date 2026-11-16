"""Regression contract for GOV-03: Weaver assesses; humans merge."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "docs/control-plane/parallel-ui/SHARED-CONTRACTS.md"
DIRECTIVE = ROOT / "docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md"
AGENTS = ROOT / "AGENTS.md"
WORKER_DOC = ROOT / "docs/control-plane/WORKER_CONTRACT.md"
WORKER_JSON = ROOT / "docs/control-plane/worker.contract.json"
WORKER_SCHEMA = ROOT / "docs/control-plane/worker.contract.schema.json"
ADAPTER = ROOT / "weaver/execution_adapter.py"


def test_governance_sources_agree_on_human_only_execution():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "GOV-03" in content
        assert "human-only" in content.lower()
        assert "M1–M13" in content
        assert "eligibility" in content.lower()
        assert "may execute a merge" in content.lower() and "no agent" in content.lower()
        assert "routine merge is permitted only through weaver" not in content.lower()
        assert "bounded conditional merge delegation" not in content.lower()


def test_weaver_retains_assessment_but_not_execution():
    shared = SHARED.read_text(encoding="utf-8")
    assert "M1–M13 criteria are retained as the Weaver assessment rubric only" in shared
    assert "ELIGIBLE_TO_MERGE" in shared
    assert "HUMAN_AUTHORITY_REQUIRED" in shared
    assert "MERGED" in shared
    assert "assessment is advisory evidence only" in shared.lower()


def test_worker_contract_encodes_separate_assessment_and_execution():
    data = json.loads(WORKER_JSON.read_text(encoding="utf-8"))
    schema = json.loads(WORKER_SCHEMA.read_text(encoding="utf-8"))
    authority = data["authority"]
    assert authority["merge"] == "human_only"
    assert authority["merge_assessment"] == "weaver_eligibility_only"
    assert authority["merge_execution"] == "human_only"
    assert schema["properties"]["authority"]["properties"]["merge_assessment"]["const"] == "weaver_eligibility_only"
    assert schema["properties"]["authority"]["properties"]["merge_execution"]["const"] == "human_only"
    assert "merge_execution" in schema["properties"]["authority"]["required"]


def test_runtime_merge_and_deploy_remain_refused():
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert 'raise RuntimeError("merge is human-only")' in adapter
    assert 'raise RuntimeError("production deploy is human-only")' in adapter


def test_reserved_human_decisions_and_lane_rules_are_preserved():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "K15/K3" in content
        assert "production" in content.lower()
        assert "acceptance" in content.lower()
    assert all(f"Workstream {n}" in shared for n in range(1, 5))
    assert "one-open-PR-per-lane" in shared or "one open PR per lane" in shared


def test_governance_change_cannot_self_authorize_its_merge():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "this governance PR itself must be reviewed and merged by a human" in content.lower()
