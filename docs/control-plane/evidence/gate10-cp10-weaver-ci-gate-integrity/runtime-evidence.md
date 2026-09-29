# Runtime evidence — GATE-10 CI gate integrity

All claims below are copied from live run logs and job/step status, not inferred.

## Weaver MVP2 — before fix

Run `36406537033`, branch `gate10/cp10-weaver-ci-gate-integrity`, event `workflow_dispatch`.

```
1 Set up job                                         -> success
2 Run actions/checkout@v4                            -> success
3 Run actions/setup-python@v5                        -> success
4 Run python -m pip install --upgrade pip            -> success
5 Run python -m pip install -r requirements.txt      -> success
6 Run pytest -q tests/test_weaver_mvp2_05.py ...     -> failure
```

Log, step 6:

```
/home/runner/work/_temp/....sh: line 1: pytest: command not found
##[error]Process completed with exit code 127.
```

`grep -in pytest requirements.txt` -> no match. pytest is not a runtime dependency.

## Weaver MVP2 — after fix

Run `36406687593`, event `pull_request` (trigger added by this pass).

```
4 Run python -m pip install --upgrade pip                                 -> success
5 Run python -m pip install -r requirements.txt                           -> success
6 Run python -m pip install pytest                                        -> success
7 Run python -m pytest -q tests/test_weaver_mvp2_05.py tests/...07.py     -> success
```

Note: this is the first run in the repository's history where this gate executed
a test at all, and the first where it ran on a pull request.

## CP10 (SG-02-FE.2-V) — after fix

Run `36406687605`, event `pull_request`. All 34 steps success:

```
5  Install frontend dependencies              -> success
6  Build Prism                                -> success
9  Install test runner                        -> success
18 Grove contracts                            -> success
19 CP10-A Lab tests                           -> success
20 CP10-B broader backend regression          -> success
23 CP10 API verification                      -> success
28 CP10 browser route verification            -> success
30 CP10 security artifact scan                -> success
31 CP10 mutation boundary                     -> success
33 Upload CP10 evidence                       -> success
34 Enforce CP10 executable gates              -> success
```

## CP10 — persistent failure pattern before fix

`actions/runs?event=pull_request` showed SG-02-FE.2-V failing on
`gate-00-closure-eden-ops-02-recovery`, `feat/eden-ops-02-team-cockpit`,
`aeas-enterprise-evidence-continuity`, `cal10-enterprise-mobile-onboarding`,
`cal-10-enterprise-product-separation`, `cal-10-eden-enterprise-workspace`,
`cal-u1-u4-arcana-density-mobile`. Cross-branch and repeated, so refactor-induced
rather than environmental.

## Local target-test evidence

```
python -m pytest -q tests/test_weaver_mvp2_05.py tests/test_weaver_mvp2_07.py tests/test_m02a_ci_gate_integrity.py
26 passed in 0.10s
```

## Policy guard probes

```
enterprises/enterprise.json                         legit=True  forbid_v3=False
web/public_prism/src/pages/SolSpireExperienceV3.tsx legit=True  forbid_v3=True
vault/Ideas/x.md                                    legit=False forbid_v3=False
unknown/path.txt                                    legit=False forbid_v3=False
```
