"""The /solspire/sources router must not depend on an undeclared import.

``api/source_connections.py`` imports ``cryptography`` at module scope. That
module is reached through ``api/key_routes.py``, which mounts the source router
inside ``try/except Exception`` so a missing dependency cannot boot-break the
app (the P1-A lesson). The cost of that guard is silence: an environment
without the dependency serves a *smaller* route set and looks healthy.

That silence was measured. ``scripts/gate2_backend_observation.py`` reported
``CONTRADICTED`` for backend<->source lineage on ``main:3e1cd00`` purely because
the observer environment lacked ``cryptography``; with the dependency present
the local signature is byte-identical to production (275 operations, digest
``359677ac7fa906d7e952...``). The defect is not the guard -- it is that the
dependency was only ever transitive (via ``pdfminer.six``), so nothing declared
it and nothing failed when it went missing.

These tests hold the declaration as a contract and carry a negative control
proving the check can detect a missing declaration.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "requirements.txt"
SOURCE_CONNECTIONS = REPO_ROOT / "api" / "source_connections.py"

# Standard library + first-party roots that never need declaring.
_NON_DEPENDENCY_ROOTS = {"api", "kernel", "knowledge", "solspire", "lab", "app", "scripts", "tests"}


def _declared_names(text: str) -> set[str]:
    """Requirement names in a requirements file, normalized for comparison.

    Strips comments, environment markers, extras and version specifiers so
    ``uvicorn[standard]>=0.30`` and ``uvicorn`` compare equal.
    """
    names: set[str] = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        line = line.split(";", 1)[0].strip()
        line = line.split("[", 1)[0]
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            line = line.split(sep, 1)[0]
        name = line.strip().replace("_", "-").lower()
        if name:
            names.add(name)
    return names


def _direct_third_party_imports(path: Path) -> set[str]:
    """Top-level, unguarded third-party imports in a module.

    Only module-scope ``import x`` / ``from x import y`` statements count: a
    lazy import inside a function or a ``try/except`` cannot break router
    mounting, so it does not create this class of defect.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return {
        r
        for r in roots
        if r not in sys.stdlib_module_names and r not in _NON_DEPENDENCY_ROOTS
    }


def test_source_connections_has_a_direct_cryptography_import():
    """Precondition: this is a real, unguarded module-scope dependency."""
    assert "cryptography" in _direct_third_party_imports(SOURCE_CONNECTIONS)


def test_cryptography_is_declared_in_requirements():
    assert "cryptography" in _declared_names(REQUIREMENTS.read_text(encoding="utf-8"))


def test_every_direct_import_of_source_connections_is_declared():
    """The general invariant: a module-scope import must be a declared contract."""
    declared = _declared_names(REQUIREMENTS.read_text(encoding="utf-8"))
    undeclared = _direct_third_party_imports(SOURCE_CONNECTIONS) - declared
    assert not undeclared, (
        f"{SOURCE_CONNECTIONS.name} imports {sorted(undeclared)} at module scope "
        "but requirements.txt does not declare them; a deployment omitting them "
        "would silently serve a smaller route set"
    )


def test_negative_control_missing_declaration_is_detected():
    """The check must fail on a requirements file that drops the declaration.

    Without this, the invariant test above could pass for the wrong reason
    (e.g. a parser that returns an empty set for every input).
    """
    doctored = "\n".join(
        line
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip().lower() != "cryptography"
    )
    declared = _declared_names(doctored)
    undeclared = _direct_third_party_imports(SOURCE_CONNECTIONS) - declared
    assert "cryptography" in undeclared


def test_negative_control_parser_is_not_vacuous():
    """Guard against a parser that trivially reports 'nothing declared'."""
    assert "fastapi" in _declared_names("fastapi\n")
    assert "uvicorn" in _declared_names("uvicorn[standard]>=0.30  # web server")
    assert _direct_third_party_imports(SOURCE_CONNECTIONS)


def test_source_router_mounts_when_dependency_is_present():
    """Regression boundary: the four source routes reach the real app."""
    pytest.importorskip("cryptography")
    sys.path.insert(0, str(REPO_ROOT))
    from api.main import app

    paths = set(app.openapi()["paths"])
    expected = {
        "/solspire/sources",
        "/solspire/sources/{source}",
        "/solspire/sources/{source}/connect",
        "/solspire/sources/{source}/sync",
    }
    assert expected <= paths, sorted(expected - paths)
