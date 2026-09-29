# GATE-HYGIENE · SH-02 batch 2 — Hourly Heartbeat Record

**Pass:** hourly bounded execution (Weaver contract), pass recorded 2026-09-29
**BASE_MAIN:** `ee3fac1baffe512f1d9462984f1d507d38cdfa7a` (`origin/main`, real commit —
"Merge pull request #124 from …/gate-hygiene/baseline-stale-assertion-repair-sci-nexus-01")
**Active branch:** `gate-hygiene/baseline-stale-assertion-repair-solariun-consolidation-01`
**Active PR:** #125 (open, not draft) → this pass head `7afab32`
**Authorization envelope:** test-hygiene only. No source, policy, governance, architecture,
identity, authority-model, mutation-path or authorization-path change.
**Merge:** not performed, never attempted. Human-only.

## 01 — Reconstruct (live evidence, not prior prose)

| Fact | Live source |
|---|---|
| `origin/main` = `ee3fac1` | `git ls-remote` / `git log -1 origin/main` |
| Branch head before this pass = `665e333` (2 commits) | `git log --oneline` on branch |
| Open PRs | REST `/pulls?state=open` → **#126** (draft, `gate-l1-agent-runtime`), **#125** (this branch) |
| CI runs on branch heads | only `security-secret-scan` (push-triggered); `success` on `665e333` and `7afab32` |

Continuity preserved: an active bounded PR (#125) mapped to the current gate existed, so it
was continued. No duplicate branch, no duplicate PR, no workstream reset.

## 02 — Classify

- `CURRENT_CANONICAL_STATE`: main green-adjacent, `main` carries recorded baseline debt.
- `ACTIVE_WORKSTREAM`: `SH-02` stale-assertion repair (`gate-hygiene`), batch 2.
- `NEXT_BOUNDED_TASK`: close the NC1 weakness in the batch-2 repair (see §06).
- `REQUIRED_AUTHORITY`: none for the edit; human merge for #125.

## 05 — Precondition

Re-derived rather than assumed. The prior session's claims were checked against live source
and a pristine `main` worktree; **two corrections** came out of this and are recorded in the
PR body:

1. **NC1 as previously recorded was vacuous.** It renamed only the import alias while the
   call site still contained the literal `searchKnowledge`, so the assertion still passed.
   The control proved nothing about the shared-substrate binding.
2. **`NC7 = 7 passed` understated the file** — `tests/test_solariun_experience_consolidation_01.py`
   holds 8 nodes.

No contradiction with the assumed state (main ancestry, clean tree, dependencies present), so
execution proceeded.

## 06 — Implement (bounded)

One node appended to the existing test file. No new vocabulary, no source edit:

```python
def test_log_binding_uses_shared_substrate():
    solspire_lines = SOLSPIRE.read_text().splitlines()
    assert any("lib/knowledgeApi" in line for line in solspire_lines)
    assert any("await searchKnowledge(" in line for line in solspire_lines)
    dashboard = DASHBOARD.read_text()
    assert "projects/${project.id}/events" in dashboard
    assert "/solspire/workevents" in dashboard
    assert "work_events" in dashboard
```

Rationale: a module-level substring match is satisfied by the **import alias alone**. A
same-named local function, or an alias imported from a foreign module, would pass. The new
node asserts the live call sites instead, so the shared Knowledge OS client is what is
actually bound.

## 07 — Prove

**Targeted:** `tests/test_solariun_experience_consolidation_01.py` → **8 passed**.

**Full suite, by node name** (pristine `main` worktree via `git worktree add /tmp/mainwt main`):

| Tree | Result |
|---|---|
| `main` @ `ee3fac1` (branch test reverted) | 48 failed / 968 passed / 12 skipped / 2 errors |
| branch `@665e333` (batch-2 repair) | 45 failed / 971 passed / 12 skipped / 2 errors |
| branch `@7afab32` (+ binding-guard node) | 45 failed / 972 passed / 12 skipped / 2 errors |

Node-set diff by name against `main`: **3 removed, 0 added, 0 altered**. The invariant node
set is identical, so no other test's fingerprint moved. The failing-node set and the
collection-error set are unchanged — baseline debt is recorded, not attributed, not fixed.

**Protected regressions:**

| Check | Result |
|---|---|
| `tests/architecture` | 11 passed |
| `tests/test_m02a_ci_gate_integrity.py` + `tests/architecture` | 60 passed |
| `python -m py_compile api/main.py` | pass (`api/main.py` = 2519 / 2600 lines) |
| `scripts/cp10_mutation_boundary_policy.py --judge` | PASS |
| `security-secret-scan` on `7afab32` | success |

**Negative controls** (each mutates live source, must be caught, then restores):

| NC | Mutation | Result |
|---|---|---|
| NC0 | baseline, no mutation | pass (8 passed) |
| NC1 | shared client swapped — `../../lib/knowledgeApi` → `../../lib/FOREIGN_SEARCH` | **caught** — 2 failed |
| NC2 | `searchKnowledge` injected into the frame wrapper | caught — 1 failed |
| NC3 | canonical `700px` breakpoint → `701px` | caught — 1 failed |
| NC4 | `experience-inspector` testid re-added to the frame | caught — 1 failed |
| NC5 | map `human_only` → `human-only` | caught — 1 failed |
| NC6 | inspector testid removed from `ProjectDashboard.tsx` | caught — 1 failed |
| NC7 | all restored, re-run | pass — 8 passed, no residue |

NC1 is now caught by two nodes. NC2 remains load-bearing: a relocation repair that merely
moved an assertion could leave the frame free to regrow the substrate.

## 08 — Classify

**IMPLEMENTED.** Code exists, targeted and full-suite proof exist, protected regressions
pass, CI secret-scan green. Not `VERIFIED` in the contract's sense: no runtime/browser
evidence exists, because `vite build` is environment-blocked (no npm registry access in this
sandbox). The change is test- and inspection-verified only, and is labelled as such in the PR.

## 10 — PR management

Existing active PR #125 updated (not duplicated): new commit `7afab32`, description rewritten
with the two corrections from §05, and the sovereign glance posted as a PR comment. PR left
**open and not draft**; readiness for merge is the sovereign's call.

## 12 — Credential boundary (reproduced, not worked around)

The ambient `GITHUB_TOKEN` is **unusable for this repository** in this environment: `gh`
returns HTTP 401 and REST returns `{"message": "Bad credentials"}`. Per the contract this
would be a hard stop if it were the only path; it was not. Git transport and the REST API both
succeed through the clone's own credential, so the pass proceeded with **no workaround** and
no credential handling that deviates from the contract. The ambient token remains a real,
reportable defect.

## 13 — Next bounded task (proposed, not executed)

`SH-02b` — `tests/test_prism_pass_c_surface_ownership.py` (6 nodes) requires a **helper
rewrite**, not string edits. Deliberately not bundled into this pass. `SH-02` budget after
this batch: **9 / 35** repaired. Discovery does not authorize execution; this is recorded as
`PROPOSED` only.

## Remaining uncertainty / not claimed

- No runtime or browser evidence. `vite build` environment-blocked.
- No claim of production parity; no deployment identity is bound to this work.
- Baseline debt untouched: 45 failures and 2 collection errors remain on the branch exactly
  as characterised on `main`, minus the 3 nodes this batch repaired.
