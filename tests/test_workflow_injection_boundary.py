"""Regression boundary for untrusted-event interpolation in CI workflows.

Any commenter can supply an issue/PR comment body. GitHub substitutes `${{ }}`
expressions *before* the shell parses a `run:` script, so interpolating such a
body directly into a `run:` block lets the commenter inject commands. Combined
with a job-level `contents: write` token, that is remote code execution with
repository write authority.

These tests pin two properties:

1. No workflow interpolates untrusted event text into a `run:` block.
2. The workflow that consumes a `/weaver` comment holds a read-only token, does
   not push to `main`, and invokes an entrypoint that exists in the repository.

The detector is proven against the vulnerable form it is meant to catch
(negative control), so a rewrite of the workflow cannot silently disarm it.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
GENESIS = WORKFLOWS / "gemini-agent-genesis.yml"

# Event paths whose content is attacker-controlled on a public repository.
UNTRUSTED_EVENT_FIELDS = (
    "github.event.comment.body",
    "github.event.issue.body",
    "github.event.issue.title",
    "github.event.pull_request.body",
    "github.event.pull_request.title",
    "github.event.review.body",
    "github.event.discussion.body",
)

_INTERPOLATION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)


def _run_scripts(workflow: dict) -> list[str]:
    """Every `run:` script in the workflow, at any job/step depth."""
    scripts: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str):
                scripts.append(run)
    return scripts


def untrusted_interpolations(workflow: dict) -> list[str]:
    """Untrusted event fields interpolated into a `run:` block.

    Interpolating the same expression into `env:` is safe -- the shell receives
    it as a value, not as script text -- so only `run:` bodies are scanned.
    """
    found: list[str] = []
    for script in _run_scripts(workflow):
        for expression in _INTERPOLATION.findall(script):
            for field in UNTRUSTED_EVENT_FIELDS:
                if field in expression:
                    found.append(expression.strip())
    return found


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _workflow_files() -> list[Path]:
    return sorted(p for p in WORKFLOWS.glob("*.yml") if p.name != "_diagnose_blank_frontend.yml")


def test_detector_flags_the_vulnerable_form():
    """Negative control: the harness must catch the defect it claims to catch."""
    vulnerable = {
        "jobs": {
            "weaver_evolution": {
                "steps": [
                    {
                        "name": "Execute Weaver Recursive Engine",
                        "run": 'TASK_INPUT="${{ github.event.comment.body || '
                        'github.event.inputs.task }}"\n',
                    }
                ]
            }
        }
    }
    assert untrusted_interpolations(vulnerable) == [
        "github.event.comment.body || github.event.inputs.task"
    ]


def test_detector_accepts_the_env_passthrough_form():
    """The repaired form passes the same text through `env:` instead."""
    safe = {
        "jobs": {
            "weaver_evolution": {
                "steps": [
                    {
                        "env": {"WEAVER_TASK_INPUT": "${{ github.event.comment.body }}"},
                        "run": 'CLEAN_TASK="$(printf \'%s\' "$WEAVER_TASK_INPUT")"\n',
                    }
                ]
            }
        }
    }
    assert untrusted_interpolations(safe) == []


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_no_workflow_interpolates_untrusted_event_text_into_run(path: Path):
    offenders = untrusted_interpolations(_load(path))
    assert offenders == [], (
        f"{path.name} interpolates untrusted event text directly into a run: block "
        f"({offenders}); pass it through `env:` and quote it instead"
    )


def test_genesis_workflow_holds_a_read_only_token():
    workflow = _load(GENESIS)
    job = workflow["jobs"]["weaver_evolution"]
    assert job.get("permissions", {}).get("contents") == "read", (
        "a job driven by untrusted comment text must not hold a write token"
    )


def test_genesis_workflow_does_not_push_to_main():
    workflow = _load(GENESIS)
    for script in _run_scripts(workflow):
        assert "git push" not in script, (
            "this workflow must not push; mutation goes through a branch and a PR"
        )


def test_genesis_workflow_invokes_an_entrypoint_that_exists():
    workflow = _load(GENESIS)
    scripts = "\n".join(_run_scripts(workflow))
    assert "weaver.workbench" in scripts, "the governed workbench is the canonical entrypoint"
    spec = importlib.util.find_spec("weaver.workbench")
    assert spec is not None, "the entrypoint the workflow invokes must be importable"
