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

The same shape of gap exists for the canonical SolSpire store. Thirteen modules
(`solspire/*.py`, `weaver/enterprise_orchestration.py`,
`lab/engineering_lab/store.py`) each snapshot

    _DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
        os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
    )

at *import* time. A test that patches only the two or three copies it happens to
import therefore leaves the rest writing to the repository's real
`data/solspire_projects.db` — a silent leak, because those tests still pass.
`test_eden_solspire_01_instantiation.py` and `test_enterprise_onboarding.py`
were both leaking this way. Patching thirteen module constants per test would be
permanently fragile: a fourteenth module added later reopens the hole. Rebinding
every copy once, at session scope, closes the class rather than the instances.
"""
from __future__ import annotations

import os
import sys
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


@pytest.fixture(scope="session", autouse=True)
def _sandbox_solspire_store():
    """Point every module-level copy of the canonical store path at a throwaway DB.

    Rebinds the imported module constants directly rather than relying on the env
    var: the constants were already snapshotted at import time by the time this
    runs. Modules imported later inherit `SOLSPIRE_PROJECTS_DB` from the
    environment, so both the already-imported and not-yet-imported cases are
    covered.
    """
    db_path = os.path.join(_SESSION_STATE, "solspire_projects.db")
    # Forced, not setdefault: a later import must agree with the rebinds below.
    os.environ["SOLSPIRE_PROJECTS_DB"] = db_path

    for module in list(sys.modules.values()):
        if module is None:
            continue
        current = getattr(module, "_DB_PATH", None)
        if isinstance(current, str) and os.path.basename(current) == "solspire_projects.db":
            module._DB_PATH = db_path

    yield
