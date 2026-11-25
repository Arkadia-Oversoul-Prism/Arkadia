# Weaver reconnaissance — remote URL userinfo redacted at the writer

**Branch:** `security/weaver-recon-remote-userinfo-redaction-01`
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Owner:** unowned gate-hygiene / secret-hygiene slice (no lane owns `weaver/recon.py`)
**Scope:** `weaver/recon.py`, `lab/observatory/git.py`, `tests/test_repository_remote_redaction.py`,
`.github/workflows/lab-security-contract.yml`. No authority surface, no route, no deployment.

## Defect (measured at `034d8879`)

`weaver/recon.py::git_identity()` returned the remote verbatim:

```python
_, remote_url, _ = _run(["git", "remote", "get-url", "origin"], repo_root)
return {"remote": remote_url or None, ...}
```

That value is not a read-model detail. It is **persisted into a tracked repository path**:

```
$ git ls-files data/weaver/context/current.json
data/weaver/context/current.json
$ git log --oneline -- data/weaver/context/current.json | wc -l
19
$ python3 -c "import json;print(json.load(open('data/weaver/context/current.json'))['repository']['remote'])"
https://github.com/Arkadia-Oversoul-Prism/Arkadia.git
```

`weaver/recon.py::write_context_packet()` rewrites that file from
`build_context_packet()` → `git_identity()`. The chain is
`git remote get-url origin` → `git_identity()["remote"]` → `build_context_packet()["repository"]["remote"]`
→ `data/weaver/context/current.json` (tracked) and → `weaver/analysis.py:122`
(`EngineeringAnalysis.repository["remote"]`).

A remote may legally carry credentials in URL userinfo
(`https://user:token@github.com/org/repo.git`), and that is the documented remediation form
used in this repository's own operating notes when a push credential expires. So the ordinary
recovery step — re-point `origin` at a token-bearing URL — followed by an ordinary `weaver`
recon run, writes the token into a file `git add` can publish. The disclosure would then be in
git history, where it cannot be withdrawn by a later edit.

The existing lab read model already refuses this
(`lab/observatory/git.py::_redact_remote_url`, merged earlier with
`tests/test_repository_remote_redaction.py`). The weaver writer — the *persisting* one — did
not, and `grep -rn "get-url" --include=*.py` showed exactly two readers of the raw remote: the
redacted lab one and the unredacted weaver one.

**State of the committed blob:** credential-free. Nothing in history needs rewriting; the
defect is a latent disclosure path, not a past disclosure.

## Repair

1. **One implementation, promoted to public.** `lab/observatory/git.py::_redact_remote_url`
   → `redact_remote_url` (same body, same behaviour). No second copy is introduced:
   `weaver/recon.py` imports it. `weaver → lab` is an established direction
   (`weaver/console_adapter.py` already imports `lab.engineering_lab.sandbox`), and
   `lab/observatory/git.py` depends only on the standard library, so the import adds no
   application dependency to the recon path (measured: `import weaver.recon` 0.05 s,
   `from lab.observatory.git import redact_remote_url` 0.17 s, no cycle).
2. **Redact at the writer.** `git_identity()` now returns the redacted `remote` plus a derived
   `remote_redacted` reading — `bool(remote_url) and remote != remote_url` — so a
   credential-free remote truthfully reports `False` rather than a constant `True` (the same
   convention `lab.observatory.git.repository_state` already uses).
3. **Select the gate on its inputs.** `lab-security-contract.yml` executes
   `tests/test_repository_remote_redaction.py`, and its `paths` filters named
   `lab/observatory/git.py` but not `weaver/recon.py`. A weaver-only commit would therefore
   have changed the guard's subject without executing the guard. `weaver/recon.py` is now in
   both the `pull_request` and `push` filters (kept symmetric).

No behaviour outside the reported remote value changes; no consumer builds a command from
`remote` (`grep -rn '"remote"' weaver/ tests/` → `analysis.py:122` reads it into a report
field; `session_kernel.py` / `continuation.py` use unrelated literals).

## Verification

| Check | Command | Result |
|---|---|---|
| Redaction contract | `pytest tests/test_repository_remote_redaction.py -q` | **18 passed** (was 14) |
| Delta attribution | `--collect-only -q` on the same file | 18 collected → `+4` is exactly the new nodes |
| Live negative control | revert `git_identity` to the raw shape, re-run | **2 failed, 16 passed** (`test_weaver_git_identity_never_exposes_remote_userinfo`, `test_weaver_context_packet_never_persists_remote_userinfo`); restore → **18 passed** |
| Monkeypatched control | `test_negative_control_the_packet_leaks_when_the_redaction_is_disabled` | passes — disabling the redaction at its definition makes the written packet contain the token, so the positive assertion is not vacuous |
| Weaver + lab surface | `pytest tests/test_weaver_context.py tests/test_weaver_k0.py tests/test_lab_repository_surface_contract.py -q` | 32 passed, 1 failed — the failure (`test_registry_declares_the_repository_reading_and_it_is_served`, `ModuleNotFoundError: google`) is **pre-existing**, node 69 of the `main` baseline set |
| CI selection / workflow guards | `pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py tests/test_m02a_ci_gate_integrity.py tests/test_boot_syntax_boundary.py tests/test_repo_hygiene_gitignore.py -q` | **246 passed** |
| Architecture | `pytest tests/architecture -q` | **11 passed** |
| CP10 mutation boundary | `git diff --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | `PASS`, rc 0 |
| Boot syntax | `python -m py_compile weaver/recon.py lab/observatory/git.py` | ok |
| Lane currency | `python scripts/lane_state.py --check` | exit 0 |
| Live recon smoke | `git_identity('.')` / `build_context_packet('.')` | `remote` = the credential-free URL, `remote_redacted` = **False** |

### Regression attribution (node identity, not counts)

| Tree | Result | Failing/error nodes | sha256 |
|---|---|---|---|
| `main` `034d8879` | 85 failed, 3995 passed, 36 skipped, 28 errors | 113 | `2658c0e1f1a1a4637af112a5250b7f0757f3b5d41c8e3e115c88154ad8f873f1` |
| branch head | 85 failed, 3999 passed, 36 skipped, 28 errors | 113 | `2658c0e1f1a1a4637af112a5250b7f0757f3b5d41c8e3e115c88154ad8f873f1` |

`comm -3` on the two sorted node lists is **empty**: zero new failures, zero repaired nodes
claimed. The `+4 passed` is exactly the four new nodes. Both trees were measured in this same
environment (the absolute numbers exceed CI's because this sandbox installs only the core
dependencies; the comparison is valid because it is same-environment).

## Discovered, not repaired (scope boundary)

`data/engineering_lab/agent_events.jsonl` is produced by a test run, is **not tracked**, and is
**not** matched by `.gitignore` (`git check-ignore` → rc 1). A `git add -A` in a hygiene pass
would stage it — the same class as the `data/economic_seams.db*` finding already recorded.
Proposed as a separate bounded change: a `data/engineering_lab/` ignore rule plus a pin in
`tests/test_repo_hygiene_gitignore.py`. Not done here: this branch is the credential repair, and
mixing an unrelated ignore rule into it would make the evidence ambiguous.

Also recorded, not repaired: `data/weaver/context/current.json` is *tracked* while being
generated output. The redaction removes the credential risk whether or not the file is tracked,
so untracking it is a separate question about what the repository should version (it has 19
commits of history and a consumer in `tests/test_weaver_context.py`).

## Disposition

`ELIGIBLE_TO_MERGE` assessment only. Under GOV-03 no agent may merge, enable auto-merge, or
deploy; the PR is opened as a draft and the merge decision is human. A merge is not deployment
verification and is not acceptance.

---

# Branch synchronization — 2026-11-25

## Why

The branch was `CONFLICTING` / `DIRTY` against `main` and could not be reviewed as a
candidate. The security fix was correct and the conflict was not about it.

## What was done

Merge commit `8cb4725f`, parents `d67aec5a` (previous head) and `fd0a4fdc` (`main`).
No source behaviour changed in this commit; it removes the conflict only.

The single conflicted path was `AGENTS.md`, and the conflict was a pure end-of-file
insertion collision — `main` appended the GOV-04 section while this branch appended the
tracked-artifact secret-hygiene lesson. Both are kept: `main`'s text byte-identical, this
branch's section appended after it.

| Check | Result |
|---|---|
| resolved file starts with `origin/main:AGENTS.md` byte-identically | `True` |
| Cyrillic codepoints | `0` |
| `scripts/agents_md_encoding_audit.py` | `inserted=1741 alterations=0 reproduced=True` |
| diff vs `d67aec5a` | 10 files, **411 insertions, 0 deletions** |

`decidable: False` on the audit is the pre-existing `cruft_delta_vs_oracle`, present on
`main` itself; it is not introduced or changed here.

## End-to-end demonstration of the defect

A scratch repository whose `origin` carries URL userinfo, read through the real module:

```
main   (fd0a4fdc)  remote -> https://x-access-token:<REDACTED>@github.com/o/r.git
branch (8cb4725f)  remote -> https://github.com/o/r.git
                   remote_redacted -> True
```

`main` hands the credential to a writer whose output is a **tracked** file. The branch
redacts it and reports the redaction as a reading, so a credential-free remote truthfully
reports `False`.

## Regression attribution (node identity, not counts)

| | `main` `fd0a4fdc` | branch `8cb4725f` |
|---|---|---|
| full suite | 20 failed / 4253 passed / 22 skipped / 1 error | 20 failed / 4257 passed / 22 skipped / 1 error |
| failing + error node set | **21** nodes | **21** nodes |
| set sha256 | `d0249a6799c5556ab07b7da40fcf73bf9d5a44118ee456e9d53c0a188aac87c5` | identical |

`only-on-main` and `only-on-branch` are both empty. The `+4 passed` is exactly the four
redaction nodes (`tests/test_repository_remote_redaction.py` 14 → 18). Both trees measured
in the same environment.

## Targeted verification on the merged tree

`tests/test_repository_remote_redaction.py` **18 passed** (including both negative
controls); combined run of that suite, `test_agents_md_encoding_adjudication.py`,
`tests/architecture` and `test_m02a_ci_gate_integrity.py` → **126 passed, 2 skipped**.

## Unchanged non-claims

- Production was observed at `source_revision = fd0a4fdc`; that is source↔runtime
  consistency for the current revision, not acceptance of this branch, and this branch is
  not deployed.
- The two previously recorded open questions stand unchanged: the untracked-but-unignored
  `data/engineering_lab/agent_events.jsonl`, and whether `data/weaver/context/current.json`
  should remain tracked at all.
- `ELIGIBLE_TO_MERGE` assessment only. Under GOV-03/GOV-04 no agent may merge; the merge
  decision is human. Merge is not deployment verification and is not acceptance.

## CI boundary at the synchronized head — one non-attributable failure

At head `acbef34c`, 15 of 16 check-runs completed `success`, including every gate that
judges this change: `lab-security-contract`, `test`, `validate`, `console-contract`,
`Full-history secret scan`, `boot-syntax`, `posture-currency`, `verdict-step-integrity`,
`provider-routing`.

`bundle-beta-evidence` failed, and it is **not attributable to this branch**:

- Its failing assertion is `statuses: {'beta-02-hausa.json': 'FAILED'}`.
- `beta-beta-02-hausa` failed first with `RUN_FAILED: "external runtime did not return
  usable inference"` and `errors: []` — the live external N-ATLAS provider returned
  nothing usable. The recorded `git_sha` in that payload is `4de30c58`, a fixed bundle
  revision, not the commit under test.
- Re-running the failed jobs turned `beta-beta-02-hausa`, `native-arkadia-golden-workflow`
  and `validate` to `success`, which proves the provider boundary rather than a code
  defect: the same tree passes when the provider answers.
- `bundle-beta-evidence` still read `FAILED` afterwards because it consumed the
  **artifact from the first attempt**; re-running a producing job inside the same run id
  does not refresh the artifact a dependent job downloads. A fresh run is the remedy, not
  a code change.

For contrast, `bundle-beta-evidence` is `success` on `main`-based heads `f2555736`,
`2a9310ab`, `747c60e3`, `1ab40328` and `bc5ce222`, so the job itself is not broken.

Classification: **BLOCKED on a live external provider**, not a regression. It is recorded
here rather than "fixed" by weakening the assertion, which would remove the only check that
the external betas actually produced a usable inference.
