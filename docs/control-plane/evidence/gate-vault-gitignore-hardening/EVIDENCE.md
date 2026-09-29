# GATE-VAULT — `.gitignore` hardening for the Knowledge OS private vault — EVIDENCE

**Authorization:** this workstream was already *recorded and proposed* on `main` in
`docs/phase1/CONTINUATION_LEDGER.md` ("New bounded finding (recorded, not executed):
`vault/` runtime output is **not gitignored** … Proposal: hygiene-only gitignore
hardening preserving tracked `.gitkeep` + `Templates/`"). This pass executes only that
pre-recorded, hygiene-only bound.

**Base:** `1d4ed0362aae88e2a5c7bfa8db90fb143f065964` (`main`, merge of PR #98).
**Branch:** `gate-vault/gitignore-hardening`.
**Merge / production deploy:** HUMAN ONLY.
**Merge / deploy / self-authorization:** not performed.

---

## 1. Bounded objective

Close the private-vault-into-canon leak: generated Knowledge OS runtime output under
`vault/` is not covered by `.gitignore`, so a routine `git add -A` stages
private-personal-vault material into a commit.

**Completion condition:** a file created at runtime under `vault/` is not stageable,
while **every currently tracked** `vault/` file remains tracked and un-ignored.

**Regression boundary:** zero test-fingerprint change; no tracked file removed.

**Authority boundary:** no merge, no deploy, no authority/identity change, no test edit,
no removal of tracked scaffolding, no scope expansion.

---

## 2. Precondition checks

| Check | Result |
|-------|--------|
| Ancestry / working tree | clean, on `main` `1d4ed03` |
| Protected surfaces | `.gitignore` is hygiene-only; no identity/auth/route/ontology surface |
| `conftest.py` note | the repo **already ships** a test-session vault sandbox (`conftest.py`) — this change is defence-in-depth for the operator path, not a substitute |
| Regression surface | no test references `.gitignore`, `vault/Templates`, or `vault/Index/README.md` (grep: none) |
| Prior art | `CONTINUATION_LEDGER.md` recorded the finding and the exact proposal; un-executed |

### 2.1 Reproduced leak (before)

```
$ git check-ignore -v vault/Ideas/foo.md      -> (no output, exit 1)   NOT IGNORED
$ printf x > vault/Ideas/__canary_test.md && git add -A -n vault/
add 'vault/Ideas/__canary_test.md'            <-- private material IS stageable
```

---

## 3. Change

One file, `.gitignore` (+7 lines), appended after the existing evidence rules:

```gitignore
# Knowledge OS private vault: generated runtime output must never be committed.
# Tracked scaffolding (.gitkeep, Index/README.md, Templates/) is preserved.
vault/**
!vault/**/
!vault/**/.gitkeep
!vault/Index/README.md
!vault/Templates/**
```

`vault/**` ignores everything; the negations re-include directories (`!vault/**/` must
precede the file rules so git descends), then the tracked scaffolding. No tracked file is
newly ignored and no tracked file is removed.

---

## 4. Verification

| Gate | Result |
|------|--------|
| `git ls-files vault/` newly ignored | **0** (all 14 tracked files still tracked, `check-ignore --stdin --no-index` empty) |
| Canary `vault/Ideas/__canary.md` | **ignored** (`.gitignore:68:vault/**`) |
| `git add -A -n vault/` with canary present | **stages nothing** |
| `git status --porcelain` after canary | clean |
| `pytest tests/architecture -q` | **11 passed / 0 failed** |
| Full suite | **49 failed / 887 passed / 12 skipped / 2 errors** |

### 4.1 Baseline comparison

`main` @ `1d4ed03` and this branch share a byte-identical failure fingerprint
(`diff` of the sorted `FAILED`/`ERROR` sets: empty). **Introduced: none. Resolved: none.**
This is a hygiene change with no test-visible behaviour.

---

## 5. Known limitations / unresolved risks

- This limits *accidental* staging via `git add -A`; an operator can still force-add with
  `git add -f`. It is a guardrail, not an authority boundary.
- The 49 remaining suite failures are pre-existing baseline debt — out of scope.
- `vault/Index/README.md` and `vault/Templates/**` remain tracked by explicit negation;
  if the vault layout changes, those negations must be revisited.

---

## 6. Rollback

Revert the merge commit / delete the branch. The change is a single appended
`.gitignore` block; with it reverted the prior (unprotected) state returns exactly.

---

## 7. Exact references

- Base: `1d4ed0362aae88e2a5c7bfa8db90fb143f065964`
- Branch: `gate-vault/gitignore-hardening`
- Prior record: `docs/phase1/CONTINUATION_LEDGER.md`, "New bounded finding (recorded, not executed)"
- Verdict: **VERIFIED**
