# WEAVER-K15 — Governed Patch Execution + Transaction Orchestration

**PATCH ≠ AUTHORIZATION · K3 is the sole mutation path**

## Module

`weaver/execution.py` — `execute_patch`, `PatchApproval`, `patch_content_hash`

## Flow

ProposedPatch + PassSpec + PatchApproval → preflight gates → `run_transaction` (K3) → K12 verify → terminal status

`run_k3=False` exercises preflight without mutation (tests).
