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

Dependency rule: imports may only point FROM less stable layers TO more stable layers.
i.e., a file in layer N may import from layer N+1 or above (higher number = more stable),
never from layer N-1 or below (lower number = less stable).
Example: api (1) → kernel (2) is permitted. kernel (2) → api (1) is a violation.

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

# ── Architectural Debt Registry ───────────────────────────────────────────────
#
# This registry records known architectural violations that exist in the
# codebase. It does NOT grant permission for them. Every entry represents
# a liability: understood, scheduled for removal, and assigned to a workstream.
#
# Freeze rule: this registry may only be edited in two cases:
#   1. New debt is intentionally introduced — rare; requires ADR justification.
#   2. Existing debt is removed — because the underlying violation has been fixed.
#
# Do not add entries to avoid a failing test. If a test fails due to a new
# violation, the correct response is to fix the import, not to register it here.
# If deferral is genuinely necessary, document the reason in an ADR first.
#
# Format: (importer_prefix, imported_prefix, "description — workstream — exit criterion")
# Remove an entry only after the violation is resolved and the fix is merged.

REGISTERED_ARCHITECTURAL_DEBT: list[tuple[str, str, str]] = [
    # ── Previously documented (Phase 1 analysis) ────────────────────────────
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E

    # Exit criterion: grep -n "from api" kernel/agents.py returns empty
    ("kernel/agents.py",     "api", "kernel→api: generate_verse — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/planner.py returns empty
    ("kernel/planner.py",    "api", "kernel→api: key_manager — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/tools_real.py returns empty
    ("kernel/tools_real.py", "api", "kernel→api: key_manager — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/jobs.py returns empty
    ("kernel/jobs.py",       "api", "kernel→api: firebase_store — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/goals.py returns empty
    ("kernel/goals.py",      "api", "kernel→api: firebase_store — Workstream A, Phase 1 Gate E"),

    # ── Discovered during B0.5 calibration (2026-07-24) ─────────────────────

    # kernel/tts.py imports api.tts_key_manager (Layer 2 → Layer 1).
    # TTS subsystem was added without following architectural governance.
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -n "from api" kernel/tts.py returns empty
    ("kernel/tts.py",        "api", "kernel→api: tts_key_manager — Workstream A, Phase 1 Gate E"),

    # api/nodes.py imports kernel.tools (Layer 3 Identity → Layer 2 Runtime Core).
    # Identity layer must be a leaf — it may not depend on Runtime Core.
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -n "from kernel" api/nodes.py returns empty
    ("api/nodes.py",         "kernel", "identity→runtime: kernel.tools — Workstream A, Phase 1 Gate E"),

    # api/main.py imports solspire.console_router (Layer 1 API → Layer 0 Presentation).
    # API surface must not depend on any presentation layer module.
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -n "solspire" api/main.py returns empty
    ("api/main.py",          "solspire", "api→presentation: solspire.console_router — Workstream A, Phase 1 Gate E"),

    # providers/* import api.provider_key_store / api.key_manager (Layer 3 → Layer 1).
    # Providers are leaf adapters — they must receive keys via injection, not import them.
    # The fix is a KeyProvider interface injected at startup (see ADR-014 Decision 4).
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -rn "from api" providers/ returns empty
    ("providers/",           "api", "provider→api: key_manager/provider_key_store — Workstream A, Phase 1 Gate E"),

    # providers/router.py imports knowledge.db (orthogonal: Provider → Knowledge).
    # Providers must not reach into the Knowledge layer; routing decisions belong
    # in the Runtime Core (kernel/planner.py), not the provider adapter.
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -n "knowledge" providers/router.py returns empty
    ("providers/router.py",  "knowledge", "provider→knowledge: knowledge.db — Workstream A, Phase 1 Gate E"),
]

# ── Circular Import Debt Registry ─────────────────────────────────────────────
#
# Same freeze rule as REGISTERED_ARCHITECTURAL_DEBT above.
# Format: (cycle_as_tuple, "description — workstream — exit criterion")
# A cycle is expressed as the sequence of module names the detector reports,
# starting and ending at the same node.
# Remove an entry only after the cycle is broken and the fix is merged.

REGISTERED_CIRCULAR_DEBT: list[tuple[tuple[str, ...], str]] = [
    # All previously registered kernel circular import cycles have been resolved
    # in source (Checkpoint A, conversational-spine prep) by relocating shared
    # helpers into the lowest appropriate kernel leaf module:
    #   • _summarize moved kernel.execution → kernel.tools
    #   • classify_input (+ private helpers) moved kernel.execution → kernel.intent_types
    # The former execution↔tools, execution↔planner, and execution→planner→tools
    # cycles no longer exist in the import graph. Keep this list empty until a
    # new cycle is genuinely introduced and registered with owner + exit criterion.
]
