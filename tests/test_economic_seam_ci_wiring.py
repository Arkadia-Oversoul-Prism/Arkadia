"""Boundary guard: the economic-seam contract must be executed in CI over its
whole derived domain.

The provider-neutral economic seam engine (``economic_seams/``) and the sovereign
scan surface that fronts it (``api/economic_seam_routes.py``) are judged by a set of
contract guards. Measured on ``main`` @ ``850216fc``, the only economic-seam-aware
workflow (``.github/workflows/economic-seam-engine.yml``) executed **five of the
seven** guards that name the seam: its ``paths`` filters and its executing step
restated a fixed inventory, and two guards arrived after that inventory was written
— ``tests/test_economic_seam_authority_boundary.py`` (the sovereign-boundary pin)
and ``tests/test_m02a_ci_gate_integrity.py`` (which pins the CP10 coupling to this
seam). A guard no workflow executes is decoration; this module keeps the domain
executed.

This mirrors the console-contract wiring guard
(``tests/test_prism_console_ci_wiring.py``) exactly, including its accepted
convention: the *judge* derives the domain from guard content at test time and
asserts the gate executes the whole derived set, while the gate carries an
enumerated inventory. The two agree because the gate's ``paths`` filter selects
``tests/**`` and the judge is named in it, so a guard added to the corpus triggers
the judge that reports it unexecuted. Deriving the gate's *inventory* instead is a
separate, wider execution surface and stays with the sovereign.

The invariant is stated generically over the workflows that execute economic-seam
guards:

1. At least one workflow must execute the **whole derived domain** — a step that
   merely *prints* or *comments* a path is a mention, not an execution, and a gate
   that runs part of the domain leaves the rest unjudged.
2. Such a gate must be selected by the surfaces it judges (``economic_seams/**``,
   ``api/economic_seam_routes.py``), by every guard it runs, and by its own file, so
   a change to any of them is judged by the gate it changes.
3. Such a gate must be dispatchable (``workflow_dispatch``), so the contract can be
   executed against an exact revision without a source change under the seam.
4. A complete gate's executing steps must be able to fail the run: no step- or
   job-level ``continue-on-error``, no step- or job-level ``if: false``. The rule is
   scoped to the complete gate(s) deliberately: ``sg-02-fe-2-v.yml`` runs the whole
   suite on a ``continue-on-error: true`` step as recorded pre-existing debt from
   another workstream, and re-litigating that here would be scope expansion.

The detector is proven against the forms it is meant to catch — mention without
executing, partial coverage, the measured pre-fix inventory, and each exemption
form — and against the wired shape it must stay silent on.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_WORKFLOW_FILE = ".github/workflows/economic-seam-engine.yml"

# A guard belongs to the domain when it names the economic seam package or the
# sovereign route surface that fronts it. The ``economic_seams`` stem also matches
# the ``api/economic_seam_routes.py`` spelling, and the joined spellings are
# included because several guards build the path with ``Path`` segments
# (``"api" / "economic_seam_routes.py"``), which a slash-only substring scan misses.
_DOMAIN_NEEDLES = (
    "economic_seams",
    "economic_seam_routes",
    '"economic_seams"',
    "'economic_seams'",
    '"economic_seam_routes"',
    "'economic_seam_routes'",
)

# The surfaces the domain judges; a gate must be selected by these.
_SURFACES = ("economic_seams/**", "api/economic_seam_routes.py")

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}


def _tracked_test_paths() -> list[str]:
    """Every tracked test module, repo-relative — the domain is derived from this."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "tests/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return sorted(p for p in result.stdout.split("\0") if p)


def _economic_seam_domain() -> list[str]:
    """The economic-seam guards, derived from their content at test time.

    Restating the list here would let it drift from the corpus it claims to cover: a
    new economic-seam guard would be omitted from the gate while this file stayed
    green.
    """
    domain = []
    for path in _tracked_test_paths():
        name = Path(path).name
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in _DOMAIN_NEEDLES):
            domain.append(path)
    return domain


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


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

    ``**/`` matches zero or more leading segments, a remaining ``**`` matches anything
    including ``/``, and ``*``/``?`` match within one segment. Placeholders keep the
    single-``*`` rewrite from clobbering the ``**`` expansion.
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


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's ``run``, tokenised.

    Comment lines are dropped, so a path that appears only in prose is not a command.
    A step with no ``run`` (e.g. a ``uses:`` action) yields nothing.
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
    """The tokens from the invoked executable onward (leading ``env``/``NAME=value``)."""
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
    """Index of the ``pytest`` word **only when it is the invoked command**.

    ``pytest x`` and ``python -m pytest x`` count; ``echo pytest x`` does not — a word
    that merely appears as an argument is not an invocation.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _executed_guards(tokens: list[str]) -> set[str]:
    """Which guards this command executes with pytest.

    A guard counts when it is an argument to the pytest command word, or when the
    containing directory is (``pytest tests/ -q`` collects and runs it).
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return set()
    arguments = _command_tokens(tokens)[idx + 1:]
    executed: set[str] = set()
    for guard in _economic_seam_domain():
        if any(
            arg == guard
            or arg.startswith(guard + "::")
            or arg.rstrip("/") == str(Path(guard).parent)
            for arg in arguments
        ):
            executed.add(guard)
    return executed


def _invocations(workflow: dict):
    """Steps that execute at least one economic-seam guard: (job, step, guards)."""
    found = []
    for job_name, job, step in _steps(workflow):
        guards: set[str] = set()
        for command in _run_lines(step):
            guards |= _executed_guards(command)
        if guards:
            found.append((job_name, job, step, guards))
    return found


def _mentions_domain(workflow: dict) -> bool:
    """Anywhere a guard or judged surface appears as a command or trigger path."""
    domain = set(_economic_seam_domain())
    for _, _, step in _steps(workflow):
        run = step.get("run")
        if isinstance(run, str) and any(guard in run for guard in domain):
            return True
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        paths = " ".join(_path_filter(trigger, event) or set())
        if "economic_seams" in paths or "economic_seam_routes" in paths:
            return True
    return False


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _is_falsey_condition(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY_CONDITIONS


def _exemption(job: dict, step: dict) -> str | None:
    """Why an executing step could not fail the run, or None when it can."""
    if job.get("continue-on-error", False):
        return "job continue-on-error"
    if _is_falsey_condition(job.get("if", "")):
        return "job if: false"
    if _is_falsey_condition(step.get("if", "")):
        return "step if: false"
    if step.get("continue-on-error", False):
        return "step continue-on-error"
    return None


def _candidates() -> list[tuple[Path, dict]]:
    """Workflows that reference the domain and are therefore judged by this guard."""
    out = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _mentions_domain(workflow):
            out.append((path, workflow))
    return out


def _effective_executed_by(workflow: dict) -> set[str]:
    """Every economic-seam guard this workflow executes on a step that can fail."""
    executed: set[str] = set()
    for _, job, step, guards in _invocations(workflow):
        if _exemption(job, step) is None:
            executed |= guards
    return executed


def _complete_gates() -> list[tuple[Path, dict]]:
    """Workflows that execute the whole derived domain, not a remembered subset."""
    domain = set(_economic_seam_domain())
    return [
        (path, workflow)
        for path, workflow in _candidates()
        if _effective_executed_by(workflow) >= domain
    ]


def _exemption_defects(workflow: dict) -> list[str]:
    """Executing steps that cannot fail the run — a gate that cannot bite."""
    defects: list[str] = []
    for _, job, step, _ in _invocations(workflow):
        reason = _exemption(job, step)
        if reason:
            defects.append(f"executing step is exempted by {reason}")
    return defects


def _gate_defects(workflow: dict) -> list[str]:
    """Why a complete gate cannot judge the changes it is meant to judge."""
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    for event in ("pull_request", "push"):
        paths = _path_filter(trigger, event)
        if paths is None:
            continue
        for selector in (*_SURFACES, *_economic_seam_domain()):
            if not _selects_path(paths, selector):
                defects.append(f"{event} paths filter omits {selector}")
    return defects


# ---------------------------------------------------------------- the invariants


def test_domain_is_derived_and_not_empty():
    """A derivation that returns nothing would make every assertion vacuous."""
    domain = _economic_seam_domain()
    assert domain, (
        "no tracked test names the economic seam or its route surface; the seam "
        "boundary moved and this guard's derivation must be updated"
    )
    assert "tests/test_economic_seam_engine.py" in domain, (
        "the engine guard is not derived; the needle set no longer matches how guards "
        "name the seam"
    )
    assert "tests/test_economic_seam_authority_boundary.py" in domain, (
        "the sovereign-boundary pin is not derived; the needle set no longer matches "
        "how guards name the seam"
    )


def test_a_workflow_executes_the_whole_economic_seam_contract():
    """A domain executed in part, or by no gate, is not a boundary."""
    complete = _complete_gates()
    assert complete, (
        "no workflow executes the whole economic-seam domain: the guards that are not "
        "executed hold only when a human runs the suite by hand"
    )


@pytest.mark.parametrize(
    "path,workflow", _complete_gates(), ids=lambda v: getattr(v, "name", None)
)
def test_complete_gate_is_selected_by_everything_it_judges(path: Path, workflow: dict):
    defects = _gate_defects(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


@pytest.mark.parametrize(
    "path,workflow", _complete_gates(), ids=lambda v: getattr(v, "name", None)
)
def test_complete_gate_can_fail_the_run(path: Path, workflow: dict):
    defects = _exemption_defects(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


def test_wiring_workflow_is_a_complete_gate_that_selects_itself():
    """A gate that rejects the branch it watches is the omission class again."""
    complete = dict((p.name, w) for p, w in _complete_gates())
    assert Path(_WORKFLOW_FILE).name in complete, (
        f"{_WORKFLOW_FILE} does not execute the whole economic-seam domain"
    )
    workflow = complete[Path(_WORKFLOW_FILE).name]
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WORKFLOW_FILE)


# --- detector controls: prove the guard bites on the forms it names -----------------

_DOMAIN = _economic_seam_domain()
_ONE = "tests/test_economic_seam_engine.py"
_ALL = " ".join(_DOMAIN)


def _minimal_workflow(run: str, **trigger) -> dict:
    return {
        True: trigger,
        "jobs": {"economic-seam-engine": {"steps": [{"run": run}]}},
    }


_WIRED_TRIGGER = dict(
    pull_request={"paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
    push={"branches": ["main"], "paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
    workflow_dispatch=None,
)


def test_positive_control_is_silent_on_the_wired_shape():
    wired = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    assert _gate_defects(wired) == []
    assert _effective_executed_by(wired) >= set(_DOMAIN)


def test_positive_control_accepts_a_directory_invocation():
    """`pytest tests/ -q` executes the whole domain; it must not be flagged."""
    wired = _minimal_workflow("python -m pytest tests/ -q", **_WIRED_TRIGGER)
    assert _effective_executed_by(wired) >= set(_DOMAIN)


def test_negative_control_mention_without_executing_is_flagged():
    printing = _minimal_workflow(f"echo {_ALL}", **_WIRED_TRIGGER)
    assert _effective_executed_by(printing) == set()


def test_negative_control_comment_only_mention_is_flagged():
    commented = _minimal_workflow(f"# run {_ALL}", **_WIRED_TRIGGER)
    assert _effective_executed_by(commented) == set()


@pytest.mark.parametrize(
    "run",
    [
        f"echo pytest {_ALL}",
        f"printf %s pytest {_ALL}",
        f"echo 'python -m pytest {_ALL}'",
    ],
)
def test_negative_control_pytest_as_an_argument_is_flagged(run: str):
    """`pytest` appearing as an *argument* to another command is not an invocation."""
    assert _effective_executed_by(_minimal_workflow(run, **_WIRED_TRIGGER)) == set()


def test_negative_control_partial_domain_is_not_a_complete_gate():
    """The measured pre-fix shape: five of seven guards, the boundary pin unrun."""
    partial = _minimal_workflow(f"python -m pytest {_ONE} -q", **_WIRED_TRIGGER)
    executed = _effective_executed_by(partial)
    assert executed == {_ONE}
    assert not executed >= set(_DOMAIN), "a partial executor is not a complete gate"


def test_negative_control_flags_the_shipped_inventory():
    """The exact `main` shape: two guards absent from both filter and step."""
    shipped_step = (
        "pytest -q tests/test_economic_seam_engine.py "
        "tests/test_economic_seam_correlation.py tests/test_nocopo_adapter.py "
        "tests/test_market_data.py tests/test_deal_sheet.py"
    )
    shipped_paths = [
        "economic_seams/**",
        "api/economic_seam_routes.py",
        "tests/test_economic_seam_engine.py",
        "tests/test_economic_seam_correlation.py",
        "tests/test_nocopo_adapter.py",
        "tests/test_market_data.py",
        "economic_seams/deal_sheet.py",
        "tests/test_deal_sheet.py",
        ".github/workflows/economic-seam-engine.yml",
    ]
    shipped = _minimal_workflow(
        shipped_step,
        pull_request={"paths": shipped_paths},
        push={"branches": ["main"], "paths": shipped_paths},
    )
    executed = _effective_executed_by(shipped)
    assert "tests/test_economic_seam_authority_boundary.py" not in executed, (
        "the pre-fix inventory must be measured as omitting the boundary pin"
    )
    assert "tests/test_m02a_ci_gate_integrity.py" not in executed, (
        "the pre-fix inventory must be measured as omitting the CP10 coupling pin"
    )
    assert not executed >= set(_DOMAIN), "the pre-fix shape must not read as complete"
    defects = _gate_defects(shipped)
    assert any("test_economic_seam_authority_boundary" in d for d in defects)
    assert "no workflow_dispatch: contract not executable on demand" in defects


def test_negative_control_flags_incomplete_filter():
    incomplete = _minimal_workflow(
        f"python -m pytest {_ALL} -q",
        pull_request={"paths": [_ONE]},
        workflow_dispatch=None,
    )
    defects = _gate_defects(incomplete)
    assert defects, "a filter selecting one guard must not pass"
    assert all("paths filter omits" in d for d in defects)


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_continue_on_error(placement: str):
    workflow = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    if placement == "step":
        workflow["jobs"]["economic-seam-engine"]["steps"][0]["continue-on-error"] = True
    else:
        workflow["jobs"]["economic-seam-engine"]["continue-on-error"] = True
    assert _exemption_defects(workflow) == [
        f"executing step is exempted by {placement} continue-on-error"
    ]


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_if_false(placement: str):
    workflow = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    if placement == "step":
        workflow["jobs"]["economic-seam-engine"]["steps"][0]["if"] = "false"
    else:
        workflow["jobs"]["economic-seam-engine"]["if"] = "${{ false }}"
    assert _exemption_defects(workflow) == [
        f"executing step is exempted by {placement} if: false"
    ]


def test_selector_rejects_unrelated_paths():
    """A selector that matched everything would make the filter assertions vacuous."""
    assert not _selects_path({"solspire/**"}, "tests/test_economic_seam_engine.py")
    assert not _selects_path({"api/*.py"}, "api/sub/module.py")


def test_detector_ignores_workflows_that_do_not_mention_the_domain():
    unrelated = _minimal_workflow(
        "python -m pytest tests/test_other.py -q", workflow_dispatch=None
    )
    assert not _mentions_domain(unrelated)
