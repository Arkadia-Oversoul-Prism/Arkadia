"""WEAVER-W1 — workbench observability / governance proofs."""
from __future__ import annotations

import subprocess

from weaver.workbench_view import (
    LIFECYCLE,
    observatory,
    render_verification_matrix,
    repository_state,
    run_read_only_pipeline,
)
import weaver.workbench_view as wview
import weaver.workbench_app as wapp


def test_repository_state_fields(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    st = repository_state(str(tmp_path))
    assert st["head_sha"]
    assert st["clean"] is True


def test_observatory_authority_locked():
    o = observatory(".")
    assert o.authority["Mutation path"] == "K3 ONLY"
    assert o.authority["PassSpec"] == "NONE"
    assert o.authority["Execution"] == "LOCKED"
    assert len(o.lifecycle) == len(LIFECYCLE)


def test_pipeline_read_only_no_auth():
    r = run_read_only_pipeline("Explain the current Weaver architecture.")
    assert r["executed"] is False
    assert r["authorization"]["Execution"] == "LOCKED"
    assert r["authorization"]["PassSpec"] == "NONE"
    assert r["patch"]["EXECUTED"] is False
    assert r["governance"]["APPROVAL"] is False
    assert "analysis" in r and "plan" in r and "changeset" in r and "patch" in r


def test_verification_matrix_unknown():
    rows = render_verification_matrix(None)
    assert rows[0]["status"] == "UNKNOWN"
    rows2 = render_verification_matrix(
        {"proof_matrix": [{"claim": "x", "evidence": "y", "status": "FAILED"}]}
    )
    assert rows2[0]["status"] == "FAILED"


def test_no_mutation_apis():
    for name in ("write_file", "commit_and_push", "apply_patch", "run_transaction", "execute_patch"):
        assert not hasattr(wview, name)
        assert not hasattr(wapp, name)
