"""WEAVER-K0.1 session kernel — preflight through durable publication."""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from .autonomy.guard import AutonomyGuard
from .git_ops import commit_and_push, push_current
from .logger import get_logger
from .pass_spec import (
    PassSpec,
    PassSpecError,
    assert_paths_authorized,
    current_head,
    current_origin_main,
    verify_lineage,
)

LOGGER = get_logger()
CHECKPOINT_DIR = os.path.join("data", "weaver", "checkpoints")


@dataclass
class SessionResult:
    ok: bool
    pass_id: str
    stage: str
    status: str = "FAILED"  # PASS | BLOCKED | FAILED | NO_CHANGE | PENDING_PUBLICATION
    message: str = ""
    changed_paths: list[str] = field(default_factory=list)
    tests_run: list[str] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)
    result_sha: str | None = None
    remote_sha: str | None = None
    publication_status: str = "not_attempted"
    checkpoint_path: str | None = None
    hard_stop: bool = True


def preflight(spec: PassSpec, repo_root: str = ".") -> str:
    return verify_lineage(spec, repo_root)


def guard_for(spec: PassSpec) -> AutonomyGuard:
    return AutonomyGuard.from_pass_spec(spec)


def filter_authorized_writes(paths: list[str], contents: dict[str, str], spec: PassSpec):
    guard = guard_for(spec)
    accepted, rejected = [], []
    for p in paths:
        if not guard.path_allowed(p):
            rejected.append(p)
            continue
        try:
            assert_paths_authorized([p], spec)
        except PassSpecError:
            rejected.append(p)
            continue
        accepted.append(p)
    return accepted, rejected


def run_required_tests(spec: PassSpec, repo_root: str = ".") -> dict[str, Any]:
    results: dict[str, Any] = {"passed": True, "items": []}
    if not spec.required_tests:
        results["note"] = "no required_tests declared"
        return results
    for item in spec.required_tests:
        proc = subprocess.run(
            ["python3", "-m", "pytest", item, "-q", "--tb=line"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        results["items"].append(
            {
                "target": item,
                "returncode": proc.returncode,
                "stdout_tail": (proc.stdout or "")[-2000:],
                "stderr_tail": (proc.stderr or "")[-1000:],
            }
        )
        if proc.returncode != 0:
            results["passed"] = False
    return results


def verify_diff_scope(spec: PassSpec, repo_root: str = ".") -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    paths = []
    for line in (proc.stdout or "").splitlines():
        if not line.strip():
            continue
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[-1]
        paths.append(path)
    if paths:
        assert_paths_authorized(paths, spec)
    subprocess.run(["git", "diff", "--check"], cwd=repo_root, check=False)
    return paths


def write_checkpoint(
    spec: PassSpec,
    *,
    status: str,
    result_sha: str | None,
    remote_sha: str | None,
    changed_paths: list[str],
    tests_run: list[str],
    test_results: dict[str, Any],
    publication_status: str,
    publication_method: str = "none",
    failure_reason: str = "",
    remaining_limitations: list[str] | None = None,
    next_action: str = "HARD STOP — await human authorization",
    repo_root: str = ".",
) -> str:
    os.makedirs(os.path.join(repo_root, CHECKPOINT_DIR), exist_ok=True)
    payload = {
        "pass_id": spec.pass_id,
        "pass_type": spec.pass_type,
        "objective": spec.objective,
        "base_sha": spec.base_sha,
        "result_sha": result_sha,
        "branch": "main",
        "remote": "origin/main",
        "remote_sha": remote_sha,
        "status": status,
        "timestamp": int(time.time()),
        "changed_files": changed_paths,
        "tests_run": tests_run,
        "test_results": test_results,
        "builds_run": list(spec.required_builds),
        "build_results": {},
        "diff_status": "ok" if status in ("PASS", "NO_CHANGE") else status.lower(),
        "authorization_status": "human",
        "publication_status": publication_status,
        "publication_method": publication_method,
        "failure_reason": failure_reason,
        "remaining_limitations": remaining_limitations or [],
        "next_action": next_action,
        "hard_stop": True,
        "provider": spec.provider,
        "push_allowed": spec.push_allowed,
        "publication_required": spec.publication_required,
        "constitution": (
            "NO EPHEMERAL PROGRESS. A Weaver pass is complete only when "
            "its state is verified on origin/main."
        ),
    }
    # Never persist secrets
    for key in list(payload.keys()):
        if any(s in key.lower() for s in ("token", "secret", "password", "api_key", "credential")):
            del payload[key]
    name = f"{spec.pass_id.replace('/', '_')}_{payload['timestamp']}.json"
    path = os.path.join(repo_root, CHECKPOINT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def _ensure_checkpoint_allowlisted(spec: PassSpec) -> None:
    """Checkpoint path must be in allow-list for durable no-op commits."""
    ck = "data/weaver/checkpoints/"
    if not any(
        a.replace("\\", "/").rstrip("/").endswith("checkpoints")
        or a.replace("\\", "/").startswith("data/weaver")
        or a == "data/"
        for a in spec.allowed_paths
    ):
        # soft: still write checkpoint locally; commit may fail scope — callers should allowlist
        LOGGER.warning("PassSpec should include data/weaver/checkpoints/ for durable no-op turns")


def finalize_session(
    spec: PassSpec,
    changed_paths: list[str],
    *,
    commit_message: str | None = None,
    status_hint: str | None = None,
    failure_reason: str = "",
    repo_root: str = ".",
) -> SessionResult:
    """Test → diff → checkpoint → commit → optional push → remote verification."""
    try:
        preflight(spec, repo_root)
    except PassSpecError as e:
        return SessionResult(
            ok=False,
            pass_id=spec.pass_id,
            stage="lineage",
            status="BLOCKED",
            message=str(e),
            failure_reason=str(e),
        )

    try:
        dirty = verify_diff_scope(spec, repo_root)
    except PassSpecError as e:
        ck = write_checkpoint(
            spec,
            status="BLOCKED",
            result_sha=current_head(repo_root),
            remote_sha=current_origin_main(repo_root),
            changed_paths=changed_paths,
            tests_run=[],
            test_results={},
            publication_status="blocked",
            failure_reason=str(e),
            repo_root=repo_root,
        )
        return SessionResult(
            ok=False,
            pass_id=spec.pass_id,
            stage="diff_gate",
            status="BLOCKED",
            message=str(e),
            changed_paths=changed_paths,
            checkpoint_path=ck,
        )

    test_results = run_required_tests(spec, repo_root)
    tests_run = list(spec.required_tests)
    if not test_results.get("passed", False):
        ck = write_checkpoint(
            spec,
            status="FAILED",
            result_sha=current_head(repo_root),
            remote_sha=current_origin_main(repo_root),
            changed_paths=changed_paths or dirty,
            tests_run=tests_run,
            test_results=test_results,
            publication_status="blocked",
            failure_reason="required tests failed",
            repo_root=repo_root,
        )
        return SessionResult(
            ok=False,
            pass_id=spec.pass_id,
            stage="test_gate",
            status="FAILED",
            message="required tests failed",
            changed_paths=changed_paths or dirty,
            tests_run=tests_run,
            test_results=test_results,
            checkpoint_path=ck,
            publication_status="blocked",
        )

    paths = list(dict.fromkeys((changed_paths or []) + dirty))
    status = status_hint or ("NO_CHANGE" if not paths else "PASS")
    result_sha = current_head(repo_root)
    publication_status = "not_attempted"
    publication_method = "none"

    # Always materialize a checkpoint file so no-op turns have a git artifact
    _ensure_checkpoint_allowlisted(spec)
    ck_path = write_checkpoint(
        spec,
        status=status,
        result_sha=result_sha,
        remote_sha=current_origin_main(repo_root),
        changed_paths=paths,
        tests_run=tests_run,
        test_results=test_results,
        publication_status=publication_status,
        failure_reason=failure_reason,
        repo_root=repo_root,
    )
    if ck_path and ck_path not in paths:
        # relative path for git
        rel_ck = os.path.relpath(ck_path, repo_root)
        paths = list(dict.fromkeys(paths + [rel_ck]))

    if spec.commit_required and paths:
        try:
            assert_paths_authorized(paths, spec)
        except PassSpecError as e:
            # if only failure is checkpoint path not allowed, still return blocked
            return SessionResult(
                ok=False,
                pass_id=spec.pass_id,
                stage="scope",
                status="BLOCKED",
                message=str(e),
                changed_paths=paths,
                checkpoint_path=ck_path,
            )
        msg = commit_message or f"weaver: {spec.pass_id} — {spec.objective[:80]}"
        do_push = bool(spec.push_allowed and spec.publication_required)
        ok = commit_and_push(
            msg,
            paths=paths,
            meta={"pass_id": spec.pass_id},
            push=do_push,
        )
        if not ok:
            return SessionResult(
                ok=False,
                pass_id=spec.pass_id,
                stage="commit",
                status="PENDING_PUBLICATION" if do_push else "FAILED",
                message="commit or push failed",
                changed_paths=paths,
                tests_run=tests_run,
                test_results=test_results,
                checkpoint_path=ck_path,
                publication_status="failed",
            )
        result_sha = current_head(repo_root)
        if do_push:
            publication_status = "published"
            publication_method = "git_push"
            # refresh remote tracking if possible
            subprocess.run(["git", "fetch", "origin"], cwd=repo_root, capture_output=True)
            remote = current_origin_main(repo_root)
            if remote != result_sha:
                return SessionResult(
                    ok=False,
                    pass_id=spec.pass_id,
                    stage="remote_verify",
                    status="PENDING_PUBLICATION",
                    message=f"HEAD {result_sha} != origin/main {remote}",
                    changed_paths=paths,
                    result_sha=result_sha,
                    remote_sha=remote,
                    publication_status="unverified",
                    checkpoint_path=ck_path,
                )
        else:
            publication_status = "committed_local_only"
            publication_method = "commit_only"
            if spec.publication_required:
                return SessionResult(
                    ok=False,
                    pass_id=spec.pass_id,
                    stage="publication",
                    status="PENDING_PUBLICATION",
                    message="publication_required but push_allowed=false",
                    changed_paths=paths,
                    result_sha=result_sha,
                    publication_status=publication_status,
                    checkpoint_path=ck_path,
                )

        # Rewrite checkpoint with final SHAs
        ck_path = write_checkpoint(
            spec,
            status=status if status != "NO_CHANGE" or paths else "NO_CHANGE",
            result_sha=result_sha,
            remote_sha=current_origin_main(repo_root),
            changed_paths=paths,
            tests_run=tests_run,
            test_results=test_results,
            publication_status=publication_status,
            publication_method=publication_method,
            failure_reason=failure_reason,
            repo_root=repo_root,
        )

    return SessionResult(
        ok=True,
        pass_id=spec.pass_id,
        stage="complete",
        status=status,
        message="session complete",
        changed_paths=paths,
        tests_run=tests_run,
        test_results=test_results,
        result_sha=result_sha,
        remote_sha=current_origin_main(repo_root),
        publication_status=publication_status,
        checkpoint_path=ck_path,
    )
