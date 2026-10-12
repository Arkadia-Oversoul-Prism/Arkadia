"""Boundary guard: the shared-connection lifecycle guard must be executed in CI.

`tests/test_knowledge_shared_connection_lifecycle.py` holds the `knowledge/db.py`
connection boundary. `get_connection()` caches one connection per thread in
`threading.local()` and treats `None` as the only "needs creating" sentinel, so a
*closed* handle left in that slot is returned unchanged and every later query in the
thread raises `ProgrammingError: Cannot operate on a closed database`.

The defect is **order-dependent**: the file that poisons the shared slot
(`tests/test_sqlite_busy_timeout.py`) is not the file that fails (the voice suites). It
is therefore invisible to per-file runs and can only be judged by a session that runs
both. A guard that no gate executes is decoration, so this module keeps it executed.

The invariant is stated generically over every workflow that **executes** the guard:

1. Some workflow must execute it with pytest on `pull_request`.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the guard can be
   executed against an exact revision without a source change under the corpus.
3. Every declared `paths` filter must select **every input the guard reads**. Those
   inputs are derived from the guard's own source by AST — the local modules it imports
   — not restated here. A second hand-maintained copy drifts, and a drifted copy makes
   the coverage assertion vacuous.
4. An executing step must be able to fail the run: no step- or job-level
   `continue-on-error`, no `if: false`. Otherwise the job stays green when the shared
   slot is poisoned again.
5. The job's environment must satisfy what it executes. A step that invokes a module
   importing a third-party package the job never installs dies on a collection error —
   a red job in which no assertion ran, which is the same false signal the defect gives.

The detector is proven against the forms it is meant to catch (negative controls),
including the mention-without-executing form, each exemption form, and a filter that
omits an input, so deleting or disarming the wiring cannot pass.
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

_GUARD_FILE = "tests/test_knowledge_shared_connection_lifecycle_ci_wiring.py"
_CONTRACT_FILE = "tests/test_knowledge_shared_connection_lifecycle.py"
_WORKFLOW_FILE = ".github/workflows/knowledge-connection-lifecycle-guard.yml"

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}


def _local_imports(module: str) -> list[str]:
    """Repo-relative local modules the contract imports, derived from its AST.

    `from knowledge import db` resolves to `knowledge/db.py`; a bare
    `from test_sqlite_busy_timeout import x` resolves to
    `tests/test_sqlite_busy_timeout.py`. Reading these from the AST rather than
    restating them keeps the filter-coverage assertion honest: an input added to the
    guard without a matching filter entry is a defect the guard reports instead of one
    it silently tolerates.
    """
    tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
    found: list[str] = []

    def add(candidate: Path) -> None:
        if candidate.is_file():
            rel = candidate.relative_to(ROOT).as_posix()
            if rel not in found:
                found.append(rel)

    def add_module(dotted: str) -> None:
        # `knowledge.db` -> `knowledge/db.py` or `knowledge/db/__init__.py`.
        # A bare test module (`test_sqlite_busy_timeout`) lives under `tests/`, which
        # pytest puts on `sys.path` — the guard imports it as a top-level name.
        for root in (ROOT, ROOT / "tests"):
            base = root.joinpath(*dotted.split("."))
            add(base.with_suffix(".py"))
            add(base / "__init__.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                continue
            add_module(node.module)
            for alias in node.names:
                add_module(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                add_module(alias.name)
    return found


_DERIVED_INPUTS = _local_imports(_CONTRACT_FILE)

_REQUIRED_SELECTORS = tuple([_CONTRACT_FILE, _GUARD_FILE, *_DERIVED_INPUTS])


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping. PyYAML parses the bare key `on` as the boolean `True`."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub `paths` glob to a whole-string regex."""
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
    """Each effective shell command in a step's `run`, tokenised, comments dropped."""
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


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _incomplete_filters(trigger_block: dict) -> list[str]:
    """Every declared `paths` filter must select every input the guard reads.

    Stated per filter rather than over their union: a union can be complete while the
    `pull_request` filter omits the input, which is precisely the defect class here.
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


def _executed_modules(job: dict) -> list[str]:
    """Repo-relative test modules this job's steps actually invoke."""
    found: list[str] = []
    for step in (job or {}).get("steps") or []:
        for cmd in _run_lines(step):
            if not _pytest_invokes(cmd):
                continue
            for arg in cmd:
                rel = arg.split("::", 1)[0]
                if rel.endswith(".py") and (ROOT / rel).is_file() and rel not in found:
                    found.append(rel)
    return found


def _module_dependencies(module: str) -> set[str]:
    """Third-party top-level imports of a test module, from its AST."""
    import sys

    tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    third_party: set[str] = set()
    for name in names:
        if name in stdlib or name == "__future__":
            continue
        # A local module is either a repo-root package/module or a bare test module,
        # which pytest resolves from `tests/` because it puts that directory on
        # `sys.path`. Missing the second form would classify the contract's own
        # sibling test as an uninstalled dependency.
        if (
            (ROOT / name).exists()
            or (ROOT / f"{name}.py").exists()
            or (ROOT / "tests" / name).exists()
            or (ROOT / "tests" / f"{name}.py").exists()
        ):
            continue
        third_party.add(name)
    return third_party


def _uninstalled_dependencies(job: dict) -> list[str]:
    """Third-party modules a job executes but never installs.

    The job's environment must satisfy what it runs. A step that invokes a module
    importing a third-party package the job never installs dies on a collection error —
    a red job in which no assertion ran, the same false signal the defect gives.
    """
    installed: set[str] = set()
    for step in (job or {}).get("steps") or []:
        for cmd in _run_lines(step):
            tokens = _command_tokens(cmd)
            if not tokens:
                continue
            if tokens[0] not in {"pip", "pip3", "python", "python3"}:
                continue
            if "install" not in tokens:
                continue
            for arg in tokens[tokens.index("install") + 1:]:
                if arg.startswith("-"):
                    continue
                installed.add(re.split(r"[<>=!~\[;]", arg)[0].strip().lower())
    required: set[str] = set()
    for module in _executed_modules(job):
        required |= _module_dependencies(module)
    # Distribution names differ from import names; `yaml` -> `pyyaml` is the pair this
    # gate needs, matching the repo's existing wiring guard.
    aliases = {"yaml": "pyyaml"}
    missing = []
    for name in sorted(required):
        dist = aliases.get(name, name)
        if name not in installed and dist not in installed:
            missing.append(name)
    return missing


def _mentions_contract(workflow: dict) -> bool:
    """Whether the workflow names the contract in a step or a `paths` filter."""
    if any(_CONTRACT_FILE in str(step.get("run", "")) for _, _, step in _steps(workflow)):
        return True
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        if _CONTRACT_FILE in (_path_filter(trigger, event) or set()):
            return True
    return False


def _candidates() -> list[tuple[Path, dict]]:
    """Workflows that name the contract.

    Scoped to a *mention*, not to a directory-argument reach. `pytest tests/` in
    `provider-routing.yml` does execute the contract, but auditing every workflow whose
    directory argument happens to cover it would report that gate's pre-existing,
    baseline-red debt as a wiring defect of this guard — the reddening the repo's
    existing wiring guards deliberately avoid. A gate that names the guard is the gate
    that owns its execution.
    """
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
    for job_name, job in (workflow.get("jobs") or {}).items():
        if not _effective_invocations({"jobs": {job_name: job}}):
            continue
        missing = _uninstalled_dependencies(job)
        if missing:
            defects.append(
                f"job {job_name} executes modules importing "
                f"{', '.join(missing)} but never installs them"
            )
    return defects


# ---------------------------------------------------------------- invariants

def test_the_derived_domain_is_not_empty():
    """The derived domain must not be empty, or the coverage assertion is vacuous."""
    assert _DERIVED_INPUTS, (
        f"{_CONTRACT_FILE} declares no local import; the filter-coverage assertion "
        "would be vacuous"
    )


def test_derived_selectors_resolve_to_real_paths():
    assert (ROOT / _CONTRACT_FILE).is_file()
    assert (ROOT / _GUARD_FILE).is_file()
    for rel in _DERIVED_INPUTS:
        assert (ROOT / rel).is_file(), f"derived input {rel} does not exist"


def test_some_workflow_executes_the_guard():
    executed = [
        path for path, workflow in _candidates() if _effective_invocations(workflow)
    ]
    assert executed, (
        f"no workflow executes {_CONTRACT_FILE} with pytest: the shared-connection "
        "lifecycle guard is a guard that no gate executes"
    )


@pytest.mark.parametrize("path,workflow", _candidates(), ids=lambda v: getattr(v, "name", None))
def test_every_candidate_workflow_is_executable_and_can_fail(path: Path, workflow: dict):
    defects = _audit(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


# ---------------------------------------------------------------- controls

def test_detector_flags_the_mention_without_executing_form():
    """Negative control: `echo pytest <contract>` is not an execution."""
    tokens = shlex.split(f"echo pytest {_CONTRACT_FILE}")
    assert _pytest_command_index(tokens) is None
    assert not _pytest_invokes(tokens)


def test_detector_accepts_the_real_invocation_forms():
    """Positive control: both invocation spellings count."""
    assert _pytest_invokes(shlex.split(f"pytest {_CONTRACT_FILE} -q"))
    assert _pytest_invokes(shlex.split(f"python -m pytest {_CONTRACT_FILE} -q"))
    assert _pytest_invokes(shlex.split("python -m pytest tests/ -q"))


def test_negative_control_an_omitted_input_is_reported():
    """A filter that selects the guard but omits an input must be reported."""
    partial = {_CONTRACT_FILE, _GUARD_FILE}
    trigger = {"pull_request": {"paths": sorted(partial)}}
    defects = _incomplete_filters(trigger)
    assert defects, "an incomplete filter must be reported"
    assert "knowledge/db.py" in defects[0]


def test_negative_control_each_exemption_form_is_reported():
    for job, step in (
        ({"continue-on-error": True}, {}),
        ({"if": "false"}, {}),
        ({}, {"if": "false"}),
        ({}, {"continue-on-error": True}),
    ):
        assert _exemption(job, step) is not None


def test_negative_control_the_real_workflow_passes_the_detector():
    """Positive control on the real file: the detector is not trivially red."""
    workflow = _load(ROOT / _WORKFLOW_FILE)
    assert _invocations(workflow)
    assert not _incomplete_filters(_trigger_block(workflow))
    assert _effective_invocations(workflow)
