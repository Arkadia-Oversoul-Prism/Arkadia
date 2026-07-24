# Phase 1 — Plugin Registry Specification

**Status:** Design complete. Awaiting approval before implementation.  
**Date:** 2026-07-24  
**Workstream:** E — Plugin Architecture

---

## Problem Statement

`kernel/intent_types.py` contains:

```python
ALLOWED_TYPES: frozenset[str] = frozenset({
    "generate_images",
    "log_transaction",
    "update_open_loops",
    "generate_verse",
    "__plan__",
})
```

Adding a new capability requires:
1. Edit `ALLOWED_TYPES` in `kernel/intent_types.py`
2. Add a new `BaseTool` subclass in `kernel/tools.py` or `kernel/tools_real.py`
3. Register the tool at startup

This is compile-time capability registration. It violates the architectural north star: *the kernel should discover capabilities, not hardcode them.*

Additionally, `select_tool()` routes by `intent.type == tool.name` — a naming constraint that prevents a tool from handling multiple intent types, or intent types that differ from the tool's own name.

---

## Design Goals

1. **Discovery over enumeration** — the kernel discovers what capabilities exist by scanning a registry; it does not maintain a hardcoded list.
2. **Metadata-first** — every capability declares its own contract: id, version, what it handles, its safety level, and its dependencies.
3. **Backward compatible** — existing `BaseTool` subclasses require zero changes. The new registry wraps them.
4. **No new required infrastructure** — plugin discovery is in-process (no filesystem scan, no subprocess, no IPC).
5. **Safety levels** — each plugin declares whether it is `safe` (no side effects), `restricted` (side effects, requires approval), or `sovereign` (system-level, requires Sovereign key).

---

## Plugin Manifest (per capability)

```python
@dataclass
class PluginManifest:
    id: str           # unique, stable identifier — matches tool name for existing tools
    version: str      # semver string, e.g. "1.0.0"
    capability: str   # human description of what this plugin does
    safety_level: Literal["safe", "restricted", "sovereign"]
    handles: set[str] # set of intent.type values this plugin handles (can be > 1)
    dependencies: list[str]  # ids of other plugins this one requires (for ordering)
    requires_approval: bool  # True if the tool requires human confirmation before run
```

**Example — existing ExecuteShellTool:**

```python
PluginManifest(
    id           = "execute_shell",
    version      = "1.0.0",
    capability   = "Run allowlisted shell commands in a sandboxed subprocess",
    safety_level = "restricted",
    handles      = {"execute_shell"},
    dependencies = [],
    requires_approval = True,
)
```

**Example — hypothetical future capability:**

```python
PluginManifest(
    id           = "git_commit",
    version      = "0.1.0",
    capability   = "Commit staged changes to the local git repository",
    safety_level = "sovereign",
    handles      = {"git_commit", "commit_changes"},  # handles multiple intent types
    dependencies = [],
    requires_approval = True,
)
```

---

## Plugin Registry API

```python
# kernel/plugin_registry.py

class PluginRegistry:
    """Replaces ALLOWED_TYPES + TOOL_REGISTRY + select_tool()."""

    def register(self, tool: BaseTool, manifest: PluginManifest) -> None:
        """Register a tool with its manifest. Validates manifest fields."""

    def discover(self) -> list[PluginManifest]:
        """Return all registered manifests, sorted by id."""

    def route(self, intent: dict) -> BaseTool | None:
        """Return the tool that handles intent['type'], or None."""

    def is_allowed(self, intent_type: str) -> bool:
        """True if any registered plugin handles this intent type."""

    def get_manifest(self, plugin_id: str) -> PluginManifest | None:
        """Return manifest for a plugin by id."""

    def list_safe(self) -> list[PluginManifest]:
        """Return manifests with safety_level == 'safe'."""

    def list_by_safety(self, level: str) -> list[PluginManifest]:
        """Return manifests filtered by safety level."""
```

---

## Registration Pattern (backward compatible)

Existing tools register themselves at startup. The only change is that `register_tool()` now also accepts an optional manifest:

```python
# Before (Phase 6 — still works):
register_tool(ExecuteShellTool())

# After (with manifest — preferred):
register_tool(ExecuteShellTool(), manifest=PluginManifest(
    id="execute_shell",
    version="1.0.0",
    ...
))
```

When no manifest is provided, a default manifest is generated from the tool's `name`, `description`, and `requires_approval` attributes — preserving backward compatibility for all existing tools.

---

## How ALLOWED_TYPES Is Replaced

**Before:**

```python
# kernel/execution.py
from kernel.intent_types import ALLOWED_TYPES, normalize

if intent.get("type") not in ALLOWED_TYPES:
    return {"handled": False, ...}
```

**After:**

```python
# kernel/execution.py
from kernel.plugin_registry import get_registry

registry = get_registry()
if not registry.is_allowed(intent.get("type")):
    return {"handled": False, ...}
```

`kernel/intent_types.py` is kept for `normalize()` and `ALLOWED_SOURCES` — but `ALLOWED_TYPES` becomes an alias that reads from the registry at call time (for backward compatibility during transition):

```python
# kernel/intent_types.py (transition period)
def _allowed_types_from_registry() -> frozenset[str]:
    try:
        from kernel.plugin_registry import get_registry
        return frozenset(get_registry().all_handled_types())
    except Exception:
        return frozenset()  # never crash — safe fallback

ALLOWED_TYPES = property(_allowed_types_from_registry)
```

After all callers are migrated, `ALLOWED_TYPES` is removed.

---

## select_tool() Replacement

**Before:**

```python
# kernel/tools.py
def select_tool(intent: dict) -> BaseTool | None:
    return TOOL_REGISTRY.get(intent.get("type"))
```

**After:**

```python
# kernel/plugin_registry.py
def route(self, intent: dict) -> BaseTool | None:
    intent_type = (intent or {}).get("type")
    if not intent_type:
        return None
    return self._handles_index.get(intent_type)  # handles-set lookup, not name match
```

`_handles_index` is built at registration time:
```python
for intent_type in manifest.handles:
    self._handles_index[intent_type] = tool
```

A tool can now handle multiple intent types, and the intent type no longer needs to match the tool's name.

---

## Safety Level Enforcement

The kernel does not enforce safety levels itself — that is the orchestration layer's job. But the registry provides the information needed:

```python
tool = registry.route(intent)
manifest = registry.get_manifest(tool.name)

if manifest.safety_level == "sovereign" and not user_is_sovereign:
    raise PermissionError("Sovereign capability requires elevated access")

if manifest.requires_approval and not approval_granted:
    return {"pending_approval": True, "tool": tool.name, ...}
```

---

## Planner Integration

The LLM planner currently calls `list_tools()` to get tool descriptions for its system prompt. After this change it calls `registry.discover()` instead — manifests include richer metadata (safety level, version, dependencies) that can be included in the planner's context.

Manifests replace the `payload_schema` dict for the planner prompt:
```
• execute_shell [restricted] — Run allowlisted shell commands in a sandboxed subprocess
    input: command: str, timeout: int, workdir: str
```

---

## Dependencies Field (Future Use)

The `dependencies` field is included in the spec but not enforced in Phase 1.
It is reserved for Phase 2, when the kernel gains a plugin dependency resolver that ensures dependent plugins are loaded before their dependents.

---

## File Plan

```
kernel/
  plugin_registry.py       ← new: PluginRegistry, PluginManifest, get_registry()
  tools.py                 ← updated: register_tool() accepts optional manifest
  intent_types.py          ← updated: ALLOWED_TYPES reads from registry (transition)
  execution.py             ← updated: uses registry.is_allowed() and registry.route()

tests/
  test_plugin_registry.py  ← new
    - test_register_and_route
    - test_handles_multiple_intent_types
    - test_default_manifest_from_tool_attrs
    - test_is_allowed_reflects_registry
    - test_safety_level_query
```

---

## Migration Sequence (no big-bang)

1. Add `kernel/plugin_registry.py` (no changes to any existing file)
2. Update `register_tool()` to optionally accept a manifest
3. Update existing tool registrations to include manifests (one at a time, per commit)
4. Update `select_tool()` to delegate to registry (single-line change)
5. Update `execute_intent()` to use `registry.is_allowed()` instead of `ALLOWED_TYPES`
6. After all callers verified: remove `ALLOWED_TYPES` from `intent_types.py`

Each step is independently deployable and independently revertable.

---

*Next document: OBSERVABILITY_DESIGN.md*
