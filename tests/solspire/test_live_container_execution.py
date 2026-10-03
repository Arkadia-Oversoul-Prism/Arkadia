from __future__ import annotations

import os
from pathlib import Path

import pytest

from solspire.project_execution_boundary import BoundaryError, run_isolated
from solspire.project_execution_service import assert_container_runtime_ready


@pytest.mark.live_container
def test_live_oci_runtime_executes_only_inside_hardened_workspace(tmp_path):
    image = os.environ.get("SOLSPIRE_TEST_AGENT_IMAGE")
    if not image:
        pytest.skip("SOLSPIRE_TEST_AGENT_IMAGE is not configured")
    assert_container_runtime_ready(image=image, runtime=os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker"))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    workspace.chmod(0o777)
    (workspace / "canonical.txt").write_text("unchanged", encoding="utf-8")

    result = run_isolated(
        image=image,
        workspace=workspace,
        command=(
            "/bin/sh", "-c",
            "test \"$(id -u)\" = 65532 && test ! -w / && "
            "printf isolated > /workspace/proof.txt && "
            "test \"$(cat /workspace/proof.txt)\" = isolated"
        ),
        timeout_seconds=30,
    )
    assert result.returncode == 0, result.stderr
    assert (workspace / "proof.txt").read_text(encoding="utf-8") == "isolated"
    assert (workspace / "canonical.txt").read_text(encoding="utf-8") == "unchanged"


def test_live_runner_refuses_unpinned_image():
    with pytest.raises(BoundaryError, match="SHA-256"):
        assert_container_runtime_ready(image="alpine:3.20")
