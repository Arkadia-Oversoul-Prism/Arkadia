"""The Prism coherence guard judges the tracked corpus, not the working tree.

Measured on ``main`` @ ``fd0a4fdc``: the guard derived its README domain with
``sorted(ROOT.rglob("README.md"))``, which also matched ``.pytest_cache/README.md``
— untracked, and ignored by ``.pytest_cache/.gitignore`` (``*``). The scan therefore
reported **33** READMEs after a test run and **32** in a clean checkout, so the
recorded 32-finding verdict moved with the working tree. The findings themselves are
a reserved product/identity decision; a verdict nobody can reproduce is not evidence
for that decision.

``tracked_readmes()`` is the single derivation, and it fails closed: an underivable
domain raises rather than returning ``[]``, because an empty domain would read as a
satisfied contract.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import prism_coherence_check as guard


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


def _repo(root: Path, files: dict[str, str], tracked: tuple[str, ...]) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "guard@example.invalid")
    _git(root, "config", "user.name", "guard")
    for name, body in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    _git(root, "add", *tracked)


def test_domain_is_exactly_the_tracked_corpus():
    domain = guard.tracked_readmes()
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "*README.md"],
        cwd=guard.ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    expected = sorted(p for p in listed.split("\0") if p)
    assert [p.relative_to(guard.ROOT).as_posix() for p in domain] == expected
    assert domain, "the tracked corpus must contain README files"


def test_untracked_readme_is_not_in_the_domain():
    """Negative control: the artifact this defect was measured on."""
    tainted = guard.ROOT / ".pytest_cache" / "README.md"
    if not tainted.exists():
        pytest.skip("the pytest cache artifact is absent in this checkout")
    assert tainted not in guard.tracked_readmes()


def test_a_temp_repo_judges_tracked_nested_readmes_only(tmp_path: Path):
    _repo(
        tmp_path,
        {
            "README.md": "root\n",
            "sub/README.md": "nested\n",
            "cache/README.md": "untracked\n",
        },
        tracked=("README.md", "sub/README.md"),
    )
    names = [p.relative_to(tmp_path).as_posix() for p in guard.tracked_readmes(tmp_path)]
    assert names == ["README.md", "sub/README.md"]


def test_an_underivable_domain_fails_closed(tmp_path: Path):
    """A non-git directory must raise, never yield an empty (passing) domain."""
    with pytest.raises(guard.DomainError):
        guard.tracked_readmes(tmp_path)


def test_main_reports_a_domain_fault_as_exit_2(monkeypatch, capsys):
    def _broken(root: Path | None = None):
        raise guard.DomainError("git ls-files failed: not a repository")

    monkeypatch.setattr(guard, "tracked_readmes", _broken)
    assert guard.main() == 2
    assert "not a repository" in capsys.readouterr().err


def test_a_clean_scan_still_reports_the_reserved_findings(monkeypatch, capsys):
    """Positive control: a derivable domain with a missing marker must FAIL (1)."""
    monkeypatch.setattr(guard, "tracked_readmes", lambda root=None: [])
    monkeypatch.setattr(guard, "check_ui", lambda: [])
    monkeypatch.setattr(guard, "check_readmes", lambda paths: ["x/README.md: missing human authority"])
    assert guard.main() == 1
    assert "FAIL" in capsys.readouterr().out
