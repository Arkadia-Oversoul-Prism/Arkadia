"""
Test-session isolation for the Knowledge OS runtime state.
=========================================================
Root-level pytest configuration for the repository.

Several test modules redirect `ARKADIA_DB_PATH` to a private tempdir at *import*
time, but `knowledge.vault` resolves `VAULT_ROOT = Path("vault")` relative to the
process cwd. A bare `pytest tests/` therefore writes real note files into the
repository's tracked-adjacent `vault/` tree — including synthetic
private-boundary canary material. `vault/` is not gitignored (only `*.db` is),
so those files are stageable by any routine `git add -A`, and an unattended
commit can fold synthetic private-vault material into canon.

This fixture closes that gap once, for every test module, without editing the
modules that already sandbox themselves.
"""
from __future__ import annotations

import os
import tempfile

import pytest

_SESSION_STATE = tempfile.mkdtemp(prefix="arkadia_pytest_session_")


@pytest.fixture(scope="session", autouse=True)
def _sandbox_knowledge_runtime():
    """Redirect all Knowledge OS runtime state to a throwaway directory.

    Applied at session scope, before any test module is collected or imported,
    so that a module-level `os.environ["ARKADIA_DB_PATH"] = ...` (the existing
    convention in `tests/test_isolation.py` et al.) still takes precedence.
    """
    os.environ.setdefault("ARKADIA_DB_PATH", os.path.join(_SESSION_STATE, "knowledge.db"))

    import knowledge
    from knowledge import db as _db
    from knowledge import vault as _vault

    # `knowledge.db` snapshots the env var into a module constant at import time,
    # and `knowledge` re-exports that same constant object.
    _db._DB_PATH = _db.Path(os.environ["ARKADIA_DB_PATH"])
    knowledge._DB_PATH = _db._DB_PATH

    vault_root = _vault.Path(os.path.join(_SESSION_STATE, "vault"))
    _vault.VAULT_ROOT = vault_root
    knowledge.VAULT_ROOT = vault_root
    yield
