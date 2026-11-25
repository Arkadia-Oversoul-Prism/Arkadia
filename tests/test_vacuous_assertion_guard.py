"""A guard that cannot fail is not a guard.

Scans the tracked test corpus for assertions whose test expression is
structurally always true (``assert True`` or ``assert <anything> or True``),
which pass on every tree and therefore protect nothing.
"""
import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _vacuous_kind(node: ast.Assert) -> str | None:
    test = node.test
    if isinstance(test, ast.Constant) and test.value is True:
        return "assert True"
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        last = test.values[-1]
        if isinstance(last, ast.Constant) and last.value is True:
            return "assert ... or True"
    return None


def _vacuous_assertions(source: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assert):
            kind = _vacuous_kind(node)
            if kind:
                found.append((node.lineno, kind))
    return sorted(found)


def _tracked_test_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--", "tests"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    return [ROOT / p for p in out if p.endswith(".py")]


def test_detector_flags_both_vacuous_forms():
    """Negative control: the detector must report the shape it exists to catch."""
    source = (
        "def test_a():\n"
        "    assert True\n"
        "def test_b():\n"
        "    assert x is None or True\n"
    )
    assert _vacuous_assertions(source) == [
        (2, "assert True"),
        (4, "assert ... or True"),
    ]


def test_detector_is_silent_on_a_real_assertion():
    """Positive control: a falsifiable assertion is not reported."""
    assert _vacuous_assertions("def test_a():\n    assert x == 1\n") == []


def test_no_tracked_test_assertion_cannot_fail():
    offenders: list[str] = []
    for path in _tracked_test_files():
        if path == Path(__file__).resolve():
            continue
        for lineno, kind in _vacuous_assertions(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT)}:{lineno} {kind}")
    assert offenders == []
