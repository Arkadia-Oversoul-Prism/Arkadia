# WORKSTREAM STATE — gate10/merge-set-354-395-composition-01

## Current state (2026-10-10)

- **BASE_MAIN:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
- **main is red on exactly one check-run:** `validate` (`SG-02-FE.2-V`). Failing step:
  `CP10 browser route verification` (`continue-on-error`), surfaced by
  `Enforce CP10 executable gates`. Root cause: `<script src="/firebase-config.js">`
  (`web/public_prism/index.html:16`) with no committed file under
  `web/public_prism/public/`. The 49 other check-runs are `success` or `skipped`.
- **Active workstream:** GATE-10 / gate-hygiene — close the `main`-red CP10 defect.

## This pass (bounded)

- **Task:** record the composition of the recommended merge set **#354 + #395** — the one
  pair no prior composition record carries (#391 = #354/#384; #393 = #388/#390; #394 =
  debt cluster; #395 §4b = #395/#390).
- **Evidence:** EVIDENCE.md in this directory.
- **Result:** clean `git apply --3way` (disjoint files), YAML parses, wired guards
  **10 passed** on the composed tree; both heads' `validate` jobs green in live CI.
- **Change set:** this directory only (2 docs). No product/workflow/test/authority change.

## Merge set (recommendation, sovereign-only)

1. Merge **#354** (`b6eec36b`) — `deploy/` allowlist rule + committed
   `firebase-config.js` + the guard. Head is **9/9 green** incl. `validate`.
2. Merge **#395** (`941a02b3`) — wires the guard into `sg-02-fe-2-v.yml`. Head green.
3. **Close #384** as superseded by #354 (byte-identical files, §#391).
4. Retarget #395's body from "stacked on #384" to "#354" — #384 is the superseded branch
   in #395's ancestry.

Order is free: #354 and #395 share **zero** files.

## Pre-existing / unowned (do not attribute to this pass)

- 15 failing + 1 error full-suite nodes on `main` (`bfcfe592…` fingerprint). Owned by the
  debt cluster (#354/#356/#357/#365/#347) except 1 sovereign-reserved CE-01 error and
  the F-01 node. Not touched here.
- `#354`'s 3 CP10 `deploy/` allowlist nodes — **repaired by #354 itself**.
- §9 of EVIDENCE.md: the `lab`/`backend` enforcement assertions are **constant-true**
  (tee-without-pipefail). Proposed, not executed — repairing reddens `main`.

## Next bounded task (for the next heartbeat)

Reconstruct from live evidence, then either:
- (a) verify a post-merge `SG-02-FE.2-V` run on `main` once #354 (+#395) merge; or
- (b) if unresolved debt remains unowned, pick the smallest such node and bound it.

Do **not** re-run this composition — it is recorded.

## Authority boundary

Evidence-only. No merge, no push to `main`, no authority/mutation path, no `api/main.py`
(2450 lines, unchanged, budget 2600). Human merge required.
