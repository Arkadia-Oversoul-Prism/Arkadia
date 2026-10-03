from __future__ import annotations

import pytest

from lab.engineering_lab.runtime import effective_tools
from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy, SandboxWriteDenied
from solspire.project_execution_service import collect_agent_candidate_patch


def test_candidate_proposal_never_writes_the_disposable_file(tmp_path):
    target = tmp_path / "README.md"
    target.write_text("canonical snapshot", encoding="utf-8")
    sandbox = Sandbox(SandboxPolicy(
        root=str(tmp_path), write_allowed=False, candidate_proposals_allowed=True, allowed_paths=("README.md",),
        command_allowlist=("echo",),
    ))
    proposal = sandbox.propose_edit("README.md", "agent suggestion", rationale="clarify the contract")
    assert proposal["content"] == "agent suggestion"
    assert proposal["path"] == "README.md"
    assert target.read_text(encoding="utf-8") == "canonical snapshot"
    assert sandbox.evidence()["operations"][-1]["operation"] == "propose_edit"


def test_candidate_proposal_requires_existing_allowlisted_path(tmp_path):
    (tmp_path / "README.md").write_text("before", encoding="utf-8")
    sandbox = Sandbox(SandboxPolicy(
        root=str(tmp_path), write_allowed=False, candidate_proposals_allowed=True, allowed_paths=("README.md",),
    ))
    with pytest.raises(SandboxWriteDenied):
        sandbox.propose_edit("../secret.txt", "no")
    with pytest.raises(SandboxWriteDenied):
        sandbox.propose_edit("new.txt", "no")


def test_human_authorization_must_include_candidate_write():
    tools = ("read", "list", "candidate_write")
    without = effective_tools(capabilities=("EDIT",), agent_tools=tools,
                              authorization_operations={"read", "list"})
    with_approval = effective_tools(capabilities=("EDIT",), agent_tools=tools,
                                   authorization_operations={"read", "list", "candidate_write"})
    assert "filesystem.propose_edit" not in without
    assert "filesystem.propose_edit" in with_approval


def test_agent_proposals_become_candidate_patch_without_persistence(monkeypatch, tmp_path):
    from solspire import project_store
    monkeypatch.setattr(project_store, "_DB_PATH", str(tmp_path / "projects.db"))
    file_row = project_store.create_file("project-1", "README.md", "before")
    result = collect_agent_candidate_patch(
        project_id="project-1", base_digest="base-digest",
        allowed_paths=("README.md",),
        turns=[{
            "tool_name": "filesystem.propose_edit",
            "tool_arguments": {"path": "README.md", "content": "after"},
            "observation": {"ok": True, "proposal": {"path": "README.md", "content": "after"}},
        }],
    )
    assert result["changed_paths"] == ["README.md"]
    assert result["persistence"] == "NOT_APPLIED"
    assert result["requires_human_review"] is True
    assert project_store.get_file(file_row["id"])["content"] == "before"



def test_project_execution_rejects_authorization_borrowed_from_another_session():
    from fastapi import HTTPException
    from api.lab_routes import _require_session_scoped_project_authorization

    class Runtime:
        def __init__(self, scope):
            self.scope = scope

        def get_authorization(self, authorization_ref, subject_uid):
            return {"authorization_id": authorization_ref, "scope_ref": self.scope}

    session = {"project_ref": "project-1", "authorization_ref": "AUTH-1"}
    with pytest.raises(HTTPException) as exc:
        _require_session_scoped_project_authorization(
            Runtime("different-session"), session, "session-1", "owner-1"
        )
    assert exc.value.status_code == 403
    _require_session_scoped_project_authorization(
        Runtime("session-1"), session, "session-1", "owner-1"
    )
