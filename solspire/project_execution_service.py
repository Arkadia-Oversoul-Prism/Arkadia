"""Governed project execution and reviewed canonical patch application."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from solspire.project_execution_boundary import BoundaryError, require_reviewed_patch


def _canonical_files(project_id: str) -> list[dict[str, Any]]:
    from solspire.project_store import get_file, list_files
    rows = []
    for item in list_files(project_id):
        full = get_file(str(item.get("id") or ""))
        if full and full.get("project_id") == project_id:
            rows.append(full)
    return sorted(rows, key=lambda row: str(row.get("name") or ""))


def canonical_base_digest(project_id: str) -> str:
    """Stable digest over canonical file IDs, names, MIME types and contents."""
    rows = _canonical_files(project_id)
    payload = [
        {"id": r["id"], "name": r["name"], "mime_type": r.get("mime_type", ""),
         "content": r.get("content", "")}
        for r in rows
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def create_disposable_workspace(subject_uid: str, project_id: str) -> dict[str, Any]:
    """Create a fresh per-execution copy, never exposing the canonical store path."""
    from solspire.project_canvas import prepare_project_workspace
    snapshot = prepare_project_workspace(subject_uid, project_id)
    temp_root = Path(tempfile.mkdtemp(prefix="arkadia-solspire-run-")).resolve()
    source = Path(snapshot["root"]).resolve()
    shutil.copytree(source, temp_root, dirs_exist_ok=True, symlinks=False)
    return {
        **snapshot,
        "root": str(temp_root),
        "canonical_base_digest": canonical_base_digest(project_id),
        "disposable": True,
    }


def execute_container_command(*, workspace: str, command: list[str], image: str,
                              runtime: str = "docker", timeout_seconds: int = 60,
                              cwd: str = ".") -> dict[str, Any]:
    """Execute an argv command inside the configured digest-pinned OCI image."""
    from solspire.project_execution_boundary import run_isolated, safe_relative_path
    root = Path(workspace).resolve(strict=True)
    rel = "." if cwd == "." else safe_relative_path(cwd)
    working = root if rel == "." else (root / rel).resolve(strict=True)
    try:
        working.relative_to(root)
    except ValueError as exc:
        raise BoundaryError("working directory escapes disposable workspace") from exc
    if "@sha256:" not in image or len(image.rsplit("@sha256:", 1)[-1]) != 64:
        raise BoundaryError("container image must be pinned by immutable sha256 digest")
    result = run_isolated(image=image, workspace=root, command=command,
                          timeout_seconds=timeout_seconds, runtime=runtime,
                          working_directory=rel)
    return {"ok": result.returncode == 0, "returncode": result.returncode,
            "stdout": result.stdout[:200000], "stderr": result.stderr[:200000],
            "runtime": runtime, "container_image": image, "network": "disabled"}


def apply_reviewed_project_patch(*, subject_uid: str, project_id: str,
                                 expected_base_digest: str, approved: bool,
                                 changes: list[dict[str, str]],
                                 allowed_paths: list[str],
                                 work_ref: str | None = None) -> dict[str, Any]:
    """Apply an explicitly reviewed patch to existing canonical project files.

    The authenticated caller is recorded as approver. Only existing file names
    can be updated in this operation; additions/deletions need a separate
    governed operation. All checks occur before the first canonical write.
    """
    from solspire.project_store import update_file
    from solspire.workspace_manager import get_workspace_manager
    from solspire.workevent_manager import get_workevent_manager

    current = _canonical_files(project_id)
    observed = canonical_base_digest(project_id)
    workspace = get_workspace_manager().get_for_subject(subject_uid)
    if workspace is None:
        raise BoundaryError("canonical workspace missing; refusing patch without WorkEvent evidence binding")
    paths = [str(change.get("path") or "") for change in changes]
    accepted = require_reviewed_patch(
        approved=approved, expected_base_digest=expected_base_digest,
        observed_base_digest=observed, changed_paths=paths,
        allowed_paths=allowed_paths,
    )
    by_name: dict[str, dict[str, Any]] = {}
    for row in current:
        name = str(row.get("name") or "")
        if name in by_name:
            raise BoundaryError("canonical project has duplicate file names; refusing ambiguous patch")
        by_name[name] = row
    normalized: list[tuple[dict[str, Any], str]] = []
    for change, path in zip(changes, accepted):
        if path not in by_name:
            raise BoundaryError(f"patch path is not an existing canonical file: {path}")
        content = change.get("content")
        if not isinstance(content, str):
            raise BoundaryError(f"patch content must be text: {path}")
        normalized.append((by_name[path], content))

    patch_digest = hashlib.sha256(json.dumps(
        [{"path": path, "content": content} for path, (_, content) in zip(accepted, normalized)],
        ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    # Recheck immediately before mutation to reject stale reviews.
    if canonical_base_digest(project_id) != expected_base_digest:
        raise BoundaryError("canonical base changed during review; refresh approval")

    for row, content in normalized:
        update_file(row["id"], content, name=row["name"])

    event = get_workevent_manager().create(
        subject_ref=subject_uid, workspace_ref=workspace.id,
        event_type="PROJECT_PATCH_APPLIED", occurred_at=__import__("time").time(),
        work_ref=work_ref or project_id, scope_ref=project_id, actor_ref=subject_uid,
        artifact_refs=[f"project-file:{row['id']}" for row, _ in normalized],
        state_before_ref=expected_base_digest,
        state_after_ref=canonical_base_digest(project_id),
        decision_ref=f"human-approval:{subject_uid}:{patch_digest}",
        witness_ref=f"sha256:{patch_digest}", status="RECORDED",
    )
    return {"ok": True, "project_id": project_id, "patch_digest": patch_digest,
            "approved_by": subject_uid, "changed_paths": accepted,
            "work_event": event.to_dict(),
            "canonical_base_digest": canonical_base_digest(project_id)}


__all__ = ["apply_reviewed_project_patch", "canonical_base_digest",
           "create_disposable_workspace", "execute_container_command"]
