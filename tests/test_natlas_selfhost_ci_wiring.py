"""Boundary guard: the N-ATLAS self-host contract and its image must be executed in CI.

`tests/test_natlas_selfhost_contract.py` pins the `deploy/n-atlas-server` contract, and
`deploy/n-atlas-server/Dockerfile` is the deployment unit itself. As shipped on `main`,
**no workflow ran either one**:

- `grep -rn "test_natlas_selfhost_contract" .github/` -> 0 matches;
- `grep -rn "n-atlas-server" .github/` -> 0 matches.

That is how an image which **could never start** stayed on `main`: the base image's
exec-form `ENTRYPOINT ["/app/llama-server"]` received the Dockerfile's shell-form `CMD`
as extra argv, so llama-server got `/bin/sh` as a positional argument and exited with
`error: invalid argument: /bin/sh`. A clean `docker build` reports nothing about that —
only running the image does. A guard no workflow executes is decoration.

The invariant is stated generically over every workflow that runs the contract:

1. Some workflow must run the contract on ``pull_request``.
2. Its ``paths`` filter must select the contract file **and every tracked file under the
   deployment unit**, because the unit is the guard's domain. A filter naming a subset is
   incomplete by construction: the next Dockerfile edit lands at a path no entry selects,
   and the smoke test never runs on the pull request that introduces the regression.
3. The guard step must be able to fail the job (``continue-on-error`` off).
4. Some job must actually **build and run** the image. Pinning the Dockerfile's text is not
   the same as proving it starts.

The covered domain is derived from ``git ls-files`` at test time, never restated, so a new
tracked file under the deployment unit is judged by the same rule without editing this file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_CONTRACT_FILE = "tests/test_natlas_selfhost_contract.py"
_WIRING_FILE = "tests/test_natlas_selfhost_ci_wiring.py"
_DEPLOY_DIR = "deploy/n-atlas-server"


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _trigger_block(workflow: dict) -> dict:
    """The ``on:`` mapping (PyYAML parses the bare key ``on`` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub ``paths`` glob to a whole-string regex.

    ``**/`` matches zero or more leading path segments, a remaining ``**`` matches
    anything including ``/``, and ``*``/``?`` match within a single path segment.
    Placeholders keep the single-``*`` rewrite from clobbering the ``**`` expansion.
    """
    placeholders = {"\x00": "**/", "\x01": "**", "\x02": "*", "\x03": "?"}
    tokens = {"\x00": "(?:.*/)?", "\x01": ".*", "\x02": "[^/]*", "\x03": "[^/]"}
    body = pattern
    for ph, token in placeholders.items():
        body = body.replace(token, ph)
    body = body.replace(".", r"\.")
    for ph, rx in tokens.items():
        body = body.replace(ph, rx)
    return re.compile("^" + body + "$")


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a ``paths`` filter selects a literal path, mirroring GitHub's globs."""
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _steps(workflow: dict) -> list[dict]:
    return [step for job in (workflow.get("jobs") or {}).values() for step in (job.get("steps") or [])]


def _guard_steps(workflow: dict) -> list[dict]:
    """Steps whose ``run:`` command names the self-host contract file."""
    return [s for s in _steps(workflow) if isinstance(s.get("run"), str) and _CONTRACT_FILE in s["run"]]


def _runs_contract(workflow: dict) -> bool:
    return bool(_guard_steps(workflow))


def _deploy_steps(workflow: dict) -> list[dict]:
    """Steps that build the deployment unit."""
    return [
        s
        for s in _steps(workflow)
        if isinstance(s.get("run"), str)
        and "docker build" in s["run"]
        and _DEPLOY_DIR in s["run"]
    ]


def _smoke_steps(workflow: dict) -> list[dict]:
    """Steps that actually run the deployment unit's image."""
    return [s for s in _steps(workflow) if isinstance(s.get("run"), str) and "docker run" in s["run"]]


def _tracked_deploy_paths() -> list[str]:
    """Every tracked file under the deployment unit — the guard's own domain."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", _DEPLOY_DIR],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return sorted(p for p in result.stdout.split("\0") if p)


def _contract_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_contract(_load(p))]


# ---------------------------------------------------------------- detector controls


def test_runs_contract_detector_distinguishes_the_forms():
    runs = {"jobs": {"j": {"steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q"}]}}}
    other = {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_natlas_developer_lab.py -q"}]}}}
    assert _runs_contract(runs)
    assert not _runs_contract(other)


def test_deploy_detector_distinguishes_the_forms():
    builds = {"jobs": {"j": {"steps": [{"run": "docker build -t x deploy/n-atlas-server"}]}}}
    other = {"jobs": {"j": {"steps": [{"run": "docker build --pull -t x ."}]}}}
    assert _deploy_steps(builds)
    assert not _deploy_steps(other)


def test_smoke_detector_distinguishes_the_forms():
    runs_it = {"jobs": {"j": {"steps": [{"run": "cid=$(docker run -d natlas:ci)"}]}}}
    ignores_it = {"jobs": {"j": {"steps": [{"run": "docker build -t x deploy/n-atlas-server"}]}}}
    assert _smoke_steps(runs_it)
    assert not _smoke_steps(ignores_it)


def test_selector_accepts_the_forms_github_uses():
    filt = {"tests/test_natlas_selfhost_contract.py", "deploy/n-atlas-server/**"}
    assert _selects_path(filt, "tests/test_natlas_selfhost_contract.py")
    assert _selects_path(filt, "deploy/n-atlas-server/Dockerfile")
    assert _selects_path(filt, "deploy/n-atlas-server/app.py")


def test_selector_rejects_an_incomplete_filter():
    # The incomplete shape the negative control below feeds to the invariant.
    filt = {"tests/test_natlas_selfhost_contract.py"}
    assert _selects_path(filt, "tests/test_natlas_selfhost_contract.py")
    assert not _selects_path(filt, "deploy/n-atlas-server/Dockerfile")


# ---------------------------------------------------------------- the invariant


def test_a_workflow_executes_the_selfhost_contract():
    """A guard no gate runs is decoration, not a boundary."""
    assert _contract_workflows(), (
        "no workflow runs tests/test_natlas_selfhost_contract.py; the self-host contract "
        "holds only when a human runs the suite by hand"
    )


@pytest.mark.parametrize("name", _contract_workflows())
def test_contract_workflow_is_selected_by_the_whole_deployment_unit(name: str):
    """The filter must cover the guard's domain, not a remembered subset."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is None or paths, f"{name} does not trigger on pull_request with paths"
    assert _selects_path(paths, _CONTRACT_FILE), f"{name} runs the contract but its filter omits it"
    domain = _tracked_deploy_paths()
    assert domain, f"git ls-files returned no files under {_DEPLOY_DIR}; layout changed"
    omitted = [p for p in domain if not _selects_path(paths, p)]
    assert not omitted, (
        f"{name} runs the self-host contract but its pull_request paths filter omits "
        f"{len(omitted)} tracked file(s) under {_DEPLOY_DIR}, e.g. {omitted[:5]}"
    )


@pytest.mark.parametrize("name", _contract_workflows())
def test_contract_step_can_fail_the_job(name: str):
    """A guard step that cannot fail the job is not a gate."""
    workflow = _load(WORKFLOWS / name)
    for step in _guard_steps(workflow):
        assert not step.get("continue-on-error", False), (
            f"{name} runs the self-host contract with continue-on-error, so the job stays "
            "green when the deployment unit drifts from the adapter contract"
        )


def test_a_workflow_builds_and_runs_the_deployment_unit():
    """Pinning the Dockerfile's text is not proof it starts; the image must be run.

    The image on `main` built cleanly and then exited with
    `error: invalid argument: /bin/sh`, so a build-only job would have passed.
    """
    built = [p.name for p in _workflow_paths() if _deploy_steps(_load(p))]
    assert built, f"no workflow builds {_DEPLOY_DIR}; the deployment unit is unexercised"
    smoked = [name for name in built if _smoke_steps(_load(WORKFLOWS / name))]
    assert smoked, (
        f"a workflow builds {_DEPLOY_DIR} but none runs the image; a clean `docker build` "
        "does not prove the container can start"
    )


# ---------------------------------------------------------------- control workflow


def test_the_gate_selects_its_own_wiring_guard():
    """A gate that rejects the branch it watches is the omission class again."""
    name = _contract_workflows()[0]
    paths = _path_filter(_trigger_block(_load(WORKFLOWS / name)), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WIRING_FILE)
