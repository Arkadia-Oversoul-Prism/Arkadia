"""Regression boundary: the repository must parse.

The P1-A incident (`cd24bb1`, recorded in AGENTS.md) shipped a `SyntaxError` in
`api/main.py` that boot-broke production; every Render deploy of that revision
failed at import. No CI job in this repository runs the pytest suite on a pull
request, so a syntactically invalid commit can reach `main` with every visible
check green. The one manual guard in the ledger -- ``python -m py_compile
api/main.py`` -- only fires if a human remembers it, on one file.

These tests make that guard continuous and repository-wide:

1. ``api/main.py`` parses (the P1-A boot surface).
2. Every Python file the repository tracks parses, at any path depth.

The detector is proven against the exact failure shape it exists to catch -- the
embedded literal newline escape from PR #293 -- so a rewrite cannot silently
disarm it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "api" / "main.py"


def _tracked_python_files() -> list[Path]:
    """Every tracked ``.py`` file, NUL-separated so a space in a name is safe."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return [ROOT / p for p in result.stdout.split("\0") if p]


def _parse_error(path: Path) -> str | None:
    """Return a human-readable parse error, or None when the file parses."""
    try:
        compile(path.read_bytes(), str(path), "exec")
    except (SyntaxError, ValueError) as exc:
        try:
            label = path.relative_to(ROOT)
        except ValueError:
            label = path
        return f"{label}: {type(exc).__name__}: {exc}"
    return None


def test_api_main_parses():
    """The P1-A boot surface must always be importable."""
    assert MAIN.is_file(), "api/main.py is missing from the repository root"
    assert _parse_error(MAIN) is None


def test_every_tracked_python_file_parses():
    """No tracked Python file may carry a SyntaxError.

    A boot-broken revision is unrecoverable at runtime, so the check is
    repository-wide rather than limited to ``api/main.py``: any tracked module
    can be imported by the application at boot.
    """
    files = _tracked_python_files()
    assert files, "git ls-files returned no Python files; the repository layout changed"
    errors = [e for e in (_parse_error(p) for p in files) if e]
    assert not errors, "tracked Python files that do not parse:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Negative control: the detector must flag the exact defect PR #293 shipped.
# ``api/main.py`` there contained the two-character sequence ``\n`` inside a
# single physical line (a collapsed block), so CPython raises
# "unexpected character after line continuation character" at that line.
# ---------------------------------------------------------------------------
_EMBEDDED_NEWLINE_ESCAPE = (
    "def f():\n"
    "    try:\n"
    '        if signal:\\n            reply = await chat()\\n        else:\\n            reply = None\n'
    "    except Exception:\n"
    "        pass\n"
)


def test_detector_flags_an_embedded_newline_escape(tmp_path):
    bad = tmp_path / "embedded.py"
    bad.write_text(_EMBEDDED_NEWLINE_ESCAPE, encoding="utf-8")
    error = _parse_error(bad)
    assert error is not None, "detector missed the PR #293 defect shape"
    assert "line continuation" in error


def test_detector_accepts_a_valid_module(tmp_path):
    good = tmp_path / "valid.py"
    good.write_text("def f():\n    return 1\n", encoding="utf-8")
    assert _parse_error(good) is None


def test_detector_reports_a_generic_syntax_error(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("def f(:\n    pass\n", encoding="utf-8")
    assert _parse_error(broken) is not None
