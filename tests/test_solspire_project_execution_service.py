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
    result = run_isolated(
        image=image, workspace=tmp_path,
        command=("/bin/sh", "-c", "id -u; test ! -w /etc; touch /workspace/runtime-probe"),
        timeout_seconds=30, runtime=runtime,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[0] == "65532"
    assert (tmp_path / "runtime-probe").is_file()
