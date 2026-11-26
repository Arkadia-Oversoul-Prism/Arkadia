"""Boundary guard: every global a tracked module references must resolve.

``research/oversoul_prism_144/test_substrate.py`` called ``transform_node`` without
importing it. The call sat inside

    try:
        transform_node(genesis, address, claim_updates={"authorization_id": "AUTH-001"})
        assert False, "authority smuggling must fail closed"
    except ValueError as exc:
        assert "authority" in str(exc)

so the module raised ``NameError`` instead of exercising the boundary, and the
package README's claim that the harness "rejects authority-shaped fields at the
transformation boundary" rested on an assertion that never ran. ``compile()``
cannot see this: the module is syntactically valid, and the boot-syntax guard
(``tests/test_boot_syntax_boundary.py``) is therefore blind to it.

This module states the invariant that would have caught it, over the corpus the
repository actually tracks:

    for every tracked ``.py`` file, every name referenced as a global resolves at
    module scope or is a builtin.

The domain is derived from ``git ls-files`` at test time, so a new module is
judged without editing this file. Modules that bind names dynamically (a star
import, or a call to ``globals``/``exec``/``eval``) cannot be judged statically
and must be pinned in ``DYNAMIC_BINDING_EXEMPT`` with a reason -- today the set is
empty, so the guard judges every module.

The detector is proven against the exact pre-repair source (a negative control)
and against the repaired source (a positive control), so a rewrite cannot silently
disarm it.
"""

from __future__ import annotations

import ast
import builtins
import subprocess
import symtable
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

GUARD_FILE = "tests/test_python_global_reference_integrity.py"
BOOT_SYNTAX_GUARD = "tests/test_boot_syntax_boundary.py"

# Names the interpreter binds for every module without the source declaring them.
IMPLICIT_MODULE_NAMES = frozenset(
    {
        "__annotations__",
        "__builtins__",
        "__cached__",
        "__dict__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
    }
)

# A module that binds globals dynamically cannot be judged by a static walk.
# Pinned, with the reason, so an exemption is a visible change rather than a
# silent weakening. Measured at the repair: the set is empty.
DYNAMIC_BINDING_EXEMPT: dict[str, str] = {}

_DYNAMIC_CALLS = frozenset({"globals", "exec", "eval"})

# The import blocks exactly as they stood before the repair (verbatim, so the
# negative control feeds the detector the shape that shipped, not a paraphrase).
_PRE_REPAIR_SOURCE = '''from .substrate import NodeAddress, PrismState, replay, validate_delta

from .substrate import (
    BranchResult, StateDelta,
    assert_non_governing,
    reconcile_branches,
    replay_branch,
)


def test_authority_smuggling_is_rejected_at_transformation_boundary():
    genesis = PrismState(claims={"probe.fact": "seed"})
    address = NodeAddress("A01", "L01")
    try:
        transform_node(genesis, address, claim_updates={"authorization_id": "AUTH-001"})
        assert False, "authority smuggling must fail closed"
    except ValueError as exc:
        assert "authority" in str(exc)
'''

_REPAIRED_SOURCE = _PRE_REPAIR_SOURCE.replace(
    "    replay_branch,\n)", "    replay_branch,\n    transform_node,\n)"
)


def _tracked_python_files() -> list[str]:
    """Every tracked ``.py`` path, repo-relative; NUL-separated so names are safe."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return sorted(p for p in result.stdout.split("\0") if p)


def _dynamic_binding_reason(tree: ast.AST) -> str | None:
    """Why a module cannot be judged statically, or None when it can."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            return f"star import at line {node.lineno}"
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _DYNAMIC_CALLS
        ):
            return f"{node.func.id}() at line {node.lineno}"
    return None


def _referenced_globals(table: symtable.SymbolTable) -> set[str]:
    """Names read as globals anywhere inside a module, nested scopes included."""
    found: set[str] = set()

    def walk(current: symtable.SymbolTable) -> None:
        for child in current.get_children():
            walk(child)
        for symbol in current.get_symbols():
            if symbol.is_global() and symbol.is_referenced():
                found.add(symbol.get_name())

    walk(table)
    return found


def undefined_globals(source: str, label: str = "<source>") -> list[str]:
    """Global names a module references without defining them at module scope."""
    tree = ast.parse(source)
    if _dynamic_binding_reason(tree) is not None:
        return []
    table = symtable.symtable(source, label, "exec")
    defined = {s.get_name() for s in table.get_symbols()}
    defined |= set(dir(builtins)) | IMPLICIT_MODULE_NAMES
    return sorted(n for n in _referenced_globals(table) if n not in defined)


# --------------------------------------------------------------- detector controls


def test_detector_flags_the_pre_repair_source():
    """The exact shape that shipped must be reported, not accepted."""
    assert undefined_globals(_PRE_REPAIR_SOURCE) == ["transform_node"]


def test_detector_accepts_the_repaired_source():
    """Positive control: the same source with the import is clean."""
    assert undefined_globals(_REPAIRED_SOURCE) == []


def test_exemption_detector_recognises_dynamic_binding():
    """An exemption that never fires would make the exemption set meaningless."""
    star = "from os.path import *\nprint(join)\n"
    injected = "globals()['x'] = 1\nprint(x)\n"
    assert _dynamic_binding_reason(ast.parse(star)) is not None
    assert _dynamic_binding_reason(ast.parse(injected)) is not None
    assert _dynamic_binding_reason(ast.parse("import os\nprint(os.sep)\n")) is None


def test_every_exemption_is_pinned_with_a_reason_and_exists():
    """A stale exemption is drift; an unexplained one is a silent weakening."""
    tracked = set(_tracked_python_files())
    for path, reason in DYNAMIC_BINDING_EXEMPT.items():
        assert path in tracked, f"{path} is exempted but is not tracked any more"
        assert reason.strip(), f"{path} is exempted without a stated reason"


# ------------------------------------------------------------------- the invariant


def test_no_tracked_module_references_an_undefined_global():
    """A referenced-but-undefined global is a defect whether or not a test runs it."""
    files = _tracked_python_files()
    assert len(files) > 100, (
        f"git ls-files returned {len(files)} Python files; the derived domain is "
        "suspiciously small, so a green result here would be vacuous"
    )

    offenders: list[str] = []
    for relative in files:
        if relative in DYNAMIC_BINDING_EXEMPT:
            continue
        path = ROOT / relative
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            missing = undefined_globals(source, relative)
        except SyntaxError:
            # Parsing is the boot-syntax guard's invariant, judged on the same corpus.
            continue
        if missing:
            offenders.append(f"{relative}: {', '.join(missing)}")

    assert not offenders, (
        "these tracked modules reference global names they never define or import "
        "(the module raises NameError instead of running):\n  " + "\n  ".join(offenders)
    )


# ------------------------------------------------------------------------- wiring


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _steps(workflow: dict) -> list[dict]:
    seen: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        seen.extend(job.get("steps") or [])
    return seen


def _run_scripts(workflow: dict) -> list[str]:
    return [s["run"] for s in _steps(workflow) if isinstance(s.get("run"), str)]


def _executing_workflows() -> list[str]:
    return [
        path.name
        for path in _workflow_paths()
        if any(GUARD_FILE in script for script in _run_scripts(_load(path)))
    ]


def test_a_workflow_executes_this_guard():
    """A guard no gate runs is decoration, not a boundary."""
    assert _executing_workflows(), (
        f"no workflow runs {GUARD_FILE}; the undefined-global boundary would hold "
        "only when a human ran the suite by hand"
    )


@pytest.mark.parametrize("name", _executing_workflows())
def test_executing_workflow_shares_the_domain_complete_filter(name: str):
    """This guard's domain is every tracked ``.py`` file, so its gate must select them all.

    ``tests/test_boot_syntax_ci_wiring.py`` proves that the workflow running the
    boot-syntax guard selects every tracked Python file. Requiring this guard to be
    executed alongside that one inherits the proven filter instead of restating it.
    """
    scripts = _run_scripts(_load(WORKFLOWS / name))
    assert any(BOOT_SYNTAX_GUARD in script for script in scripts), (
        f"{name} runs {GUARD_FILE} but not {BOOT_SYNTAX_GUARD}; its paths filter is "
        "then not proven to select every tracked Python file, so a new module could "
        "be added at a path this gate never runs on"
    )


@pytest.mark.parametrize("name", _executing_workflows())
def test_executing_step_can_fail_the_job(name: str):
    """A step that cannot fail the job is not a gate."""
    workflow = _load(WORKFLOWS / name)
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if isinstance(step.get("run"), str) and GUARD_FILE in step["run"]:
                assert not step.get("continue-on-error", False), (
                    f"{name} runs {GUARD_FILE} with continue-on-error"
                )
                assert not job.get("continue-on-error", False), (
                    f"{name}'s job for {GUARD_FILE} is continue-on-error"
                )
