"""Phase 5 — Governed execution dry-run and forbidden actions."""
from lab.execution import FORBIDDEN_ACTIONS, execute_governed


PROPOSAL = {
    "proposal_id": "EV-PHASE5-DRY-001",
    "title": "Document parallel execution path debt",
    "approval_required": True,
    "problem": {"description": "fixture", "evidence": ["pattern:parallel-execution-paths"]},
}


def test_forbidden_actions_include_merge_deploy():
    assert "merge" in FORBIDDEN_ACTIONS
    assert "deploy" in FORBIDDEN_ACTIONS


def test_dry_run_emits_events_no_pr():
    r = execute_governed(PROPOSAL, mode="dry_run")
    assert r.ok is True
    names = [e["event"] for e in r.events]
    assert "dry_run.completed" in names
    assert "pr.created" not in names
    d = r.to_dict()
    assert d["merge"] is False
    assert d["deploy"] is False


def test_rejects_auto_execution_flags():
    bad = {**PROPOSAL, "execution": True}
    r = execute_governed(bad, mode="dry_run")
    assert r.ok is False


def test_prepare_pr_requires_callables():
    r = execute_governed(PROPOSAL, mode="prepare_pr")
    assert r.ok is False
    assert r.ok is False and (any("callable" in e.lower() for e in r.errors) or any(e.get("event")=="prepare_pr.blocked" for e in r.events))


def test_prepare_pr_with_injected_callables():
    state = {"branch": None, "applied": False, "pr": None}

    def create_branch(b: str) -> None:
        state["branch"] = b

    def apply(_p: dict) -> None:
        state["applied"] = True

    def tests() -> tuple[bool, str]:
        return True, "ok"

    def open_pr(b: str, pid: str) -> str:
        state["pr"] = f"https://example.invalid/{b}/{pid}"
        return state["pr"]

    r = execute_governed(
        PROPOSAL,
        mode="prepare_pr",
        create_branch_fn=create_branch,
        apply_fn=apply,
        run_tests_fn=tests,
        open_pr_fn=open_pr,
    )
    assert r.ok is True
    assert state["branch"] and state["applied"] and state["pr"]
    assert r.pr_url == state["pr"]
    assert "pr.created" in [e["event"] for e in r.events]
    assert r.to_dict()["merge"] is False


# Comparative Examination I — Arkadia-native disposable execution boundary.
def test_comparative_exam_i_authorization_change_reaches_k15_before_k3(monkeypatch, tmp_path):
    import os
    import subprocess
    from pathlib import Path

    from solspire.project_manager import get_project_manager
    from solspire.project_execution import build_patch_approval, execute_project_patch
    from weaver.execution import pass_spec_hash, patch_content_hash
    from weaver.pass_spec import PassSpec
    from weaver.provider import ProviderOutcome, ProviderResult
    from weaver.patch import _unified_diff

    def git(cwd: str, *args: str) -> str:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def make_fixture(name: str):
        root = tmp_path / name
        root.mkdir()
        git(str(root), "init")
        git(str(root), "config", "user.email", "comparative-exam@arkadia.test")
        git(str(root), "config", "user.name", "Comparative Examination I")
        git(str(root), "checkout", "-b", "main")
        fixture = root / "fixture.txt"
        fixture.write_text("ORIGINAL FIXTURE CONTENT\n", encoding="utf-8")
        git(str(root), "add", "fixture.txt")
        git(str(root), "commit", "-m", "seed comparative examination fixture")
        head = git(str(root), "rev-parse", "HEAD")
        git(str(root), "update-ref", "refs/remotes/origin/main", head)
        return str(root), head

    def make_case(repo_root: str, head: str, patch_id: str, new_body: str):
        before = Path(repo_root, "fixture.txt").read_text(encoding="utf-8")
        patch = {
            "patch_id": patch_id,
            "plan_id": f"plan-{patch_id}",
            "plan_content_hash": f"planhash-{patch_id}",
            "changeset_id": f"cs-{patch_id}",
            "status": "VALID",
            "base_head_sha": head,
            "base_origin_sha": head,
            "files": [{
                "path": "fixture.txt",
                "operation": "MODIFY",
                "symbols_or_regions": [],
                "before": before,
                "after": new_body,
                "patch_text": _unified_diff("fixture.txt", before, new_body, "MODIFY"),
            }],
            "tests": {},
            "impact": {},
            "validation": {},
            "review": {"objective": "Comparative Examination I disposable fixture mutation"},
            "authorization": {},
            "execution": {},
        }
        spec = PassSpec(
            pass_id=f"comparative-{patch_id}",
            objective="Mutate fixture.txt via governed K15→K3",
            base_sha=head,
            allowed_paths=["fixture.txt"],
            forbidden_paths=[],
            required_tests=[],
            required_builds=[],
            non_goals=["touch Arkadia tree", "second mutation path"],
            commit_required=True,
            push_allowed=False,
            publication_required=False,
            human_approval_required=True,
            checkpoint_required=False,
            pass_type="engineering",
        )
        spec.validate_structure()
        ps = spec.to_dict()
        ps["pass_spec_hash"] = pass_spec_hash(spec)
        ps["bound_patch_id"] = patch_id
        ps["bound_patch_hash"] = patch_content_hash(patch)
        approval = build_patch_approval(patch, ps, approved=True)
        return patch, spec, ps, approval

    new_body = "MUTATED BY COMPARATIVE EXAMINATION I\n"

    def fake_invoke(req):
        return ProviderResult(
            outcome=ProviderOutcome.SUCCESS,
            text=f"--- FILE: fixture.txt ---\n{new_body}",
            provider="comparative-exam-fixture",
            attempts=1,
        )

    monkeypatch.setattr("weaver.agent.invoke_provider", fake_invoke)
    monkeypatch.setattr("weaver.provider.invoke_provider", fake_invoke)

    # Control A: valid authorization reaches K3 and produces the declared consequence.
    control_root, control_head = make_fixture("control")
    control_patch, _, control_spec, control_approval = make_case(
        control_root, control_head, "comparative-control", new_body
    )
    control_project = get_project_manager().create(
        "Comparative Examination I Control", {}, owner_uid="comparative-exam"
    )
    prev_cwd = os.getcwd()
    prev_repo_root = os.environ.get("REPO_ROOT")
    try:
        os.chdir(control_root)
        os.environ["REPO_ROOT"] = control_root
        control_out = execute_project_patch(
            control_project.to_dict(),
            control_patch,
            control_spec,
            control_approval,
            repo_root=control_root,
            run_k3=True,
        )
    finally:
        os.chdir(prev_cwd)
        if prev_repo_root is None:
            os.environ.pop("REPO_ROOT", None)
        else:
            os.environ["REPO_ROOT"] = prev_repo_root

    assert Path(control_root, "fixture.txt").read_text(encoding="utf-8") == new_body
    assert control_out["k15_ready"] is True
    assert (control_out["execution"] or {}).get("k3") not in ("NOT_INVOKED", None)

    # Examination B: change PassSpec after approval but before K3.
    exam_root, exam_head = make_fixture("examination")
    exam_patch, _, exam_spec, exam_approval = make_case(
        exam_root, exam_head, "comparative-examination", new_body
    )
    changed_spec = dict(exam_spec)
    changed_spec["objective"] = "AUTHORITY CHANGE BEFORE K3"
    changed_spec["pass_spec_hash"] = pass_spec_hash(PassSpec.from_dict(changed_spec))

    exam_project = get_project_manager().create(
        "Comparative Examination I Authority Change", {}, owner_uid="comparative-exam"
    )

    prev_cwd = os.getcwd()
    prev_repo_root = os.environ.get("REPO_ROOT")
    try:
        os.chdir(exam_root)
        os.environ["REPO_ROOT"] = exam_root
        exam_out = execute_project_patch(
            exam_project.to_dict(),
            exam_patch,
            changed_spec,
            exam_approval,
            repo_root=exam_root,
            run_k3=True,
        )
    finally:
        os.chdir(prev_cwd)
        if prev_repo_root is None:
            os.environ.pop("REPO_ROOT", None)
        else:
            os.environ["REPO_ROOT"] = prev_repo_root

    # Independent consequence observation: K3 must not be invoked and the fixture remains original.
    assert Path(exam_root, "fixture.txt").read_text(encoding="utf-8") == "ORIGINAL FIXTURE CONTENT\n"
    assert exam_out["k15_ready"] is False
    assert (exam_out["execution"] or {}).get("status") == "NOT_RUN"
    assert (exam_out["execution"] or {}).get("final_status") == "BLOCKED"
    assert (exam_out["execution"] or {}).get("k3") is None
    assert "PassSpec hash no longer matches approval" in str(
        (exam_out["execution"] or {}).get("message")
    )
    assert (exam_out.get("authorization") or {}).get("PatchApproval") == "INVALIDATED"
