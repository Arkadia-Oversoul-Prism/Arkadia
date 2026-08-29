# WEAVER-K8 — Durable Engineering Memory + Continuation

**MEMORY ≠ AUTHORIZATION · HISTORY ≠ AUTHORIZATION**

## Artifact

`data/weaver/continuation/current.json`

## Module

`weaver/continuation.py` — `build_continuation`, `write_continuation`, `load_continuation`, `reconstruct_fresh_session`

## Status

CURRENT | STALE | MISSING | INVALID

Fresh session always: `authorization.state = NONE`, `next_action = awaiting human authorization`
