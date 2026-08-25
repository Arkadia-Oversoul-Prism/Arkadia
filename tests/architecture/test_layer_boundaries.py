"""
Architecture Fitness Tests — Layer Boundary Enforcement
=======================================================
Enforces ADR-015: dependencies may point only toward more stable layers.

Run:
    pytest tests/architecture/test_layer_boundaries.py -v

In CI:
    pytest tests/architecture/ --tb=short

These are not unit tests. They parse Python source with the `ast` module —
no code is executed. Safe to run without secrets or a running server.

Failure means a new layer violation was introduced. Either:
  a) Reverse the import (preferred), OR
  b) Add a temporary entry to REGISTERED_ARCHITECTURAL_DEBT in LAYER_MAP.py with a
     documented rationale and deadline.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator

# ── Project root & layer map ─────────────────────────────────────────────────

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

sys.path.insert(0, str(_HERE))
from LAYER_MAP import REGISTERED_ARCHITECTURAL_DEBT, REGISTERED_CIRCULAR_DEBT, LAYER_MAP, ORTHOGONAL_GROUPS, PROJECT_ROOT  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────────────

def _layer_for(path: Path) -> int | None:
    """Return the layer number for a file path, or None if unmapped."""
    rel = path.relative_to(PROJECT_ROOT)
    rel_str = str(rel).replace("\\", "/")

    # Most-specific prefix wins — sort by length descending
    candidates = sorted(
        ((prefix, layer) for prefix, layer in LAYER_MAP.items()
         if rel_str == prefix or rel_str.startswith(prefix + "/")),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    return candidates[0][1] if candidates else None


def _orthogonal_group(path: Path) -> str | None:
    """Return the orthogonal group name for a file, or None."""
    rel = path.relative_to(PROJECT_ROOT)
    rel_str = str(rel).replace("\\", "/")
    candidates = sorted(
        ((prefix, group) for prefix, group in ORTHOGONAL_GROUPS.items()
         if rel_str == prefix or rel_str.startswith(prefix + "/")),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    return candidates[0][1] if candidates else None


def _extract_imports(source: str) -> list[str]:
    """Return all module names imported in a Python source string."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _module_to_path_prefix(module: str) -> str:
    """Convert a dotted module name to a path prefix. e.g. 'api.auth' → 'api/auth.py'"""
    parts = module.split(".")
    # Try exact file first, then directory
    as_file = "/".join(parts) + ".py"
    as_dir  = "/".join(parts)
    return as_file  # caller checks both


def _is_allowed_violation(importer: Path, imported_prefix: str) -> bool:
    """Return True if this importer/imported pair is in the allowed list."""
    rel = str(importer.relative_to(PROJECT_ROOT)).replace("\\", "/")
    for allowed_importer, allowed_imported, _ in REGISTERED_ARCHITECTURAL_DEBT:
        if rel == allowed_importer or rel.startswith(allowed_importer):
            if imported_prefix.startswith(allowed_imported):
                return True
    return False


def _python_files(directory: Path) -> Iterator[Path]:
    """Yield all .py files under directory, skipping hidden dirs and __pycache__."""
    for p in directory.rglob("*.py"):
        if any(part.startswith(".") or part == "__pycache__" or part == "node_modules"
               for part in p.parts):
            continue
        yield p


# ── Core violation detector ──────────────────────────────────────────────────

def collect_violations() -> list[dict]:
    """Walk all Python files and return a list of layer violation dicts."""
    violations = []

    for py_file in _python_files(PROJECT_ROOT):
        importer_layer = _layer_for(py_file)
        if importer_layer is None:
            continue  # unmapped file — skip (tests, scripts, etc.)

        importer_group = _orthogonal_group(py_file)

        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for module in _extract_imports(source):
            # Resolve module to a path prefix
            prefix_file = _module_to_path_prefix(module)
            prefix_dir  = "/".join(module.split("."))

            # Check both possible forms against the layer map
            imported_layer = None
            matched_prefix = None
            for prefix in (prefix_file, prefix_dir):
                candidates = sorted(
                    ((p, l) for p, l in LAYER_MAP.items()
                     if prefix == p or prefix.startswith(p + "/") or p.startswith(prefix)),
                    key=lambda x: len(x[0]),
                    reverse=True,
                )
                # Pass 07: when the module resolves to a real directory (a
                # package, e.g. bare 'from api import arkadia_engine' → 'api'),
                # an entry INSIDE that package (e.g. 'api/key_pool.py') must
                # not outrank the package's own layer entry ('api') — the
                # import targets the package as a whole, not that submodule.
                # Without this guard the longer file prefix wins by length
                # and the whole package is misclassified (detector blind spot).
                if (PROJECT_ROOT / prefix).is_dir():
                    exact = [c for c in candidates if c[0] == prefix]
                    if exact:
                        candidates = exact
                if candidates:
                    imported_layer = candidates[0][1]
                    matched_prefix = candidates[0][0]
                    break

            if imported_layer is None:
                continue  # stdlib, third-party, or unmapped — not our concern

            # Skip self-layer imports (same layer number, same orthogonal group)
            imported_group = None
            for prefix, group in ORTHOGONAL_GROUPS.items():
                if prefix_file.startswith(prefix) or prefix_dir.startswith(prefix) or prefix.startswith(prefix_dir):
                    imported_group = group
                    break

            # Rule 1: more stable layer may not import from less stable layer.
            # LAYER_MAP numbering: higher number = more stable.
            # Permitted direction: lower-numbered (less stable) → higher-numbered (more stable).
            # Violation: higher-numbered (more stable) → lower-numbered (less stable).
            # e.g. kernel (2) → api (1) is a violation; api (1) → kernel (2) is permitted.
            # See: ADR-015, tests/architecture/LAYER_MAP.py
            if imported_layer < importer_layer:
                if not _is_allowed_violation(py_file, prefix_dir or prefix_file):
                    violations.append({
                        "type": "layer_inversion",
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "importer_layer": importer_layer,
                        "imported_module": module,
                        "imported_layer": imported_layer,
                        "message": (
                            f"Layer {importer_layer} imports from Layer {imported_layer}: "
                            f"'{module}' (violation of ADR-015)"
                        ),
                    })

            # Rule 2: orthogonal layer 3 sub-layers must not import from each other
            elif (importer_layer == 3 and imported_layer == 3
                  and importer_group is not None and imported_group is not None
                  and importer_group != imported_group):
                if not _is_allowed_violation(py_file, prefix_dir or prefix_file):
                    violations.append({
                        "type": "orthogonal_cross",
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "importer_group": importer_group,
                        "imported_module": module,
                        "imported_group": imported_group,
                        "message": (
                            f"Orthogonal layer '{importer_group}' imports from "
                            f"'{imported_group}': '{module}' (violation of ADR-015)"
                        ),
                    })

    return violations


# ── pytest tests ─────────────────────────────────────────────────────────────

def test_no_layer_inversions():
    """
    No Python file in a lower architectural layer may import from a higher layer.
    Violations must be registered in REGISTERED_ARCHITECTURAL_DEBT with a remediation deadline.

    See: ADR-015, docs/phase1/ARCHITECTURE_MAP.md
    """
    violations = [v for v in collect_violations() if v["type"] == "layer_inversion"]
    if violations:
        report = "\n".join(f"  • {v['file']}: {v['message']}" for v in violations)
        raise AssertionError(
            f"\n{len(violations)} layer boundary violation(s) detected:\n{report}\n\n"
            "Fix the import, or register it in REGISTERED_ARCHITECTURAL_DEBT in "
            "tests/architecture/LAYER_MAP.py with owner, workstream, and exit criterion.\n"
            "Read the freeze rule in LAYER_MAP.py before adding an entry."
        )


def test_no_orthogonal_cross_dependencies():
    """
    Orthogonal layer-3 subsystems (knowledge, identity, provider) must not import
    from each other.

    See: ADR-015
    """
    violations = [v for v in collect_violations() if v["type"] == "orthogonal_cross"]
    if violations:
        report = "\n".join(f"  • {v['file']}: {v['message']}" for v in violations)
        raise AssertionError(
            f"\n{len(violations)} orthogonal cross-dependency violation(s):\n{report}"
        )


def test_registered_debt_is_documented():
    """
    Every entry in REGISTERED_ARCHITECTURAL_DEBT must have a non-empty reason string.
    Undocumented debt entries defeat the purpose of the registry.
    """
    undocumented = [
        (importer, imported)
        for importer, imported, reason in REGISTERED_ARCHITECTURAL_DEBT
        if not reason.strip()
    ]
    assert not undocumented, (
        "Every REGISTERED_ARCHITECTURAL_DEBT entry must have a non-empty reason string. "
        f"Missing reasons for: {undocumented}"
    )


def test_registered_debt_references_remediation():
    """
    Every REGISTERED_ARCHITECTURAL_DEBT entry must reference a remediation plan
    (must contain 'Phase', 'Gate', 'Workstream', 'deadline', or 'remediate').
    Debt without a scheduled removal is not a registry — it's an excuse.
    """
    without_deadline = [
        (importer, imported, reason)
        for importer, imported, reason in REGISTERED_ARCHITECTURAL_DEBT
        if not any(kw in reason.lower() for kw in ("phase", "gate", "workstream", "deadline", "remediate", "wip"))
    ]
    assert not without_deadline, (
        "Every REGISTERED_ARCHITECTURAL_DEBT entry must reference a remediation timeline. "
        f"Missing deadline: {[(i, r) for i, _, r in without_deadline]}"
    )


def test_kernel_does_not_import_api_directly():
    """
    Fast-path guard: the kernel/ layer must not import from api/ (except via
    REGISTERED_ARCHITECTURAL_DEBT). This is the single most critical boundary in the
    current codebase — tested separately for clarity of failure messages.

    See: ADR-015, docs/phase1/DEPENDENCY_GRAPH.md
    """
    kernel_dir = PROJECT_ROOT / "kernel"
    if not kernel_dir.exists():
        return  # nothing to check

    unapproved = []
    for py_file in _python_files(kernel_dir):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        for module in _extract_imports(source):
            if module == "api" or module.startswith("api."):
                if not _is_allowed_violation(py_file, "api"):
                    unapproved.append((str(py_file.relative_to(PROJECT_ROOT)), module))

    if unapproved:
        report = "\n".join(f"  • {f}: imports '{m}'" for f, m in unapproved)
        raise AssertionError(
            f"\nkernel/ imports api/ without a REGISTERED_ARCHITECTURAL_DEBT entry:\n{report}\n\n"
            "Fix the import (preferred), or register it in LAYER_MAP.py after reading the freeze rule."
        )


def test_providers_do_not_import_kernel():
    """
    The provider layer must not import from the kernel. Providers are leaf adapters
    — they accept text input and return text output. They must be swappable without
    touching the kernel.

    See: ADR-015
    """
    providers_dir = PROJECT_ROOT / "providers"
    if not providers_dir.exists():
        return

    violations = []
    for py_file in _python_files(providers_dir):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        for module in _extract_imports(source):
            if module == "kernel" or module.startswith("kernel."):
                violations.append((str(py_file.relative_to(PROJECT_ROOT)), module))

    assert not violations, (
        f"providers/ must not import from kernel/:\n"
        + "\n".join(f"  • {f}: imports '{m}'" for f, m in violations)
    )


def test_knowledge_does_not_import_api():
    """
    The knowledge layer must not import from the API surface.
    It is a stable leaf — callers depend on it; it depends on nothing above it.

    See: ADR-015
    """
    knowledge_dir = PROJECT_ROOT / "knowledge"
    if not knowledge_dir.exists():
        return

    violations = []
    for py_file in _python_files(knowledge_dir):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        for module in _extract_imports(source):
            if module == "api" or module.startswith("api.") or \
               module == "kernel" or module.startswith("kernel."):
                violations.append((str(py_file.relative_to(PROJECT_ROOT)), module))

    assert not violations, (
        f"knowledge/ must not import from api/ or kernel/:\n"
        + "\n".join(f"  • {f}: imports '{m}'" for f, m in violations)
    )


def test_no_circular_imports_in_kernel():
    """
    Detect circular imports within the kernel layer by building a directed graph
    and checking for cycles. Circular imports in the kernel cause intermittent
    ImportError on cold starts and make dependency injection impossible.
    """
    kernel_dir = PROJECT_ROOT / "kernel"
    if not kernel_dir.exists():
        return

    # Build adjacency list: kernel module → set of kernel modules it imports
    graph: dict[str, set[str]] = {}
    for py_file in _python_files(kernel_dir):
        rel = str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
        module_name = rel.replace("/", ".").removesuffix(".py")
        graph[module_name] = set()

        source = py_file.read_text(encoding="utf-8", errors="replace")
        for module in _extract_imports(source):
            if module.startswith("kernel.") or module == "kernel":
                graph[module_name].add(module)

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {k: WHITE for k in graph}
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node, [])

    # Filter out cycles registered in the debt registry.
    # A detected cycle matches an allowed entry when the cycle's node sequence
    # (as a tuple) equals the registered cycle tuple.
    allowed_cycle_tuples = {entry[0] for entry in REGISTERED_CIRCULAR_DEBT}
    unregistered = [c for c in cycles if tuple(c) not in allowed_cycle_tuples]

    assert not unregistered, (
        f"{len(unregistered)} unregistered circular import cycle(s) in kernel/:\n"
        + "\n".join(f"  • {' → '.join(c)}" for c in unregistered)
        + "\n\nRegister known cycles in REGISTERED_CIRCULAR_DEBT in LAYER_MAP.py "
        "with owner, workstream, and exit criterion. Read the freeze rule first."
    )


def test_api_main_line_count_within_budget():
    """
    api/main.py must not grow beyond 2600 lines until it is decomposed (Phase 2).
    This is a holding test — it prevents the monolith from growing further while
    decomposition is pending. When Phase 2 decomposition is complete, this test
    is removed and replaced by tests for each extracted module.

    Current size: ~2506 lines. Budget: 2600 (headroom for legitimate additions).
    """
    main_py = PROJECT_ROOT / "api" / "main.py"
    if not main_py.exists():
        return
    line_count = sum(1 for _ in main_py.open(encoding="utf-8", errors="replace"))
    budget = 2600
    assert line_count <= budget, (
        f"api/main.py has grown to {line_count} lines (budget: {budget}). "
        f"This file is pending decomposition in Phase 2. "
        f"Do not add new route handlers or business logic here — "
        f"create a new router module instead."
    )


def test_intent_types_allowed_types_is_not_a_frozenset():
    """
    After Phase 1 Workstream E is complete, ALLOWED_TYPES must no longer be a
    hardcoded frozenset in kernel/intent_types.py. It must read from the plugin
    registry instead.

    This test will FAIL until Workstream E is implemented — that is expected.
    It serves as a CI reminder that the migration is pending.

    Remove this test when ALLOWED_TYPES is removed from intent_types.py.
    """
    intent_types_path = PROJECT_ROOT / "kernel" / "intent_types.py"
    if not intent_types_path.exists():
        return

    source = intent_types_path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    # Look for: ALLOWED_TYPES = frozenset({...})
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ALLOWED_TYPES":
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        if isinstance(func, ast.Name) and func.id == "frozenset":
                            raise AssertionError(
                                "ALLOWED_TYPES is still a hardcoded frozenset in "
                                "kernel/intent_types.py. Phase 1 Workstream E is not yet complete. "
                                "Once the plugin registry is implemented, remove the frozenset "
                                "assignment and this test."
                            )


def test_from_package_import_resolves_package_layer():
    """Pass 07 regression: bare 'from api import <module>' must be classified
    by the api package's own layer (1), not by a longer LAYER_MAP entry inside
    the package (e.g. 'api/key_pool.py' → 3). This was the blind spot that hid
    kernel/agents.py → api.arkadia_engine: '_extract_imports' yields 'api',
    and the old longest-prefix match picked 'api/key_pool.py' over 'api'.
    The proof is allowlist-independent: the kernel/agents debt entry is
    temporarily removed, so only correct classification can surface it.
    """
    saved = list(REGISTERED_ARCHITECTURAL_DEBT)
    try:
        REGISTERED_ARCHITECTURAL_DEBT[:] = [
            e for e in saved if e[0] != "kernel/agents.py"
        ]
        violations = collect_violations()
        kernel_agents = [
            v for v in violations
            if v["file"] == "kernel/agents.py" and v["imported_module"] == "api"
        ]
        assert kernel_agents, (
            "detector must see kernel/agents.py → api (the from-package import "
            "of api.arkadia_engine) once the debt entry is bypassed"
        )
        assert kernel_agents[0]["imported_layer"] == 1
        assert kernel_agents[0]["importer_layer"] == 2
    finally:
        REGISTERED_ARCHITECTURAL_DEBT[:] = saved


# ── Main (for manual runs) ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running architecture fitness checks...\n")
    violations = collect_violations()
    if not violations:
        print("✅ No layer boundary violations detected.")
    else:
        print(f"❌ {len(violations)} violation(s):\n")
        for v in violations:
            print(f"  • {v['file']}: {v['message']}")
    print(f"\nRegistered architectural debt ({len(REGISTERED_ARCHITECTURAL_DEBT)} entries):")
    for importer, imported, reason in REGISTERED_ARCHITECTURAL_DEBT:
        print(f"  ⚠  {importer} → {imported}: {reason}")
    print(f"\nRegistered circular debt ({len(REGISTERED_CIRCULAR_DEBT)} entries):")
    for cycle, reason in REGISTERED_CIRCULAR_DEBT:
        print(f"  ⚠  {' → '.join(cycle)}: {reason}")
