# WEAVER-K0.1 — Deterministic Session Safety + Durable Publication

## Constitutional invariant

> NO EPHEMERAL PROGRESS.  
> A Weaver pass is not complete merely because local execution completed.  
> A pass is complete when its state is verified on `origin/main`.

## Lifecycle

REMOTE PREFLIGHT → RECON → AUTHORIZATION → SCOPE → IMPLEMENT → TEST → DIFF → CHECKPOINT → COMMIT → PUSH → REMOTE VERIFY → HARD STOP

## Defaults

- `push_allowed = true`
- `publication_required = true`
- internal `commit_and_push(..., push=False)` remains the safe primitive
- terminal passes publish unless explicitly forbidden

## Components

- `weaver/pass_spec.py`
- `weaver/session_kernel.py`
- `weaver/agent.py` (PassSpec required)
- `weaver/autonomy/guard.py` (allow-list)
- `weaver/git_ops.py` (commit ≠ push)
- `weaver/recursive.py` (inherits PassSpec)
- checkpoints: `data/weaver/checkpoints/`
