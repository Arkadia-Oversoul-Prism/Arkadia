# Lane 1 — advertised-contract detector completeness (gate-hygiene)

**Branch:** `gate10/lane1-advertised-contract-completeness-01`
**Base:** `main` @ `36f53be2` (`36f53be22d753ffe269f05cbf3fb39212f744207`)
**Lane:** LANE 1 — shell / navigation / design system / integration seam
**Status:** IMPLEMENTED — guard repaired and both negative controls proven; PR open, not merged.

## 1. Bounded objective

Repair `tests/test_console_endpoint_registry_contract.py`'s advertised-contract guard so
that it judges **every** `contract="…"` string a console page advertises, and correct the
six-entry `RECORDED_ADVERTISED_DRIFT` set that those defects had made false.

No feature page is edited. No lane-owned source file is touched. The change is confined to
one Lane-1 test file plus this evidence record.

## 2. Defect A — the detector saw one contract per file (last-wins overwrite)

The pre-repair extractor keyed its result by **file name**:

```python
found = {}
for name, src in sources.items():
    for match in re.finditer(r'contract="([^"]+)"', src):
        found[name] = match.group(1)      # <- overwrite; only the LAST survives
return found
```

A file advertising four contracts therefore contributed exactly one. Measured on
`main` @ `36f53be2`:

| | count |
|---|---|
| advertised `contract=` occurrences in `src/**/*.tsx` | **6** |
| strings the live detector judged | **3** |

`pages/SolSpirePage.tsx` advertises four contracts; the guard judged only its last
(`/solspire/voice/events`) and silently dropped:

- `/solspire/proposals`
- `/solspire/workevents`
- `/solspire/enterprise/workspaces`

Three quarters of that file's advertised surface was outside the guard. An invented
contract written as any but the final `contract=` in a multi-advertising file was
invisible.

**Negative control (Control A).** The pre-repair last-wins body was restored into the real
file and the suite run:

```
E  AssertionError: the first of several contracts in one file was dropped:
                   ['/solspire/voice/events']
E  assert '/api/invented/ghost-contract' in ['/solspire/voice/events']
FAILED tests/test_console_endpoint_registry_contract.py::test_advertised_contract_detector_sees_every_occurrence_in_a_file
1 failed, 19 passed in 1.42s
```

The control detects the defect it claims to detect.

## 3. Defect B — the comparison was decided by the *parameter name*, and the first repair over-corrected

The pre-repair `is_served()` erased `{…}` on the advertised value and compared it against
an **unstripped** served path:

```python
stripped = value[4:] if value.startswith("/api/") else value
return re.sub(r"\{[^}]*\}", "{}", stripped) in normalized_served   # served side NOT normalized
```

The served side was never normalized, so the two forms could not meet for a route whose
parameter is spelled differently:

```
advertised+normalized : /api/lab/engineering/sessions/{}/execute
served (unnormalized) : /api/lab/engineering/sessions/{session_id}/execute
```

Measured:

```
is_served('/api/lab/engineering/sessions/{id}/execute')          = False
is_served('/api/lab/engineering/sessions/{session_id}/execute')  = True
```

So the real defect is that **the parameter name decided the comparison**. The repair is to
erase the parameter name on **both** sides.

### The first repair's second change was wrong and is reverted here

The first repair also dropped the leading `/api/` from the normalized form, on the stated
premise that the app "serves the same surface under both spellings — `/health` *and*
`/api/health`, `/api/version` *and* `/version`". **That premise is false**, measured at
`main` @ `36f53be2` against `api.main.app.openapi()["paths"]` (288 paths):

| measurement | value |
|---|---|
| paths served under **both** `/x` and `/api/x` | **0** |
| `/api/solspire/*` routes | **0** |
| `/solspire/*` routes | **116** |
| `/api/health` served / `/health` served | False / True |
| `/api/version` served / `/version` served | True / False |

`/api` is a real route-group distinction in this app, not a spelling variant, and there is
no prefix-stripping middleware. Dropping it makes the detector accept paths the app does
**not** serve — `/version` and `/knowledge/graph` both normalize to a served route and
would pass. That is a false-negative class the guard did not have before this PR. The
prefix is therefore restored as **significant**, and only the parameter name is erased.

**Negative control (Control B).** The first repair's `_normalized_route` (prefix-stripping)
was restored into the real file and the suite run:

```
E  assert [] == ['/version']
E    Right contains one more item: '/version'
FAILED tests/test_console_endpoint_registry_contract.py::test_advertised_contract_detector_normalizes_only_the_parameter_name
1 failed, 19 passed in 1.22s
```

The control fails on the over-correction and passes on the corrected form, so it pins both
directions of the defect rather than only the original one.

## 4. The recorded set was false, but not for the reason first recorded

Under the corrected normalization the complete advertised inventory at `main` @ `36f53be2`
is five strings, all served:

| advertised string | advertised by | served? |
|---|---|---|
| `/api/lab/engineering/sessions/{id}/execute` | `EngineeringLabPage.tsx`, `WeaverPage.tsx` | **yes** (`{session_id}/execute`) |
| `/solspire/proposals` | `SolSpirePage.tsx` | yes |
| `/solspire/workevents` | `SolSpirePage.tsx` | yes |
| `/solspire/enterprise/workspaces` | `SolSpirePage.tsx` | yes |
| `/solspire/voice/events` | `SolSpirePage.tsx` | yes |

`RECORDED_ADVERTISED_DRIFT` is therefore `set()` — measured, not assumed.

The six entries it previously held were false for **two different reasons**, and the first
repair's evidence doc mis-stated the second:

- **One** (`/api/lab/engineering/sessions/{id}/execute`) is still advertised verbatim at
  `main` and was a **detector false positive** — the parameter-name defect above. This is
  the only entry the normalization repair actually resolves.
- **Five** (`/api/solspire/{workloads,proposals,pulses,voice}` and
  `/api/solspire/projects/{id}/runtime-context`) were advertised at the revision the set
  was recorded against (`a29a9b8f`) but **had already been repaired in source** by
  `68acf89f` (PR #556), which rewrote the `NotYetWired` panels to the real paths
  (`/solspire/proposals`, `/solspire/workevents`, `/solspire/enterprise/workspaces`,
  `/solspire/voice/events`). `git log -S'/api/solspire/proposals' -- web/arkadia_console/src/`
  shows exactly two commits: the scaffold that introduced it (`c081d200`) and the repair
  that removed it (`68acf89f`).

  These five were **stale recorded entries**, not live drift and not normalization
  artifacts. The first repair's doc claimed all six were produced by its two detector
  defects; that is wrong for these five, which no normalization change could have
  affected. The recorded set is a *floor*, so a stale entry does not by itself make the
  guard red — but it does make the doc's attribution false, and a false attribution in an
  evidence record is a defect to correct rather than reconcile.

**Note on measurement depth.** `git log -S` over a shallow clone is not an absence oracle:
this clone began `--depth 1` (`git rev-list --count HEAD` → 1, `a29a9b8f` unresolvable), so
the first attempt to date these literals returned "never present in src history" and that
reading was wrong. After `git fetch --unshallow` (2548 commits) the two-commit history above
is the measured one. A history-wide claim requires a non-shallow clone.

The `_transport_sources()` domain (`.ts` **and** `.tsx`, less the transport module) is used
rather than `_tsx_sources()`: the read carries the endpoint contract regardless of file
extension, so a `contract=` string in a plain `.ts` module would otherwise be invisible.
Measured: no `.ts` file advertises one today, so this widens the domain without changing
the current verdict.

## 5. Verification

| command | result |
|---|---|
| `python -m pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **20 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m pytest tests/test_prism_console_ci_wiring.py tests/test_console_legacy_route_coverage.py tests/test_console_shell_nav_contract.py -q` | **76 passed** |
| full suite (`-q -rEf --continue-on-collection-errors`) | 8 failed, 3454 passed, 1 error — see §6 |

The file restored byte-identically after each control (`diff -q` clean) and the suite
re-run green, so the controls did not leave residue.

## 6. Regression boundary

The guard's own node count moves **18 → 20** (`--collect-only`, measured on both trees):
the two new negative controls. The pre-existing recorded-set node was reworked in place
rather than duplicated, so it is not an addition.

Full-suite baseline on `main` @ `36f53be2` (measured, one pass,
`-q -rEf --continue-on-collection-errors`):

```
8 failed, 3454 passed, 20 skipped, 3 warnings, 1 error in 239.33s
```

Failing/error node set — **9 nodes**, sha256 `c280ddc616fe4f4e9110bf4e…`:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**None of these is in the changed file** (`grep -c endpoint_registry` → 0), so no
baseline failure is attributable to this change and none was repaired. The
`test_engineering_lab_api.py` pair and the `test_autonomy.py` CE-01 collection error are
the recorded, sovereign-owned pre-existing debt described in `AGENTS.md`; they are left
alone.

Branch side, same environment, same invocation:

```
8 failed, 3456 passed, 20 skipped, 3 warnings, 1 error in 235.41s
outcomes fingerprint c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b
ids fingerprint      215e4308371a01f5b0b73f1e2b5dca5bba30f6578f65bb7c8af6eca67bc8b741
```

The outcomes fingerprint is **byte-identical** to the `main` value above — the
failing/error **node set is unchanged**, which is the load-bearing claim. The
`3454 → 3456` passed delta is `+2`, and `--collect-only` measures `18 → 20` on the same
two trees: the delta is exactly the two new negative controls, not new coverage
elsewhere. Derived with `scripts/baseline_fingerprint.py` (the canonical extractor, which
hashes sorted `FAILED`/`ERROR` node ids rather than printed reason text, so the value does
not depend on terminal width).

No console source file, no other lane's file, and no workflow is touched, so the
console-contract CI gate's derived domain is unchanged.

## 7. Scope and authority boundary

- Repaired: `tests/test_console_endpoint_registry_contract.py` (Lane 1 owned).
- Added: this evidence record.
- **Not** touched: `App.tsx` (PR #550), `router.ts` / legacy-route and shell-nav tests
  (PR #562), `AGENT-03`/`AGENT-04` (PR #568), any feature page, any workflow.
- No merge, no deploy, no acceptance claimed. Human merge authority unchanged.

## 8. Remaining uncertainty

The guard bounds *advertised* strings against the served route table. It does not assert
that a `NotYetWired` panel's route is *reachable* by the console at runtime — only that the
backend serves the path the panel names. Runtime reachability of the advertised surfaces
remains a separate, unclaimed question.
