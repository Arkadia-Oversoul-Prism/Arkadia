# WEAVER-K7 — Governed Engineering Workbench

Composition API over K6 session conductor. No second write/commit/push path.

## API

`Workbench.start / recon / propose / review_bundle / approve / reject / execute / status`

CLI: `python -m weaver.workbench <command> --objective "..."`

## Invariants

CONTEXT ≠ AUTHORIZATION · PROPOSAL ≠ AUTHORIZATION · PassSpec required for execute
