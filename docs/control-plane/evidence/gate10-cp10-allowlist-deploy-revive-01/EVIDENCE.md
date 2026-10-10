# GATE-10 · CP10 mutation-boundary allowlist — deploy/ + growth/ admission (revive)

**Branch:** `gate10/cp10-deploy-allowlist-revive-01`
**Base main at authoring:** `17b931b4fe6dd9b27749894dd0d9b1dc9a2e14f5`
**Revised from:** PR #354 (`gate10/cp10-allowlist-deploy-surface-01`, closed unmerged).

## Origin

PR #354 added the `deploy/` admission and passed the CP10 judge 64/64, but was
closed unmerged. The sovereign closure comment directed:

> Preserve this change for a fresh branch/PR composed against current main; do
> not claim the defect is resolved solely from this closure.

This branch is that fresh, current-main composition. It was rebuilt from
`main` rather than resurrecting #354's tree, so the only carried change is the
policy allowlist edit.

## Defect (reproduced on current main)

The CP10 allowlist (`scripts/cp10_mutation_boundary_policy.py::LEGIT`) is subject
to a completeness invariant asserted by `tests/test_m02a_ci_gate_integrity.py`:
**every path in `git ls-files` must be admitted by the policy module.** On main
at `17b931b4` the invariant was red:

- `deploy/n-atlas-server/{Dockerfile,app.py,requirements.txt,README.md}` —
  tracked via PR #352 (merge `a27c6c80`), omitted from the allowlist.
- `growth/voice_of_belonging.py` — tracked via PR #349
  (`15386e7f`, "add governed Voice of Belonging state machine"), omitted.

Measured on `main` @ `17b931b4`:

```
$ python -m pytest tests/test_m02a_ci_gate_integrity.py -q
3 failed, 61 passed
  FAILED test_allowlist_admits_every_tracked_top_level_prefix
  FAILED test_allowlist_covers_every_tracked_surface
  FAILED test_delegated_verdict_admits_every_tracked_surface
```

Enumerating every rejected tracked path (`git ls-files | python
scripts/cp10_mutation_boundary_policy.py --judge`) yields exactly two roots:
`deploy` and `growth`. Both are legitimate tracked repository surfaces, so both
are allowlist omissions — the allowlist, not the commits, is wrong.

## Change

`scripts/cp10_mutation_boundary_policy.py`: two regex additions to `LEGIT`,
each with a comment naming the omission class and its merge provenance.

```
r"|deploy/"
r"|growth/"
```

No other file changed. The gate's teeth are untouched: the `forbid` stage
(constitutional `SolSpireExperienceV3/V2` shells) and the rejection of unknown
roots both still fire.

## Proof

Fixed (branch, `17b931b4` + patch):

```
$ git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)   exit 0

$ python -m pytest tests/test_m02a_ci_gate_integrity.py -q
64 passed
```

Negative controls (the gate still has teeth):

| Input | Expected | Measured |
|---|---|---|
| `unknown-tree/x.py` (unknown root) | reject | exit 1 — "Unexpected path outside legitimate surfaces" |
| `web/public_prism/src/SolSpireExperienceV3.tsx` | reject | exit 1 — "Forbidden V3 dual shell" |
| `web/public_prism/src/SolSpireExperienceV2.tsx` + `v2_diff_adds_function=True` (module API) | reject | rejected; V2 is flag-gated by design (main's code, unchanged) |

Architecture fitness: `python -m pytest tests/architecture -q` → **11 passed**
(the contract's "10/10" does not reproduce; main measures 11).

## Regression boundary

Policy-allowlist only; no runtime, API, boot, or frontend code touched.
`python -m py_compile api/main.py` not required (no boot code). Full-suite delta
recorded below.

## Authorization

Ready for sovereign merge. Does not merge, deploy, or self-authorize.
