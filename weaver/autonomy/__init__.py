"""
Autonomy package compatibility surface.

The package contains the newer proposal/guard primitives, while older callers
still use the Cycle 9 scheduled-run API. Keep that API explicitly exported here
so Python's package resolution does not hide the legacy sibling module.
"""

from .legacy_runtime import (
    deterministic_stub,
    load_autonomy_config,
    run_scheduled_once,
    validate_autonomy_config,
)

__version__ = "9.0"
__cycle__ = "9"
__status__ = "disabled"

__all__ = [
    "deterministic_stub",
    "load_autonomy_config",
    "run_scheduled_once",
    "validate_autonomy_config",
]
