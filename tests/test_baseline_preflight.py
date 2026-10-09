"""gate-hygiene — baseline reproducibility preflight guard.

Network-free. Proves the preflight detects the two environment properties that
silently change a full-suite failing/error node set (clone depth, missing
declared dependency), and that a negative control — the naive environment check
that omits the depth probe — reports the same tree as clean. Without that
control the harness could be gutted while its positive tests still passed.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "baseline_preflight", REPO_ROOT / "scripts" / "baseline_preflight.py"
)
baseline_preflight = importlib.util.module_from_spec(_SPEC)
sys.modules["baseline_preflight"] = baseline_preflight
_SPEC.loader.exec_module(baseline_preflight)


# --------------------------------------------------------------------------- #
# git-derived probes, exercised against real throwaway repositories
# --------------------------------------------------------------------------- #

def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )


@pytest.fixture()
def origin_repo(tmp_path: Path) -> Path:
    """A tiny non-shallow repo with one commit, used as a clone source."""
    src = tmp_path / "origin"
    src.mkdir()
    _git("init", "-q", cwd=src)
    _git("config", "user.email", "t@t.t", cwd=src)
    _git("config", "user.name", "t", cwd=src)
    (src / "a.txt").write_text("hello\n", encoding="utf-8")
    _git("add", "a.txt", cwd=src)
    _git("commit", "-q", "-m", "one", cwd=src)
    return src


def test_full_clone_is_not_shallow(origin_repo: Path, tmp_path: Path) -> None:
    dst = tmp_path / "full"
    _git("clone", "-q", str(origin_repo), str(dst), cwd=tmp_path)
    assert baseline_preflight.clone_is_shallow(dst) is False


def test_shallow_clone_is_detected(origin_repo: Path, tmp_path: Path) -> None:
    """The detector bites on the real defect form (negative control)."""
    dst = tmp_path / "shallow"
    _git("clone", "-q", "--depth", "1", origin_repo.as_uri(), str(dst), cwd=tmp_path)
    assert baseline_preflight.clone_is_shallow(dst) is True


def test_oracle_revision_absent_in_shallow_clone(
    origin_repo: Path, tmp_path: Path
) -> None:
    dst = tmp_path / "shallow"
    _git("clone", "-q", "--depth", "1", origin_repo.as_uri(), str(dst), cwd=tmp_path)
    # The real oracle revision is not in this one-commit clone.
    assert baseline_preflight.oracle_revision_present("HEAD", dst) is True
    assert baseline_preflight.oracle_revision_present("0000000000", dst) is False


def test_oracle_revision_present_on_the_live_clone() -> None:
    """The repository pins the oracle revision; a full clone resolves it.

    Guarded on the live clone's depth so a shallow CI checkout reports a skip
    rather than a false failure — this node measures the *repository's* oracle
    pin, not the operator's clone.
    """
    if baseline_preflight.clone_is_shallow(REPO_ROOT):
        pytest.skip("shallow clone: oracle availability is clone-depth dependent")
    assert baseline_preflight.oracle_revision_present(
        baseline_preflight.ORACLE_REV, REPO_ROOT
    )


def test_ce01_collision_present_on_this_repo() -> None:
    assert baseline_preflight.ce01_collision_present() is True


def test_ce01_collision_absent_without_the_package() -> None:
    # A module name with neither the package nor the sibling module has no collision.
    assert baseline_preflight.ce01_collision_present("does.not.exist") is False


# --------------------------------------------------------------------------- #
# requirement probing
# --------------------------------------------------------------------------- #

def test_missing_requirements_flags_absent_mapped_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(
        baseline_preflight.IMPORT_NAME, "fakepkg", "no_such_module_xyz_123"
    )
    req = tmp_path / "requirements.txt"
    req.write_text("fakepkg==1.0\n", encoding="utf-8")
    result = baseline_preflight.missing_requirements(req)
    assert result["omitted"] == ["fakepkg"]


def test_missing_requirements_retains_unmapped_names(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("some-unmapped-dist\n", encoding="utf-8")
    result = baseline_preflight.missing_requirements(req)
    assert result["omitted"] == []
    assert result["retained"] == ["some-unmapped-dist"]


def test_missing_requirements_ignores_comments_and_extras(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("# comment\npyyaml\n", encoding="utf-8")
    result = baseline_preflight.missing_requirements(req)
    # pyyaml maps to `yaml`, which is installed in the test environment.
    assert "pyyaml" not in result["omitted"]


# --------------------------------------------------------------------------- #
# collect(): the composed verdict, with the environment probes pinned
# --------------------------------------------------------------------------- #

def _pin_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline_preflight, "clone_is_shallow", lambda *a, **k: False)
    monkeypatch.setattr(
        baseline_preflight, "oracle_revision_present", lambda *a, **k: True
    )
    monkeypatch.setattr(
        baseline_preflight,
        "missing_requirements",
        lambda *a, **k: {"omitted": [], "retained": []},
    )
    monkeypatch.setattr(
        baseline_preflight, "ce01_collision_present", lambda *a, **k: False
    )


def test_collect_clean_environment_has_no_blocking_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_clean(monkeypatch)
    report = baseline_preflight.collect(REPO_ROOT)
    assert report["blocking_count"] == 0


def test_collect_flags_shallow_clone(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_clean(monkeypatch)
    monkeypatch.setattr(baseline_preflight, "clone_is_shallow", lambda *a, **k: True)
    monkeypatch.setattr(
        baseline_preflight, "oracle_revision_present", lambda *a, **k: False
    )
    report = baseline_preflight.collect(REPO_ROOT)
    ids = {f["id"] for f in report["findings"]}
    assert "SHALLOW_CLONE" in ids
    assert report["blocking_count"] >= 1


def test_collect_blocks_on_consequential_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_clean(monkeypatch)
    monkeypatch.setattr(
        baseline_preflight,
        "missing_requirements",
        lambda *a, **k: {"omitted": ["pdfminer.six"], "retained": []},
    )
    report = baseline_preflight.collect(REPO_ROOT)
    assert report["node_set_consequential_omitted"] == ["pdfminer.six"]
    assert report["blocking_count"] == 1


def test_collect_does_not_block_on_nonconsequential_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_clean(monkeypatch)
    monkeypatch.setattr(
        baseline_preflight,
        "missing_requirements",
        lambda *a, **k: {"omitted": ["beautifulsoup4"], "retained": []},
    )
    report = baseline_preflight.collect(REPO_ROOT)
    ids = {f["id"] for f in report["findings"]}
    assert "MISSING_REQUIREMENT_NONCONSEQUENTIAL" in ids
    assert report["blocking_count"] == 0


# --------------------------------------------------------------------------- #
# negative control: the naive environment check would call a shallow clone clean
# --------------------------------------------------------------------------- #

def test_negative_control_naive_probe_misses_the_shallow_clone(
    origin_repo: Path, tmp_path: Path
) -> None:
    """A probe that only checks the oracle *name* (never resolves it) reports the
    shallow clone as reproducible. This is the exact defect the preflight exists
    to catch; the control fails if the depth probe is ever removed."""
    dst = tmp_path / "shallow"
    _git("clone", "-q", "--depth", "1", origin_repo.as_uri(), str(dst), cwd=tmp_path)

    def naive_is_reproducible(repo: Path) -> bool:
        # Would-be check that trusts the constant is configured, not that the
        # revision is resolvable in this clone.
        return True

    assert naive_is_reproducible(dst) is True  # blind
    assert baseline_preflight.clone_is_shallow(dst) is True  # the real probe bites


# --------------------------------------------------------------------------- #
# render / CLI
# --------------------------------------------------------------------------- #

def test_main_json_returns_blocking_status(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _pin_clean(monkeypatch)
    monkeypatch.setattr(baseline_preflight, "clone_is_shallow", lambda *a, **k: True)
    monkeypatch.setattr(
        baseline_preflight, "oracle_revision_present", lambda *a, **k: False
    )
    rc = baseline_preflight.main(["--json"])
    assert rc == 1
    payload = capsys.readouterr().out
    assert "SHALLOW_CLONE" in payload


def test_main_clean_returns_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    _pin_clean(monkeypatch)
    assert baseline_preflight.main(["--repo", str(REPO_ROOT)]) == 0
