# Security repair — a git remote's userinfo must never be surfaced (additive delta)

**Workstream:** 4 (Arkana, Weaver, Engineering Lab) — authorized shared-substrate repair
**Branch:** `security/lab-remote-userinfo-redaction-01`
**Base revision:** `7097d6a4c0d847179bb892528f6c89bfbee4a13c` (current `main`, re-measured)
**Authority:** explicit human authorization in the PR #432 comment — "proceed with the
shared-substrate security repair raised in slice 08 … make the redaction/security
status truthful and narrowly scoped."
**No merge, no deployment, no human acceptance.**

---

## 1. Reconciliation: `main` landed the producer fix while this branch was in flight

The pass this record supersedes began from `main` `17988afd` and wrote a producer
redactor. While that work was in flight, `main` **advanced six commits** and landed
its own equivalent repair of the same defect:

| Commit | Date | Change |
|---|---|---|
| `eaea5162` | 2026-10-11T16:15:17+01:00 | `fix(lab): redact repository remote URL userinfo` — `_redact_remote_url()` in `lab/observatory/git.py`, `tests/test_repository_remote_redaction.py`, `.github/workflows/lab-security-contract.yml` |
| `7097d6a4` | 2026-10-11T16:41:09+01:00 | current `main` head |

The branch's first commit (`95b1676a`) therefore conflicted with `main` in
`lab/observatory/git.py`. **Per the Agent Execution Contract §3 ("do not expand scope
to repair adjacent failures") and §4 (compose against a freshly measured baseline),
this branch was rebuilt from current `main` rather than rebased over it** — a rebase
would either duplicate or overwrite reviewed work.

**Measured: `main`'s redactor is sound.** Run against the same edge-case matrix from
the superseded pass, `main`'s `_redact_remote_url` produces the expected output for
every form:

```
https://user:TOKEN@github.com/o/r.git          -> https://github.com/o/r.git
https://TOKEN@github.com/o/r.git               -> https://github.com/o/r.git
https://user:p@ss:TOKEN@github.com/o/r.git     -> https://github.com/o/r.git
ssh://git@github.com/o/r.git                   -> ssh://github.com/o/r.git
git@github.com:o/r.git                         -> github.com:o/r.git
https://user:TOKEN@github.com/o/r.git?x=1#frag -> https://github.com/o/r.git?x=1#frag
https://github.com/o/r.git                     -> https://github.com/o/r.git   (unchanged)
https://github.com:8443/o/r.git                -> https://github.com:8443/o/r.git (unchanged)
```

So the producer (`_redact_remote_url` inside `repository_state()`) is **not
re-proposed here**. This branch carries only what the authorization asked for that
`main` does **not** yet have.

---

## 2. What this branch adds

### 2.1 `repository_state` reports the redaction as a *reading*

`main` returns only the redacted value. A consumer cannot tell whether the value it
receives is the environment's configured remote or a rewritten one.

```python
redacted = _redact_remote_url(remote)
return {
    ...,
    "remote": redacted,
    "remote_redacted": bool(remote) and redacted != remote,   # new
    ...,
}
```

**Derived from the comparison, not a constant** — a credential-free remote truthfully
reports `False`. `main`'s redactor cannot signal this because it returns only the
string.

### 2.2 Truthful, narrowly-scoped security status — `lab/service.py`

`main`'s `build_overview()` still returns
`"security":{"observations":security,"values_redacted":True}`. That flag reads as a
blanket assurance but is set only by `security_observations()`, which classifies *file
paths* mentioning credential-ish names — it has never inspected `repository.remote`.
This branch names the scope and states the remote guarantee separately:

```python
"security": {
    "observations": security,
    "values_redacted": True,
    "redaction_scope": "security.observations",   # new — what the flag always covered
    "remote_userinfo_redacted": True,             # new — the remote guarantee, stated
}
```

`repository` likewise carries `remote_redacted`.

Measured at this branch:

```
repository.remote:            https://github.com/Arkadia-Oversoul-Prism/Arkadia.git
repository.remote_redacted:   True
security:                     True security.observations True
```

### 2.3 Test forms `main` lacks, plus a negative control

`main`'s `tests/test_repository_remote_redaction.py` covers five parametrized forms
and one malformed case. This branch **extends that file** (it does not add a parallel
one) with:

| Added test | What it pins |
|---|---|
| bare `token@` (no colon) | a token-only userinfo is stripped too |
| `p@ss:TOKEN@` (password containing `@`) | the authority splits on the **last** `@` |
| `:8443` port + `?query#fragment` | redaction preserves port, query, fragment |
| `test_repository_state_reports_redaction_only_when_it_happened` | `remote_redacted` is a reading, not a constant — a clean remote reports `False` |
| `test_build_overview_security_status_is_truthful_and_narrowly_scoped` | the scoped status keys |
| `test_build_overview_never_returns_remote_userinfo` | the handler, not just the producer |
| `test_negative_control_the_redaction_reading_can_fail` | the assertions can fail — a raw value is distinguishable from a redacted one |

All fixtures use the **synthetic** literal `synthetic-token`. No real credential is
read, printed, written, or persisted.

---

## 3. CI execution

`main`'s `.github/workflows/lab-security-contract.yml` already runs
`tests/test_repository_remote_redaction.py` in a **judging** step (no
`continue-on-error`), is `workflow_dispatch`-able, and path-filters on
`lab/observatory/git.py`, `lab/service.py`, `api/lab_routes.py` and itself. Verified by
reading the file: every run step has `continue-on-error: None`.

Because this branch **extends the file that workflow already executes**, the added
nodes are executed by an existing judging gate — no new workflow is needed, and none
was added.

**Runtime proof, not a source claim.** Run `38153892202` (`Lab Security Contract`,
`event=pull_request`, `conclusion=success`) step *Execute remote-redaction contract*
logged:

```
python -m pytest -q tests/test_repository_remote_redaction.py
14 passed in 2.81s
```

`14` is this branch's extended node count (main's 7 + the 7 added here), so the added
nodes demonstrably ran in a step with no `continue-on-error`. (The superseded pass added a parallel
`.github/workflows/lab-remote-redaction.yml`; it was **removed** here as a duplicate of
`main`'s gate.)

---

## 4. Baseline comparison (same environment, both trees)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Summary | Failing/error node set sha256 | Nodes |
|---|---|---|---|
| `main` `7097d6a4` (detached worktree) | 19F / 2614P / 17S / 1E | `6cd8bea1f7a4387f716e766a22704954b8bafd363396e95b12a0b02b80fc5dac` | 20 |
| branch (this change) | 19F / 2621P / 17S / 1E | `6cd8bea1f7a4387f716e766a22704954b8bafd363396e95b12a0b02b80fc5dac` | 20 |

`diff` on the sorted node sets is **empty** — no node fixed, none broken. The
`+7 passed` is exactly this branch's added nodes (`--collect-only` on the extended
file: **7 → 14**).

Other checks:

* `python -m py_compile api/main.py` → OK (**2505** lines, within the 2600 budget;
  `api/main.py` is untouched by this branch).
* `tests/architecture` → **11 passed**.
* `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths →
  **PASS**.
* `tests/test_m02a_ci_gate_integrity.py` → **68 passed**.

### Pre-existing `main` failure (not attributable to this branch)

`tests/test_ci_gate_trigger_coverage.py::test_push_and_pull_request_filters_are_identical[openapi-security-metadata.yml]`
fails **identically on `main` `7097d6a4`** and on this branch (measured: `1 failed, 74
passed` on `main`; the same node on the branch). `.github/workflows/openapi-security-metadata.yml`
originates in `main`'s own commit series, not here. Reported, not repaired —
repairing it is that workflow owner's scope.

---

## 5. Changed paths

| Path | Role |
|---|---|
| `lab/observatory/git.py` | `repository_state()` reports `remote_redacted` as a derived reading |
| `lab/service.py` | truthful, narrowly-scoped `security` status; `repository.remote_redacted` |
| `tests/test_repository_remote_redaction.py` | extended with the missing forms + negative control |

No new workflow, no new test file, no shared shell/route/endpoint/type registry edited.
`api/main.py`, `api/lab_routes.py`, `lib/endpoints.ts`, `App.tsx`, `lib/router.ts`,
`lib/surfaces.ts`, `lib/types.ts` untouched.

---

## 6. Limitations / open items (recorded, not repaired)

* **Not deployed.** Production parity and acceptance **NOT CLAIMED**.
* **`weaver/recon.py::git_identity` still leaks the raw remote** — measured on current
  `main`: `git_identity('.')["remote"]` returns a URL carrying userinfo. It flows to
  `weaver/analysis.py:122` (`EngineeringAnalysis.repository.remote`) via
  `build_context_packet`, which `weaver/workbench_view.py:206` invokes inside
  `run_read_only_pipeline`. The Weaver workbench is **not** served by the canonical
  runtime (`grep -rn workbench api/main.py` → 0), so its exposure is local-operator
  only. Hardening `weaver/` is a **separate bounded change** outside this
  authorization's named scope (`lab/observatory/git.py` / `lab/service.py`); recorded
  as proposed work, not performed.
* The superseded pass's evidence and its parallel workflow/test files were removed in
  this rebuild; their measurements are superseded by `main`'s landed fix plus the
  results above.

---

## 7. Next permitted action

Human review of this PR. On merge, re-fetch `main` and either continue Workstream 4's
bounded read-surface work or take up the recorded `weaver/recon.py` hardening as its
own bounded change.
