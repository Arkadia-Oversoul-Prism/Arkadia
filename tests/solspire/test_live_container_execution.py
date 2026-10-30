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


@pytest.mark.live_container
def test_p04_test_operation_executes_pinned_argv_in_a_real_container(tmp_path):
    """P0.4 — the Lab's bounded test operation against a live OCI runtime.

    Stubs prove the wiring; this proves the part only a real container can:
    our pinned argv actually executes inside the hardened boundary, and the
    exit code that comes back is the container's own. A non-zero exit must
    surface as a failure carrying the container's output — never as a
    fabricated pass — and a claimed pass must be corroborated by the suite's
    own output.
    """
    image = os.environ.get("SOLSPIRE_TEST_AGENT_IMAGE")
    if not image:
        pytest.skip("SOLSPIRE_TEST_AGENT_IMAGE is not configured")
    runtime_name = os.environ.get("SOLSPIRE_CONTAINER_RUNTIME", "docker")
    try:
        assert_container_runtime_ready(image=image, runtime=runtime_name)
    except Exception as exc:  # pragma: no cover - depends on the runner
        pytest.skip(f"container runtime unavailable: {exc}")

    from lab.engineering_lab.bounded_test_execution import (
        DEFAULT_TEST_COMMAND,
        resolve_test_command,
    )
    from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # The container runs as uid 65532, so the bind mount must be writable by
    # that uid — the same shape the live boundary test above uses.
    workspace.chmod(0o777)
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert True\n", encoding="utf-8"
    )

    sandbox = Sandbox(
        SandboxPolicy(
            root=str(workspace),
            containerized=True,
            container_image=image,
            container_runtime=runtime_name,
        )
    )
    result = sandbox.run_test(
        command=resolve_test_command("tests/test_smoke.py"), timeout=120
    )

    assert result["kind"] == "test"
    assert result["boundary"] == "solspire.container"
    assert result["network"] == "disabled"
    assert result["argv"][:3] == list(DEFAULT_TEST_COMMAND[:3])
    assert result["argv"][-1] == "tests/test_smoke.py"
    # `ok` must mirror the container's exit code in both directions.
    assert result["ok"] is (result["returncode"] == 0)
    if result["returncode"] == 0:
        # A claimed pass must be corroborated by the suite's own output.
        assert "passed" in result["stdout"] or "collected" in result["stdout"], (
            f"exit 0 without suite output: {result['stdout'][:200]!r}"
        )
    else:
        assert (result["stderr"] or result["stdout"]), (
            "a failed run must carry the container's own output"
        )


def test_live_runner_refuses_unpinned_image():
    with pytest.raises(BoundaryError, match="SHA-256"):
        assert_container_runtime_ready(image="alpine:3.20")
