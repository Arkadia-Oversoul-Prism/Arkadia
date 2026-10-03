from __future__ import annotations

import os
import shutil

import pytest

from solspire.project_execution_boundary import BoundaryError, run_isolated
from solspire.project_execution_service import candidate_patch_digest, execute_container_command


def test_runner_refuses_host_fallback_when_runtime_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("solspire.project_execution_boundary.shutil.which", lambda _: None)
    with pytest.raises(BoundaryError, match="refusing host execution"):
        run_isolated(image="agent@sha256:" + "a" * 64, workspace=tmp_path,
                     command=("/bin/true",))


def test_container_image_must_be_digest_pinned(tmp_path):
    with pytest.raises(BoundaryError, match="immutable sha256 digest"):
        execute_container_command(workspace=str(tmp_path), command=["true"],
                                  image="agent:latest")


def test_candidate_digest_changes_when_any_reviewed_content_changes():
    one = candidate_patch_digest([{"path": "README.md", "content": "one"}])
    two = candidate_patch_digest([{"path": "README.md", "content": "two"}])
    assert one != two


@pytest.mark.integration
def test_actual_oci_runtime_hardens_process_and_mount(tmp_path):
    """Live OCI acceptance test. Configure a digest-pinned image in CI to execute it."""
    image = os.environ.get("SOLSPIRE_TEST_AGENT_IMAGE", "")
    runtime = os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker")
    if not shutil.which(runtime) or "@sha256:" not in image or len(image.rsplit("@sha256:", 1)[-1]) != 64:
        pytest.skip("requires an installed container runtime and SOLSPIRE_TEST_AGENT_IMAGE pinned by sha256")
    tmp_path.chmod(0o777)
    result = run_isolated(
        image=image, workspace=tmp_path,
        command=("/bin/sh", "-c", "id -u; test ! -w /etc; touch /workspace/runtime-probe"),
        timeout_seconds=30, runtime=runtime,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[0] == "65532"
    assert (tmp_path / "runtime-probe").is_file()


def test_reviewed_patch_updates_canonical_store_and_records_workevent(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from solspire import project_store
    from solspire.project_execution_service import (
        apply_reviewed_project_patch, canonical_base_digest,
    )

    monkeypatch.setattr(project_store, "_DB_PATH", str(tmp_path / "projects.db"))
    file_row = project_store.create_file("project-1", "README.md", "before")
    base = canonical_base_digest("project-1")
    changes = [{"path": "README.md", "content": "after"}]
    digest = candidate_patch_digest(changes)
    captured = {}

    class WorkspaceManager:
        def get_for_subject(self, uid):
            return SimpleNamespace(id="workspace-owner")

    class WorkEventManager:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(to_dict=lambda: {"event_type": kwargs["event_type"],
                                                    "actor_ref": kwargs["actor_ref"]})

    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager", lambda: WorkspaceManager())
    monkeypatch.setattr("solspire.workevent_manager.get_workevent_manager", lambda: WorkEventManager())
    result = apply_reviewed_project_patch(
        subject_uid="owner-1", project_id="project-1",
        expected_base_digest=base, approved_patch_digest=digest,
        changes=changes, allowed_paths=["README.md"],
    )
    assert project_store.get_file(file_row["id"])["content"] == "after"
    assert result["approved_by"] == "owner-1"
    assert result["work_event"]["event_type"] == "PROJECT_PATCH_APPLIED"
    assert captured["witness_ref"] == f"sha256:{digest}"


def test_reviewed_patch_rejects_digest_mismatch_before_canonical_write(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from solspire import project_store
    from solspire.project_execution_service import (
        apply_reviewed_project_patch, canonical_base_digest,
    )

    monkeypatch.setattr(project_store, "_DB_PATH", str(tmp_path / "projects.db"))
    file_row = project_store.create_file("project-2", "README.md", "before")

    class WorkspaceManager:
        def get_for_subject(self, uid):
            return SimpleNamespace(id="workspace-owner")

    monkeypatch.setattr("solspire.workspace_manager.get_workspace_manager", lambda: WorkspaceManager())
    with pytest.raises(BoundaryError, match="exact candidate patch digest"):
        apply_reviewed_project_patch(
            subject_uid="owner-1", project_id="project-2",
            expected_base_digest=canonical_base_digest("project-2"),
            approved_patch_digest="wrong",
            changes=[{"path": "README.md", "content": "after"}],
            allowed_paths=["README.md"],
        )
    assert project_store.get_file(file_row["id"])["content"] == "before"


def test_disposable_workspace_changes_are_candidate_only(monkeypatch, tmp_path):
    from solspire import project_store
    from solspire.project_execution_service import (
        canonical_base_digest, collect_candidate_patch,
    )

    monkeypatch.setattr(project_store, "_DB_PATH", str(tmp_path / "projects.db"))
    file_row = project_store.create_file("project-3", "README.md", "canonical")
    base = canonical_base_digest("project-3")
    workspace = tmp_path / "disposable"
    workspace.mkdir()
    (workspace / "README.md").write_text("candidate", encoding="utf-8")
    (workspace / "new.txt").write_text("not-allowed", encoding="utf-8")

    candidate = collect_candidate_patch(
        project_id="project-3", workspace=str(workspace), base_digest=base
    )
    assert candidate["changed_paths"] == ["README.md"]
    assert candidate["persistence"] == "NOT_APPLIED"
    assert candidate["requires_human_review"] is True
    assert "new.txt" in candidate["rejected_paths"]
    assert project_store.get_file(file_row["id"])["content"] == "canonical"
