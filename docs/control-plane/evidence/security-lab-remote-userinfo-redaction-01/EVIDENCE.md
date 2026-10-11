# Security repair — a git remote's userinfo must never be surfaced

**Workstream:** 4 (Arkana, Weaver, Engineering Lab) — authorized shared-substrate repair
**Branch:** `security/lab-remote-userinfo-redaction-01`
**Base revision:** `17988afdde8460cfcaf778258bc43aed1fc9d21f` (current `main`, PR #434 merge)
**Authority:** explicit human authorization in the PR #432 comment — "proceed with the
shared-substrate security repair raised in slice 08 … fix the source of truth in
`lab/observatory/git.py` / `lab/service.py` as appropriate so `repository.remote` never
exposes URL userinfo, and make the redaction/security status truthful and narrowly
scoped."
**Scope kept separate from UI-only PR #432**, as the authorization requires.
**No merge, no deployment, no human acceptance.**

---

## 1. Defect (measured, not inferred)

`lab/observatory/git.py::repository_state()` returned `remote` as the **verbatim**
output of `git remote get-url origin`. Git stores a remote URL including any
`user:token@` userinfo, so the value carried whatever credential the environment's
remote was configured with.

Reproduced on a synthetic repository (temp dir, `git remote add origin
https://user:<SYNTHETIC>@github.com/o/r.git`) against the **pre-repair** tree — the
raw value came straight through:

```
$ python3 -c "... repository_state('/tmp/probe-repo') ..."
{
 "branch": "master",
 "head": "eb3f2cd21dbbe72492e08db03eae05ff68134d10",
 "clean": true,
 "remote": "https://user:<SYNTHETIC>@github.com/o/r.git",   <-- userinfo present
 "status": "observed",
 "reason": null
}
```

The value reaches `lab.service.build_overview()`'s `repository.remote`, which is what
`GET /api/lab/overview` returns.

A second consumer served the same unredacted value: `weaver/workbench_web.py:329`
(`/api/repo`) calls the same `repository_state`. The repair at the producer hardens
both.

### The handler's own flag did not cover it

`security.values_redacted: true` read as a blanket assurance, but
`security_observations()` (`lab/observatory/snapshot.py:74`) only classifies *file
paths* that mention credential-ish **names** (`GEMINI_API_KEY`, `AIza`, …) and returns
`"value redacted"` for those paths. It never inspected `repository.remote`. The
response therefore asserted redaction while carrying an unredacted remote.

---

## 2. Repair

### 2.1 Source of truth — `lab/observatory/git.py`

New `redact_remote_url(url) -> RemoteURL(url, redacted)`:

* strips userinfo from an authority component, splitting on the **last** `@` in the
  authority so a password containing `@` is fully removed;
* handles the scp-like shorthand `user@host:path`, which `urlsplit` does not parse;
* returns a credential-free URL unchanged with `redacted=False`;
* **fails closed**: an unparseable form (e.g. `urlsplit` raises `ValueError` on a
  malformed IPv6 host) or an unparsed form still carrying an `@` yields `url=None`
  with `redacted=True` — a credential is never passed through on the assumption it is
  safe.

`repository_state()` now returns `"remote": redacted.url` plus a new
`"remote_redacted": bool`. Because the guarantee is made **once, at the producer**,
no caller has to remember to strip it.

### 2.2 Truthful, narrowly-scoped status — `lab/service.py`

`build_overview()`'s `security` block gains two keys that name exactly what is
redacted, replacing the blanket-reading flag:

```python
"security": {
    "observations": security,
    "values_redacted": True,
    "redaction_scope": "security.observations",   # new — what the flag always covered
    "remote_userinfo_redacted": True,             # new — the remote guarantee, stated
}
```

`repository` also carries `remote_redacted`, so a consumer can render whether the
value was altered **or withheld** without re-deriving it.

---

## 3. Measured behaviour, per URL form

| Input | `redact_remote_url().url` | `redacted` |
|---|---|---|
| `https://user:TOKEN@github.com/o/r.git` | `https://github.com/o/r.git` | `True` |
| `https://TOKEN@github.com/o/r.git` | `https://github.com/o/r.git` | `True` |
| `https://user:p@ss:TOKEN@github.com/o/r.git` | `https://github.com/o/r.git` | `True` |
| `ssh://git@github.com/o/r.git` | `ssh://github.com/o/r.git` | `True` |
| `git@github.com:o/r.git` (scp-like) | `github.com:o/r.git` | `True` |
| `https://user:TOKEN@github.com/o/r.git?x=1#frag` | `https://github.com/o/r.git?x=1#frag` | `True` |
| `https://github.com/o/r.git` | unchanged | `False` |
| `https://github.com:8443/o/r.git` | unchanged | `False` |
| `http://[::1` (unparseable) | `None` (withheld) | `True` |
| `https://user:TOKEN@` (empty authority) | `None` (withheld) | `True` |
| `None` / `""` / non-string | `None` | `False` |

Every fixture uses a **synthetic** literal
(`SYNTHETIC0000TOKEN0000NOTAREALSECRET`). No real credential is read, printed,
written, or persisted. The synthetic repositories are built in a temp directory.

---

## 4. Tests

| File | Nodes | Role |
|---|---|---|
| `tests/test_lab_remote_redaction.py` | 31 | producer + handler conformance over every URL form, plus a negative control |
| `tests/test_lab_remote_redaction_ci_wiring.py` | 14 | the guard executes in a judging step, is selected by every surface it reads, and is dispatchable |

Coverage per the authorization: HTTPS with `user:token` userinfo, bare `token@`,
credential-free URLs, malformed/unsupported forms (withheld, not guessed), and the
credential-free pass-through. Negative control
(`test_negative_control_the_detector_would_flag_an_unredacted_remote`) proves the
assertions can fail rather than passing vacuously.

---

## 5. CI execution — proving it is not a `continue-on-error` broad suite

`sg-02-fe-2-v.yml`'s only broad-suite step (`CP10-B broader backend regression`) is
`continue-on-error: true` and runs a bare `python -m pytest tests/ -q`, which
**aborts** at the CE-01 `weaver.autonomy` collection error (documented in-repo:
`Interrupted: 1 error during collection`). It executes none of the Lab guards.

Repair: a dedicated workflow, `.github/workflows/lab-remote-redaction.yml`, with a
**judging step** (no `continue-on-error`) that runs
`python -m pytest tests/test_lab_remote_redaction.py tests/test_lab_remote_redaction_ci_wiring.py -q`.
The producer uses only the standard library, so the job needs no application
dependency and cannot misreport a dependency gap as a redaction regression.

`tests/test_lab_remote_redaction_ci_wiring.py` holds the invariant generically:

* it **derives** the guard's domain by parsing the guard's imports, never restating
  the list, so a new surface the guard reads is judged by the same rule;
* a `paths` filter missing any surface the guard reads fails;
* `push` and `pull_request` filters must be identical;
* the workflow must be dispatchable;
* an `echo <guard>` or a commented mention is **not** an execution — the command is
  tokenised (`shlex`, comments dropped, line-continuations joined) and `pytest` must
  be the invoked command word with the guard among its arguments.

### Detector proven on the real workflow (mutation testing)

| Mutation to `.github/workflows/lab-remote-redaction.yml` | Result |
|---|---|
| add `continue-on-error: true` to the judging step | **1 failed** — `test_the_executing_step_can_fail_the_job` |
| drop `lab/observatory/**` from the `pull_request` filter only | **3 failed** — domain-selection, filter-symmetry, and the incomplete-filter control |

Both mutations were then reverted and the file verified **byte-identical**
(`cmp` → identical). The detectors bite.

---

## 6. Baseline comparison (same environment, both trees)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Summary | Failing/error node set sha256 | Nodes |
|---|---|---|---|
| `main` `17988afd` (detached worktree) | 20F / 2566P / 19S / 1E | `a56dc1fc1836d1dfce5d05068560bdf83ab6c5155fe8ff8f00e32fd3c2d3441b` | 21 |
| branch (this change) | 20F / 2616P / 19S / 1E | `a56dc1fc1836d1dfce5d05068560bdf83ab6c5155fe8ff8f00e32fd3c2d3441b` | 21 |

`diff` on the sorted node sets is **empty** — no node fixed or broken. The
`+50 passed` is attributed, not inferred:

* **45** = the two new test files' own nodes (`--collect-only` → 31 + 14);
* **5** = the generic workflow-scanning suites gaining passing nodes because a new
  workflow file now exists (`--collect-only`: 141 on `main` → 146 on the branch).

The 21 pre-existing failing/error nodes are unchanged `main` debt; two of them
(`tests/test_engineering_lab_api.py`) were verified present on `main`'s own baseline
node set, so they are not attributable to this branch.

Other checks:

* `python -m py_compile api/main.py` → OK (**2499** lines, within the 2600 budget;
  `api/main.py` is untouched).
* `tests/architecture` → **11 passed**.
* `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths →
  **PASS**.
* Guard node identity: `tests/test_engineering_lab.py`,
  `tests/test_engineering_lab_api.py`, `tests/test_weaver_w1.py`,
  `tests/test_weaver_context.py`, `tests/test_weaver_w2.py` — no new failures
  (2 pre-existing `main` failures in `test_engineering_lab_api.py` only).

---

## 7. Changed paths

| Path | Role |
|---|---|
| `lab/observatory/git.py` | `redact_remote_url()` + `RemoteURL`; `repository_state` returns the redacted value + `remote_redacted` |
| `lab/service.py` | truthful, narrowly-scoped `security` status; `repository.remote_redacted` |
| `tests/test_lab_remote_redaction.py` | producer + handler conformance (31 nodes) |
| `tests/test_lab_remote_redaction_ci_wiring.py` | CI-execution invariant (14 nodes) |
| `.github/workflows/lab-remote-redaction.yml` | dedicated judging gate |
| `docs/control-plane/evidence/security-lab-remote-userinfo-redaction-01/EVIDENCE.md` | this record |

No shared shell/route/endpoint/type registry edited. `api/main.py`,
`api/lab_routes.py`, `lib/endpoints.ts`, `App.tsx`, `lib/router.ts`,
`lib/surfaces.ts` and `lib/types.ts` are untouched.

---

## 8. Interaction with PR #432 (recorded, not reconciled)

PR #432's slice-08 UI boundary redaction (`labOverview.ts::redactRemote()`) remains
correct and is now **defence in depth**: the producer redacts, and the UI redacts
again. PR #432's `test_the_handler_really_does_carry_userinfo_on_the_remote` asserts
an *environment fact* and **skips** with a stated reason when the remote carries no
userinfo — which is now the case after this repair. It degrades to a skip, not a
failure. That file belongs to PR #432's branch; it is not edited here.

---

## 9. Limitations / open items

* **Not deployed.** Production parity and human acceptance are **NOT CLAIMED**.
* The same raw-value pattern exists at `weaver/recon.py:49` (`git_identity` →
  `build_context_packet.repository.remote`) and `weaver/analysis.py:122`, feeding the
  Weaver workbench (`/api/repo` is already hardened by this repair because it calls
  the repaired `lab.observatory.git.repository_state`; the *recon* path is a
  different function). Hardening `weaver/recon.py::git_identity` is a
  **separate bounded change** — not performed here, to keep the authorization's
  scope to `lab/observatory/git.py` / `lab/service.py`. Recorded as proposed work.
* `weaver/workbench_web.py` is not served by the canonical runtime
  (`grep -rn workbench api/main.py` → 0), so its exposure is local-operator only.

---

## 10. Next permitted action

Human review of this PR. On merge, re-fetch `main` and continue Workstream 4's
bounded read-surface work; propose the `weaver/recon.py` hardening as its own
bounded change.
