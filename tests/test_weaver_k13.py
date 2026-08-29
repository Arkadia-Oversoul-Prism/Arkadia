"""WEAVER-K13 — implementation synthesis (design-only) proofs."""
from __future__ import annotations

import subprocess
from pathlib import Path

from weaver.engineering_plan import EngineeringPlan
from weaver.implementation import (
    ChangesetStatus,
    FileOp,
    synthesize_changeset,
    review_changeset,
)
from weaver.pass_spec import PassSpec
from weaver.verification import plan_content_hash
import weaver.implementation as imod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "mod.py").write_text("def alpha():\n    return 1\n\nclass Beta:\n    pass\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _plan(paths):
    return EngineeringPlan(
        plan_id="ep1",
        objective="synth",
        affected_paths=list(paths),
        implementation_steps=["step-one", "step-two"],
        proposed_changes=["change-one"],
        test_strategy={"required_tests": ["tests/test_mod.py"], "paths_without_discoverable_tests": []},
        verification_strategy=["pytest"],
        risk_register=[{"description": "risk-a"}],
        unknowns=[{"statement": "unk-a"}],
        evidence_refs=[{"kind": "FACT", "statement": "file exists"}],
    )


def test_symbols_and_modify(tmp_path):
    head = _repo(tmp_path)
    cs = synthesize_changeset(
        _plan(["weaver/mod.py"]),
        pass_spec=PassSpec(
            pass_id="K13",
            objective="s",
            base_sha=head,
            allowed_paths=["weaver/"],
            forbidden_paths=["api/"],
        ),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert cs.status == ChangesetStatus.PROPOSED.value
    assert cs.files
    assert cs.files[0]["operation"] == FileOp.MODIFY.value
    assert "alpha" in cs.files[0]["symbols_or_regions"]
    assert "Beta" in cs.files[0]["symbols_or_regions"]
    assert "MODIFY" in cs.files[0]["implementation"]
    assert cs.authorization["current_pass_authorized"] is True
    # no repo mutation
    assert (tmp_path / "weaver" / "mod.py").read_text().startswith("def alpha")


def test_add_for_missing_file(tmp_path):
    head = _repo(tmp_path)
    cs = synthesize_changeset(
        _plan(["weaver/new_mod.py"]),
        pass_spec=PassSpec(pass_id="K13", objective="s", base_sha=head, allowed_paths=["weaver/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert cs.files[0]["operation"] == FileOp.ADD.value
    assert not (tmp_path / "weaver" / "new_mod.py").exists()


def test_out_of_scope(tmp_path):
    head = _repo(tmp_path)
    cs = synthesize_changeset(
        _plan(["api/main.py"]),
        pass_spec=PassSpec(
            pass_id="K13",
            objective="s",
            base_sha=head,
            allowed_paths=["weaver/"],
            forbidden_paths=["api/"],
        ),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert cs.status == ChangesetStatus.OUT_OF_SCOPE.value


def test_stale(tmp_path):
    head = _repo(tmp_path)
    cs = synthesize_changeset(
        _plan(["weaver/mod.py"]),
        bound_head_sha="0" * 40,
        repo_root=str(tmp_path),
    )
    assert cs.status == ChangesetStatus.STALE.value


def test_plan_binding(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/mod.py"])
    cs = synthesize_changeset(p, expected_plan_hash="bad", bound_head_sha=head, repo_root=str(tmp_path))
    assert cs.status == ChangesetStatus.PLAN_BINDING_MISMATCH.value


def test_deterministic_id(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/mod.py"])
    a = synthesize_changeset(p, bound_head_sha=head, repo_root=str(tmp_path))
    b = synthesize_changeset(p, bound_head_sha=head, repo_root=str(tmp_path))
    assert a.changeset_id == b.changeset_id
    assert a.plan_content_hash == plan_content_hash(p)


def test_no_mutation_apis():
    for name in ("write_file", "commit_and_push", "run_transaction", "execute", "apply_patch"):
        assert not hasattr(imod, name)


def test_review_bundle(tmp_path):
    head = _repo(tmp_path)
    cs = synthesize_changeset(_plan(["weaver/mod.py"]), bound_head_sha=head, repo_root=str(tmp_path))
    b = review_changeset(cs)
    for k in ("objective", "changes", "affected_files", "symbols", "tests", "authorization", "scope"):
        assert k in b
    assert b["authorization"]["note"]
