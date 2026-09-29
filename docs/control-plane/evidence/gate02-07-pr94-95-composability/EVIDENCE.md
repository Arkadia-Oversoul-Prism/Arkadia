# PR #94 + PR #95 — Composability & Regression Evidence

**Workstream:** Bounded verification pass (WS-VERIFY-COMPOSE)
**Base:** `main` @ `e9257bf`
**PR #95 head:** `194c765` (`gate02/conftest-vault-sandbox`)
**PR #94 head:** `d3ead27` (`gate07/main-py-line-budget-restore`)
**Status:** VERIFIED (verification pass; no source change)
**Authorization required:** sovereign merge decision on #94 and #95

---

## 1. Objective

Both open PRs are independently VERIFIED against `main`. Neither has been assessed
*for composition*. A test-isolation fix (#95) and a composition-root extraction (#94)
touch the same test harness and the same app boot path, so the sovereign's merge
decision needs to know whether they are order-dependent, conflict-free, and
regression-free **when applied together**.

This pass answers that question with runtime evidence. It makes no source change.

## 2. Method

Applied both heads onto `main` with Git's real merge machinery (not a rebase or a
diff reconstruction), then ran the same evidence commands used for each PR alone:

```
git checkout -B combined origin/main
git merge --no-edit d3ead27     # PR #94: api/main.py line budget
git merge --no-edit 194c765     # PR #95: conftest vault sandbox
python -m py_compile api/main.py api/loop_routes.py
python -m pytest tests/ -q --continue-on-collection-errors
python -m pytest tests/architecture -q
```

Baseline fingerprint was captured from `main` @ `e9257bf` under the same interpreter
(`/tmp/arkvenv`, Python 3.13) before any merge, so all deltas below are
same-environment comparisons.

## 3. Result — merge is conflict-free and order-independent

Both merges applied with **zero conflicts**. The two PRs touch disjoint files except
for `docs/phase1/CONTINUATION_LEDGER.md` (append-only, auto-merged):

| PR | Files changed |
|----|---------------|
| #94 | `api/main.py` (2607 → 2512), `api/loop_routes.py` (new, +123), evidence, ledger |
| #95 | `conftest.py` (new, +1951 bytes), evidence, ledger |

No file was modified by both PRs in a semantically overlapping way, so merge order
does not change the outcome.

## 4. Result — combined regression fingerprint

| Ref | passed | failed | skipped | errors | architecture |
|-----|--------|--------|---------|--------|--------------|
| `main` @ `e9257bf` (base) | 842 | 51 | 12 | 2 | 10 passed / 1 failed |
| PR #94 alone (`d3ead27`) | 843 | 50 | 12 | 2 | 10 / 1 |
| **#94 + #95 combined** | **843** | **50** | **12** | **2** | **10 / 1** |

Set-difference of failing test names, base → combined:

```
- test_api_main_line_count_within_budget      (repaired by PR #94)
(no new failures)
```

**Delta vs baseline: 1 repaired, 0 introduced.** The combined tree reproduces the
PR-#94-alone fingerprint exactly. PR #95 adds no test-visible failure.

`py_compile api/main.py api/loop_routes.py` → OK, applied to the combined tree, per
the P1-A boot-code rule.

## 5. Result — #95 is not optional alongside #94; it is load-bearing

This is the material finding for the merge decision. A prior pass reported the vault
count as stable at 14 under PR #95. That measurement was taken in a working tree that
already held untracked vault output from an earlier unprotected run, i.e. it was
contaminated. Re-measured cleanly:

| Condition | vault files before | after | untracked |
|-----------|--------------------|-------|-----------|
| PR #94 **alone** (no `conftest.py`) | 14 | **48** | 34 leaked |
| #94 + #95 combined (clean tree) | 14 | **14** | 0 |

Reproduction of the leak, PR #94 alone:

```
git checkout --detach d3ead27
python -m pytest tests/test_oracle_spine.py tests/test_isolation.py -q
# 19 passed
git status --porcelain vault | wc -l   ->  34 untracked files
```

`knowledge.vault` resolves `VAULT_ROOT = Path("vault")` relative to cwd, so any suite
run without the root `conftest.py` sandbox writes private-vault-shaped records into the
repository's `vault/` tree. PR #94 touches the composition root and therefore does not
carry the sandbox. The combined tree holds at 14 with 0 untracked, confirming PR #95
neutralises the leak it was written to fix.

**Consequence:** if #94 is merged without #95, `main` acquires a repeating
test-time leak of private-vault-shaped content into a tracked directory. The two
should be merged in the same window, or #95 first.

## 6. Remaining failure — pre-existing, not attributable to either PR

`tests/architecture/test_layer_boundaries.py::test_no_layer_inversions` reports 2
ADR-015 violations, both in `api/nodes.py` (Layer 3) importing Layer 1 modules
`api.ais_profile` and `api.lab_routes`. Present identically at base, PR-#94, PR-#95,
and combined — **baseline debt, not introduced by this work.**

It is **CONTRADICTED** as a next bounded task. A previously recorded pass noted the
fix "collides" with an identity test; that claim was re-verified here and holds:

```
tests/test_ais_w8_canonical_identity.py:31
    assert "router.include_router(_ais_profile_router)" in nodes
```

`api/nodes.py` is in the `identity` orthogonal group (ADR-015 / `LAYER_MAP.py`).
The only fix satisfying the architecture detector — collapsing the `ais_profile`
router mount into the app composition root — is precisely the structure the W8
canonical-identity test asserts must remain in `api/nodes.py`. That test file also
asserted an identity invariant at HEAD of `main` immediately after PR #93 (not just
placed by #93), so `main` is self-inconsistent on this invariant. This is an
identity-boundary conflict: excluded from this pass, no architectural
reinterpretation attempted. See §8.

## 7. Bounded finding — `vault/` runtime output is not gitignored

`git check-ignore vault/Ideas/<any>.md` → not ignored. `.gitignore` covers
`data/api_keys.json`, `data/provider_keys.json`, `data/user_keys/`,
`data/ims_credentials_sealed.json`, `.env`, `.env.local`, but **not `vault/`**.

`vault/` legitimately tracks `.gitkeep` scaffolds and `Templates/*.md`. Any
runtime-generated personal-vault capture therefore appears as untracked content, and a
sweeping `git add -A` would commit private personal-vault material. PR #95 sandboxes
this at *test time*; nothing prevents it at *commit time*.

Recorded, not executed (NO SELF-EXPANSION). Proposed as its own bounded task in §8.

## 8. Proposed next bounded tasks (not executed)

1. **`gitignore` vault hardening** — small, hygiene-only, within envelope.
   Scope: ignore runtime `vault/` content while preserving tracked `.gitkeep` +
   `Templates/`. Exit: `git check-ignore` on a synthetic
   `vault/Ideas/*.md` returns ignored; `git ls-files vault` still lists the
   scaffolds; no tracked file removed. Authority: none beyond normal PR review.
2. **`api/nodes.py` ADR-015 inversion** — **CONTRADICTED**, requires identity-boundary
   authority. Do not execute without a sovereign decision on which of the two
   invariants yields (`LAYER_MAP` freeze rule vs. W8 canonical-identity assert).
   Options for the sovereign: (a) register the inversion as deliberate debt via a
   superseding ADR, (b) amend the W8 assert to accept composition-root mounting,
   (c) exempt the `identity` group from the orthogonal cross-check. Each changes a
   governance/identity surface — sovereign-only.

## 9. Credential & hygiene surface (reconnaissance, no change)

- `data/api_keys.json`, `data/provider_keys.json`, `data/tts_keys.json` →
  **not tracked**. `.env`, `.env.local` → not tracked. No private keys.
- `data/personal_codices/*.json` **is tracked** (6 nodes). Inspected: sovereign-authored
  identity records (`node_key`, `display_name`, `ims_id`, `role`, `soul_function`,
  `name_decode`) — intentional canonical content, not credential material.
- Secret-shaped-string scan across tracked files
  (`AIza...`, `sk-...`, `ghp_...`, `-----BEGIN ... PRIVATE KEY`) → **no matches**
  outside examples/tests.
- `api/nodes.py::_safe_public_profile` returns only
  `username/handle/display_name/bio/avatar_url`; UID is never projected. Good.

## 10. Provenance

- Base `main` `e9257bf`; PR #94 head `d3ead27`; PR #95 head `194c765`.
- Combined merge applied on throwaway branch `combined` (not pushed).
- Interpreter: `/tmp/arkvenv/bin/python` (3.13). Full suite ~101 s.
- Vault counted with `find vault -type f`; leak measured against a tree cleaned to
  14 files / 0 untracked immediately before each run.
