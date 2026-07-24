"""
Arkadia Architecture — Layer Map
=================================
Canonical directory-to-layer assignments for the architecture fitness tests.
Update this file whenever a new subsystem or layer is added.

Referenced by: ADR-015, test_layer_boundaries.py

Layer stability order (higher number = more stable = fewer permitted dependencies):
  0 — Presentation  (least stable — depends on everything below)
  1 — API Surface
  2 — Runtime Core
  3 — Knowledge / Identity / Provider  (orthogonal stable leaves)
  4 — Storage Substrate
  5 — Constitution  (most stable — nothing depends on it)

Dependency rule: imports may only point FROM lower layers TO higher layers.
i.e., a file in layer N may import from layer N or lower, never from N+1 or above.

Orthogonal layers (all at level 3) must not import from each other:
  knowledge <-> identity: forbidden
  knowledge <-> provider: forbidden
  identity  <-> provider: forbidden
"""

from pathlib import Path

# Root of the project (two levels up from this file's directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Layer assignments ────────────────────────────────────────────────────────
# Maps a path prefix (relative to PROJECT_ROOT) to its layer number.
# More specific prefixes take priority over less specific ones.

LAYER_MAP: dict[str, int] = {
    # Layer 5 — Constitution
    "docs":                 5,
    ".agents":              5,

    # Layer 4 — Storage Substrate
    "data":                 4,
    "vault":                4,

    # Layer 3 — Knowledge (orthogonal)
    "knowledge":            3,

    # Layer 3 — Identity (orthogonal)
    "api/auth.py":          3,
    "api/nodes.py":         3,
    "api/user_key_store.py": 3,
    "api/firebase_store.py": 3,

    # Layer 3 — Provider (orthogonal)
    "providers":            3,

    # Layer 2 — Runtime Core
    "kernel":               2,

    # Layer 1 — API Surface
    "api":                  1,   # catches all api/* not already assigned above

    # Layer 0 — Presentation
    "web":                  0,
    "bot":                  0,
    "arkadia-android":      0,
    "sonata-android":       0,
    "solspire":             0,
    "app":                  0,
    "static":               0,

    # Orthogonal sub-layer IDs for cross-dependency checks within level 3
    # (used by the test, not the numeric layer assignment above)
}

# Which directories belong to which orthogonal group at layer 3
ORTHOGONAL_GROUPS: dict[str, str] = {
    "knowledge":            "knowledge",
    "api/auth.py":          "identity",
    "api/nodes.py":         "identity",
    "api/user_key_store.py": "identity",
    "api/firebase_store.py": "identity",
    "providers":            "provider",
}

# ── Temporary violations (Phase 1 remediation backlog) ───────────────────────
# Format: (importer_prefix, imported_prefix, "reason — deadline: Phase N")
# Remove an entry only after the violation is resolved.

ALLOWED_VIOLATIONS: list[tuple[str, str, str]] = [
    ("kernel/agents.py",    "api",   "kernel→api: generate_verse — remediate in Phase 1 Workstream A"),
    ("kernel/planner.py",   "api",   "kernel→api: key_manager — remediate in Phase 1 Workstream A"),
    ("kernel/tools_real.py","api",   "kernel→api: key_manager — remediate in Phase 1 Workstream A"),
    ("kernel/jobs.py",      "api",   "kernel→api: firebase_store — remediate in Phase 1 Workstream A"),
    ("kernel/goals.py",     "api",   "kernel→api: firebase_store — remediate in Phase 1 Workstream A"),
]
