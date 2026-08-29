"""Weaver agent — K0.1: PassSpec required; scoped writes; terminal publication policy."""
from __future__ import annotations

import re

from .fs import read_repo, write_file
from .llm import call_llm
from .provider import invoke_provider, ProviderRequest, ProviderOutcome
from .logger import get_logger
from .pass_spec import PassSpec, PassSpecError, assert_paths_authorized
from .prompts import build_prompt
from .session_kernel import (
    SessionResult,
    filter_authorized_writes,
    finalize_session,
    guard_for,
    preflight,
)

LOGGER = get_logger()


def run(task: str, engine_cycle: int | None = None, pass_spec: PassSpec | None = None):
    if pass_spec is None:
        LOGGER.error(
            "weaver.agent.run refused: PassSpec required (WEAVER-K0.1). "
            "Use run_authorized(task, pass_spec=...)."
        )
        return [], None
    result = run_authorized(task, pass_spec, engine_cycle=engine_cycle)
    if not result.ok:
        return result.changed_paths, None
    return result.changed_paths, result.message


def run_authorized(
    task: str,
    pass_spec: PassSpec,
    *,
    engine_cycle: int | None = None,
    provider: str | None = None,
    repo_root: str = ".",
) -> SessionResult:
    try:
        preflight(pass_spec, repo_root)
    except PassSpecError as e:
        return SessionResult(
            ok=False,
            pass_id=pass_spec.pass_id,
            stage="lineage",
            status="BLOCKED",
            message=str(e),
        )

    guard = guard_for(pass_spec)
    if not guard.allowed():
        return SessionResult(
            ok=False,
            pass_id=pass_spec.pass_id,
            stage="guard",
            status="BLOCKED",
            message="AutonomyGuard denied execution",
        )

    files = read_repo(repo_root)
    scoped = {
        k: v
        for k, v in files.items()
        if guard.path_allowed(k.replace("\\", "/").lstrip("./"))
    }
    prompt = build_prompt(task, scoped or files)
    model = provider or pass_spec.provider or "gemini"
    try:
        # Prefer structured provider result (K2); never treat failure as success
        pres = invoke_provider(ProviderRequest(provider=model, prompt=prompt))
        if not pres.ok:
            LOGGER.warning("Provider failed for task '%s': %s %s", task, pres.outcome, pres.error)
            return SessionResult(
                ok=False,
                pass_id=pass_spec.pass_id,
                stage="llm",
                status="FAILED",
                message=f"{pres.outcome.value}: {pres.error}",
            )
        response = pres.text
    except Exception as e:
        LOGGER.warning("LLM call failed for task '%s': %s", task, e)
        return SessionResult(
            ok=False,
            pass_id=pass_spec.pass_id,
            stage="llm",
            status="FAILED",
            message=str(e),
        )

    pattern = r"--- FILE: (.*?) ---\n(.*?)(?=--- FILE:|\Z)"
    matches = re.findall(pattern, response, re.S)
    if not matches:
        # Durable no-op: still finalize (checkpoint + optional publish policy)
        return finalize_session(
            pass_spec,
            [],
            commit_message=f"weaver: {pass_spec.pass_id} — NO_CHANGE",
            status_hint="NO_CHANGE",
            repo_root=repo_root,
        )

    proposed, content_map = [], {}
    for path, content in matches:
        p = path.strip()
        proposed.append(p)
        content_map[p] = content.strip()

    accepted, rejected = filter_authorized_writes(proposed, content_map, pass_spec)
    if rejected:
        LOGGER.warning("Rejected unauthorized paths: %s", rejected)
    if not accepted:
        return SessionResult(
            ok=False,
            pass_id=pass_spec.pass_id,
            stage="scope",
            status="BLOCKED",
            message=f"no authorized paths; rejected={rejected}",
        )

    updated_files = []
    for p in accepted:
        try:
            assert_paths_authorized([p], pass_spec)
        except PassSpecError as e:
            LOGGER.warning("%s", e)
            continue
        if write_file(p, content_map[p]):
            updated_files.append(p)

    commit_msg = f"weaver: {pass_spec.pass_id} — {task[:120]}"
    if engine_cycle is not None:
        commit_msg += f" (cycle {engine_cycle})"

    return finalize_session(
        pass_spec,
        updated_files,
        commit_message=commit_msg,
        status_hint="PASS" if updated_files else "NO_CHANGE",
        repo_root=repo_root,
    )
