"""Boundary guard: the `.gitleaks.toml` config guard must be executed in CI.

`tests/test_gitleaks_config_guard.py` validates the root `.gitleaks.toml` that the
Full-history secret scan (`gitleaks/gitleaks-action@v3` in
`.github/workflows/security-secret-scan.yml`) reads. A config that does not parse makes
the scan abort *without scanning*, and an unanchored `allowlist.regexes` entry
over-suppresses findings — both silent failures at the boundary the guard holds.

Measured on `main` @ `850216fc`: the guard is executed by **no** workflow.
`grep -rln test_gitleaks_config_guard .github/workflows/` returns nothing, so it held
only when a human ran the suite by hand. `provider-routing.yml` — the only workflow
that runs the full suite — is path-filtered to `weaver/**`, `providers/**`,
`api/lab_routes.py` and named files, so a commit that edits `.gitleaks.toml` (or adds
the malformed entry the guard rejects) never ran it. A guard no gate executes is
decoration; this module keeps it executed.

The invariant is stated generically over every workflow that **executes** the guard:

1. Some workflow must execute it with pytest on `pull_request`.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the guard can be
   executed against an exact revision without a source change under the corpus.
3. Every declared `paths` filter must select **every input the guard reads**. Those
   inputs are derived from the guard's own source by AST — the module-level config
   constants it names — not restated here. A second hand-maintained copy drifts, and a
   drifted copy makes the coverage assertion vacuous.
4. An executing step must be able to fail the run: no step- or job-level
   `continue-on-error`, no `if: false`. Otherwise the job stays green when the config
   stops parsing.

The detector is proven against the forms it is meant to catch (negative controls),
including the mention-without-executing form, each exemption form, and a filter that
omits the guard's declared input, so deleting or disarming the wiring cannot pass.
"""

from __future__ import annotations

import ast
import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_gitleaks_config_guard_ci_wiring.py"
_CONTRACT_FILE = "tests/test_gitleaks_config_guard.py"
_WORKFLOW_FILE = ".github/workflows/gitleaks-config-guard.yml"

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}
_CONFIG_SUFFIXES = (".toml", ".json", ".yaml", ".yml")


def _declared_config_inputs() -> list[str]:
    """Repo-relative config paths the guard reads, derived from its source by AST.

    The contract names them as module-level constants of the form
    ``NAME = <root> / "<literal>"`` (e.g. ``GITLEAKS_CONFIG = REPO_ROOT / ".gitleaks.toml"``).
    Reading them from the AST rather than restating them keeps the filter-coverage
    assertion honest: a config added to the guard without a matching filter entry is a
    defect the guard reports instead of one it silently tolerates.
    """
    tree = ast.parse((ROOT / _CONTRACT_FILE).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not (isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div)):
            continue
        literal = value.right
        if not isinstance(literal, ast.Constant) or not isinstance(literal.value, str):
            continue
        candidate = literal.value
        if candidate.endswith(_CONFIG_SUFFIXES) and candidate not in found:
            found.append(candidate)
    return found


_DERIVED_INPUTS = _declared_config_inputs()

_REQUIRED_SELECTORS = tuple([_CONTRACT_FILE, _GUARD_FILE, *_DERIVED_INPUTS])


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping.

    PyYAML parses the bare key `on` as the boolean `True`, so both spellings are read.
    """
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub `paths` glob to a whole-string regex.

    `**/` matches zero or more leading segments (so `**/*.py` selects `weaver.py`),
    a remaining `**` matches anything including `/`, and `*`/`?` match within a single
    segment. Placeholders keep the single-`*` rewrite from clobbering the `**` form.
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
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's `run`, tokenised.

    Comment lines are dropped, so a path that appears only in prose is not a command.
    """
    run = step.get("run")
    if not isinstance(run, str):
        return []
    commands: list[list[str]] = []
    for line in run.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            tokens = stripped.split()
        if tokens:
            commands.append(tokens)
    return commands


def _command_tokens(tokens: list[str]) -> list[str]:
    """The tokens from the invoked executable onward (leading `env`/`NAME=value` dropped)."""
    i = 0
    if tokens and tokens[0] == "env":
        i = 1
    while i < len(tokens):
        head = tokens[i].split("=", 1)[0]
        if "=" in tokens[i] and head.isidentifier():
            i += 1
            continue
        break
    return tokens[i:]


def _pytest_command_index(tokens: list[str]) -> int | None:
    """Index of the `pytest` word **only when it is the invoked command**.

    `pytest x` and `python -m pytest x` count; `echo pytest x` does not — a word that
    merely appears as an argument is not an invocation.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _pytest_invokes(tokens: list[str]) -> bool:
    """Whether this command actually executes pytest against the contract."""
    idx = _pytest_command_index(tokens)
    if idx is None:
        return False
    contract_dir = str(Path(_CONTRACT_FILE).parent)
    for arg in _command_tokens(tokens)[idx + 1:]:
        if arg == _CONTRACT_FILE or arg.startswith(_CONTRACT_FILE + "::"):
            return True
        if arg in {contract_dir, contract_dir + "/"}:
            return True
    return False


def _invocations(workflow: dict):
    found = []
    for job_name, job, step in _steps(workflow):
        if any(_pytest_invokes(cmd) for cmd in _run_lines(step)):
            found.append((job_name, job, step))
    return found


def _mentions_contract(workflow: dict) -> bool:
    if any(_CONTRACT_FILE in str(step.get("run", "")) for _, _, step in _steps(workflow)):
        return True
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        if _CONTRACT_FILE in (_path_filter(trigger, event) or set()):
            return True
    return False


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _incomplete_filters(trigger_block: dict) -> list[str]:
    """Every declared `paths` filter must select every input the guard reads.

    Stated per filter rather than over their union: a union can be complete while the
    `pull_request` filter omits the input, which is precisely the defect class this
    guard exists to catch.
    """
    defects: list[str] = []
    for event in ("pull_request", "push"):
        path_filter = _path_filter(trigger_block, event)
        if path_filter is None:
            continue  # event not declared, or all paths selected
        omitted = [s for s in _REQUIRED_SELECTORS if not _selects_path(path_filter, s)]
        if omitted:
            defects.append(f"{event} paths filter omits {', '.join(omitted)}")
    return defects


def _is_falsey_condition(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY_CONDITIONS


def _exemption(job: dict, step: dict) -> str | None:
    if job.get("continue-on-error", False):
        return "job continue-on-error"
    if _is_falsey_condition(job.get("if", "")):
        return "job if: false"
    if _is_falsey_condition(step.get("if", "")):
        return "step if: false"
    if step.get("continue-on-error", False):
        return "step continue-on-error"
    return None


def _effective_invocations(workflow: dict):
    return [
        (name, job, step)
        for name, job, step in _invocations(workflow)
        if _exemption(job, step) is None
    ]


def _candidates() -> list[tuple[Path, dict]]:
    out = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _mentions_contract(workflow):
            out.append((path, workflow))
    return out


_EXEMPTION_DEFECT = (
    "no effective step executes the contract "
    "(a mention is not an execution; or the step is exempted by "
    "continue-on-error / if: false)"
)


def _audit(workflow: dict) -> list[str]:
    if not _mentions_contract(workflow):
        return []
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _effective_invocations(workflow):
        defects.append(_EXEMPTION_DEFECT)
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    defects.extend(_incomplete_filters(trigger))
    return defects


def test_the_guard_reads_at_least_one_declared_config_input():
    """The derived domain must not be empty, or the coverage assertion is vacuous."""
    assert _DERIVED_INPUTS, (
        f"{_CONTRACT_FILE} declares no module-level `<root> / \"<config>\"` constant; "
        "the filter-coverage assertion would be vacuous"
    )


def test_derived_selectors_resolve_to_real_paths():
    assert (ROOT / _CONTRACT_FILE).is_file()
    assert (ROOT / _GUARD_FILE).is_file()
    for rel in _DERIVED_INPUTS:
        assert (ROOT / rel).is_file(), f"derived input {rel} does not exist"


def test_some_workflow_executes_the_gitleaks_config_guard():
    executed = [path for path, workflow in _candidates() if _effective_invocations(workflow)]
    assert executed, (
        f"no workflow executes {_CONTRACT_FILE} with pytest: the `.gitleaks.toml` config "
        "guard is a guard that no gate executes"
    )


@pytest.mark.parametrize("path,workflow", _candidates(), ids=lambda v: getattr(v, "name", None))
def test_every_candidate_workflow_is_executable_and_can_fail(path: Path, workflow: dict):
    defects = _audit(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


# --- detector controls: prove the guard bites on the forms it names -----------------


def _minimal_workflow(run: str, **trigger) -> dict:
    return {
        True: trigger,
        "jobs": {"gitleaks-config-guard": {"steps": [{"run": run}]}},
    }


_WIRED_TRIGGER = dict(
    pull_request={"paths": list(_REQUIRED_SELECTORS)},
    push={"branches": ["main"], "paths": list(_REQUIRED_SELECTORS)},
    workflow_dispatch=None,
)


def test_positive_control_is_silent_on_the_wired_shape():
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER)
    assert _audit(wf) == []


def test_negative_control_mention_without_execution_is_caught():
    wf = _minimal_workflow(f"echo pytest {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_negative_control_comment_only_is_caught():
    wf = _minimal_workflow(f"# pytest {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_negative_control_filter_omitting_the_declared_config_is_caught():
    """The measured defect: a filter that selects the test but not what it reads."""
    trigger = dict(_WIRED_TRIGGER)
    trigger["pull_request"] = {"paths": [_CONTRACT_FILE, _GUARD_FILE]}
    trigger["push"] = {"branches": ["main"], "paths": [_CONTRACT_FILE, _GUARD_FILE]}
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **trigger)
    defects = _audit(wf)
    assert any("paths filter omits" in d for d in defects), defects


def test_negative_control_asymmetric_filter_is_caught():
    """A complete `pull_request` filter with an incomplete `push` filter is a defect."""
    trigger = dict(_WIRED_TRIGGER)
    trigger["push"] = {"branches": ["main"], "paths": [_CONTRACT_FILE]}
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **trigger)
    assert any("push paths filter omits" in d for d in _audit(wf))


def test_negative_control_undispatchable_is_caught():
    trigger = dict(_WIRED_TRIGGER)
    del trigger["workflow_dispatch"]
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **trigger)
    assert any("workflow_dispatch" in d for d in _audit(wf))


@pytest.mark.parametrize(
    "exempt",
    [
        {"step_continue_on_error": True},
        {"step_if": "false"},
        {"job_continue_on_error": True},
        {"job_if": "false"},
    ],
)
def test_negative_controls_exempted_steps_are_caught(exempt: dict):
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER)
    step = wf["jobs"]["gitleaks-config-guard"]["steps"][0]
    job = wf["jobs"]["gitleaks-config-guard"]
    if "step_continue_on_error" in exempt:
        step["continue-on-error"] = True
    if "step_if" in exempt:
        step["if"] = exempt["step_if"]
    if "job_continue_on_error" in exempt:
        job["continue-on-error"] = True
    if "job_if" in exempt:
        job["if"] = exempt["job_if"]
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_selector_accepts_the_forms_github_uses():
    filt = {".gitleaks.toml", "**/*.toml", "*.toml"}
    assert _selects_path(filt, ".gitleaks.toml")
    assert not _selects_path({_CONTRACT_FILE}, ".gitleaks.toml")


def test_wiring_workflow_selects_its_own_file():
    """A gate that rejects the branch it watches is the omission class again."""
    workflow = _load(ROOT / _WORKFLOW_FILE)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WORKFLOW_FILE)
    assert _selects_path(paths, _GUARD_FILE)
