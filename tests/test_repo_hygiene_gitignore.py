"""Repository hygiene — the canonical store's SQLite family must never be stageable.

`data/solspire_projects.db` is an untracked runtime database. It runs in WAL mode
(`PRAGMA journal_mode=WAL` in `solspire/workspace_manager.py` and
`solspire/eden_ops_02.py`), so SQLite materialises `-wal` and `-shm` siblings
alongside it. `.gitignore`'s `*.db` rule covers only the database file itself.

That asymmetry is a real hazard, not cosmetics: the sidecars appear the moment a
test session touches the canonical store, so `git add -A` in a hygiene pass would
stage them. These assertions pin the invariant rather than the literal pattern, so
the rule may be expressed in any equivalent form.

The last assertion is the load-bearing one. Ignoring the file hides the symptom;
the defect is that a module-level `_DB_PATH` snapshot points into the repository.
`conftest.py::_sandbox_solspire_store` rebinds those copies, and this test fails
if that fixture is ever removed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

CANONICAL_DB = "data/solspire_projects.db"

#: Every file SQLite may materialise for a WAL-mode database.
SQLITE_FAMILY = (CANONICAL_DB, f"{CANONICAL_DB}-wal", f"{CANONICAL_DB}-shm")


def _is_ignored(path: str) -> bool:
    """Ask git itself, so the assertion tracks any equivalent ignore rule."""
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    pytest.skip(f"git check-ignore unavailable: {result.stderr.strip()}")


@pytest.mark.parametrize("path", SQLITE_FAMILY)
def test_canonical_store_is_never_stageable(path: str) -> None:
    assert _is_ignored(path), (
        f"{path} is not ignored; a test session that touches the canonical store "
        f"would leave it stageable by `git add -A`"
    )


def test_canonical_store_is_not_tracked() -> None:
    """Ignoring is the guardrail; not being tracked is the actual invariant."""
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", CANONICAL_DB],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert tracked.returncode != 0, f"{CANONICAL_DB} is tracked and must not be"


def test_scratch_db_sidecars_remain_ignored() -> None:
    """Regression guard for the pre-existing `tests/_spine_test.db*` rule."""
    for path in ("tests/_spine_test.db", "tests/_spine_test.db-wal",
                 "tests/_spine_test.db-shm"):
        assert _is_ignored(path), f"{path} lost its ignore rule"


def test_attention_outbox_is_never_stageable() -> None:
    """The worker's attention outbox is runtime output, not review state.

    `weaver/engineering_worker.py::_record_attention` appends to
    `docs/control-plane/evidence/attention-events.jsonl` on every run, so the file
    materialises the moment a scheduler session or a local test session runs the
    worker — untracked and, without an ignore rule, stageable by `git add -A` in a
    hygiene pass. Its sibling per-run reports are already ignored; this pins the
    same invariant for the outbox.
    """
    assert _is_ignored("docs/control-plane/evidence/attention-events.jsonl"), (
        "docs/control-plane/evidence/attention-events.jsonl is not ignored; a worker "
        "run would leave it stageable by `git add -A`"
    )


def test_attention_outbox_control_is_not_ignored() -> None:
    """Negative control: the ignore is a rule for the outbox, not a blanket tree ignore.

    Without this, `test_attention_outbox_is_never_stageable` would still pass if a
    future edit ignored all of `docs/control-plane/evidence/`, which would also hide
    durable acceptance records the next scheduler wake must reconstruct from.
    """
    assert not _is_ignored("docs/control-plane/evidence/__hygiene_control__.txt"), (
        "a non-outbox file under the evidence tree is ignored; the ignore rule is "
        "broader than the runtime output it is meant to cover"
    )


def test_scheduler_session_result_is_never_stageable() -> None:
    """The scheduler's root-level run result is runtime output, not review state.

    `.github/workflows/arkadia-engineering-scheduler.yml` writes
    `engineering-session-result.json` to the repository root on every session — the
    same run that appends the attention outbox — and then uploads it as a build
    artifact. Untracked and, without an ignore rule, stageable by `git add -A` in a
    hygiene pass, which would commit a transient run result to main.
    """
    assert _is_ignored("engineering-session-result.json"), (
        "engineering-session-result.json is not ignored; a scheduler session or a "
        "local reproduction would leave it stageable by `git add -A`"
    )


def test_session_result_ignore_is_scoped_to_the_run_result() -> None:
    """Negative control: the rule names one runtime artifact, not every root file.

    The tracked root manifest (`railway.json`) is durable review
    state that a later session must be able to read. A blanket root-JSON ignore
    would satisfy the assertion above while hiding them.
    """
    for path in ("railway.json",):
        assert not _is_ignored(path), (
            f"{path} is tracked repository state but is ignored; the rule is broader "
            f"than the runtime artifact it is meant to cover"
        )



def test_no_module_resolves_the_repository_canonical_store() -> None:
    """Every module-level `_DB_PATH` copy must point outside the repository.

    This is what `conftest.py::_sandbox_solspire_store` guarantees. Deleting the
    fixture leaves every test green while silently re-pointing thirteen modules at
    `data/solspire_projects.db`, so the defect would be invisible without this.
    """
    import solspire.enterprise_router  # noqa: F401  (import for its side effect)
    import solspire.eden_ops_02  # noqa: F401
    import solspire.workspace_manager  # noqa: F401
    import weaver.enterprise_orchestration  # noqa: F401
    import lab.engineering_lab.store  # noqa: F401

    leaked = []
    for name, module in list(sys.modules.items()):
        if module is None:
            continue
        current = getattr(module, "_DB_PATH", None)
        if not isinstance(current, str):
            continue
        if os.path.basename(current) != "solspire_projects.db":
            continue
        if Path(current).resolve() == (REPO_ROOT / CANONICAL_DB).resolve():
            leaked.append(name)

    assert not leaked, (
        "these modules still resolve the repository's canonical store: "
        f"{sorted(leaked)} — the session sandbox fixture is missing or ineffective"
    )
