"""WEAVER-MVP2-02 — concrete-target surgical patch synthesis."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = str(Path(__file__).resolve().parents[1])


@pytest.fixture
def repo_root():
    return REPO_ROOT


def test_mvp202_concrete_docstring_is_surgical(repo_root):
    from weaver.workbench_view import run_read_only_pipeline

    objective = (
        'Update the module docstring in weaver/pass_spec.py '
        'to say "Surgical MVP2-02 concrete target."'
    )
    result = run_read_only_pipeline(
        objective,
        repo_root=repo_root,
        affected_paths=["weaver/pass_spec.py"],
    )
    patch = result.get("patch") or {}
    files = patch.get("files") or []
    assert len(files) >= 1
    target = next((f for f in files if f.get("path") == "weaver/pass_spec.py"), files[0])
    pt = target.get("patch_text") or ""
    assert "@@ redesign region @@" not in pt
    stats = target.get("line_stats") or {}
    # Surgical: small change, not whole-file
    assert stats.get("changed", 999) < 30
    fidelity = target.get("fidelity") or (result.get("patch") or {}).get("review", {}).get("fidelity")
    # Prefer file-level, fallback review
    if not fidelity:
        fidelity = (patch.get("review") or {}).get("fidelity") or (patch.get("review") or {}).get(
            "implementation_quality"
        )
    assert fidelity in ("HIGH", "MINIMAL") or stats.get("changed", 999) < 20
    assert result.get("executed") is False
    auth = result.get("authorization") or {}
    assert auth.get("Execution") in (None, "LOCKED", "NONE") or auth.get("Execution") == "LOCKED"


def test_mvp202_unrelated_body_preserved(repo_root):
    from weaver.patch import _surgical_modify

    before = Path(repo_root, "weaver/pass_spec.py").read_text(encoding="utf-8")
    after, strategy, fidelity = _surgical_modify(
        before,
        objective='Update the module docstring in weaver/pass_spec.py to say "X."',
        symbols=[],
        impl="",
    )
    assert strategy.startswith("MODULE_DOCSTRING")
    assert fidelity == "HIGH"
    # Body after first docstring should match for a long common suffix
    # Strip module docstring from both and compare
    import re

    def strip_mod_doc(s: str) -> str:
        m = re.match(r'(?s)^\s*[ruRU]{0,2}("""|\'\'\').*?\1\s*', s)
        return s[m.end() :] if m else s

    assert strip_mod_doc(before) == strip_mod_doc(after)


def test_mvp202_no_redesign_region(repo_root):
    from weaver.workbench_view import run_read_only_pipeline

    result = run_read_only_pipeline(
        'Clarify the module docstring in weaver/pass_spec.py to say "Y."',
        repo_root=repo_root,
        affected_paths=["weaver/pass_spec.py"],
    )
    for f in (result.get("patch") or {}).get("files") or []:
        assert "@@ redesign region @@" not in (f.get("patch_text") or "")


def test_mvp202_ambiguous_not_false_precision(repo_root):
    from weaver.workbench_view import run_read_only_pipeline

    result = run_read_only_pipeline(
        "Improve the architecture.",
        repo_root=repo_root,
    )
    patch = result.get("patch") or {}
    files = patch.get("files") or []
    # Must not claim HIGH surgical fidelity for vague objective
    review = patch.get("review") or {}
    fidelity = review.get("fidelity") or review.get("implementation_quality") or "LIMITED"
    if files:
        for f in files:
            if f.get("operation") == "MODIFY":
                assert f.get("fidelity", "LIMITED") != "HIGH" or f.get("synthesis_strategy") == "ANNOTATIVE_MARKER"
    assert fidelity != "HIGH" or not files
    assert result.get("executed") is False


def test_mvp202_does_not_authorize(repo_root):
    from weaver.workbench_view import run_read_only_pipeline

    result = run_read_only_pipeline(
        'Update the module docstring in weaver/pass_spec.py to say "Z."',
        repo_root=repo_root,
        affected_paths=["weaver/pass_spec.py"],
    )
    assert result.get("executed") is False
    assert (result.get("authorization") or {}).get("Execution") == "LOCKED"


def test_mvp202_k15_boundary_intact():
    import inspect
    import solspire.project_execution as pe

    src = inspect.getsource(pe)
    assert "execute_patch" in src
    assert "run_transaction" not in src


def test_mvp202_pass_spec_still_required(repo_root):
    from solspire.project_manager import get_project_manager
    from solspire.project_execution import evaluate_execution_state
    from weaver.workbench_view import run_read_only_pipeline
    from weaver.pass_spec import current_head, current_origin_main

    r = run_read_only_pipeline(
        'Update the module docstring in weaver/pass_spec.py to say "Auth still required."',
        repo_root=repo_root,
        affected_paths=["weaver/pass_spec.py"],
    )
    patch = dict(r.get("patch") or {})
    patch.setdefault("base_head_sha", current_head(repo_root))
    patch.setdefault("base_origin_sha", current_origin_main(repo_root))
    st = evaluate_execution_state(patch=patch, repo_root=repo_root)
    assert st["k15_ready"] is False
    assert st["state"] == "PASSSPEC_REQUIRED"
