"""Arkadia Engineering Lab — native agent execution substrate (EL-01 → EL-10).

Canonical principle:

    ARKADIA ORCHESTRATES.
    ARKANA INTERFACES.
    WEAVER WORKS.
    SANDBOX EXECUTES.
    EVIDENCE PROVES.
    HUMAN AUTHORITY DECIDES.

This package is the native Arkadia control plane for agentic engineering work.
It gives the Lab hands without granting it authority:

  * EL-01  runtime boundary + foundational contracts  -> ``contracts``, ``sandbox``
  * EL-02  multi-agent orchestration                  -> ``models``, ``runtime``
  * EL-03  native automations                         -> ``automations``
  * EL-04  artifact canvas                            -> ``artifacts``
  * EL-05  Google Tasks / Keep adapters               -> ``adapters``
  * EL-06  Android control plane                      -> ``android``
  * EL-07  voice adapter                              -> ``voice``
  * EL-08  local/open model runtime (gateway)         -> ``gateway``
  * EL-09  agent deployment                           -> ``runtime``
  * EL-10  C09 operational surface                    -> ``runtime``

It reuses canonical Arkadia primitives and creates no second identity,
workspace, mutation, or authority system.
"""

from __future__ import annotations

from .contracts import (
    AUTHORITY_LEVELS,
    CHECKPOINT_STATES,
    FORBIDDEN_OPERATIONS,
    LAB_AUTHORITY_CEILING,
    NON_COLLAPSES,
    BoundaryViolation,
)
from .runtime import CANONICAL_LOOP, BoundedOperation, BoundedTask, EngineeringLabRuntime, get_runtime

SCHEMA_VERSION = "1.0"
SUBSTRATE_ID = "ARKADIA-ENGINEERING-LAB"

__all__ = [
    "AUTHORITY_LEVELS",
    "CHECKPOINT_STATES",
    "FORBIDDEN_OPERATIONS",
    "LAB_AUTHORITY_CEILING",
    "NON_COLLAPSES",
    "BoundaryViolation",
    "CANONICAL_LOOP",
    "BoundedOperation",
    "BoundedTask",
    "EngineeringLabRuntime",
    "get_runtime",
    "SCHEMA_VERSION",
    "SUBSTRATE_ID",
]
