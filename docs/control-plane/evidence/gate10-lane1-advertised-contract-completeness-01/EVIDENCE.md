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

## 3. Defect B — the `/api` strip was applied to one side only

The pre-repair `is_served()` stripped the leading `/api/` from the **advertised** value and
then compared it against **unstripped** served paths:

```python
stripped = value[4:] if value.startswith("/api/") else value
return re.sub(r"\{[^}]*\}", "{}", stripped) in normalized_served   # served side NOT stripped
```

The normalized forms could therefore never meet for a served `/api/…` route:

```
stripped+normalized : /lab/engineering/sessions/{}/execute
served normalized   : /api/lab/engineering/sessions/{}/execute
```

Measured:

```
is_served('/api/lab/engineering/sessions/{id}/execute')          = False
is_served('/api/lab/engineering/sessions/{session_id}/execute')  = True
```

Four of the six recorded "drift" entries were this artifact.

**Negative control (Control B).** The one-sided strip and the unstripped served set were
restored into the real file:

```
E  Left contains one more item: '/api/lab/engineering/sessions/{id}/execute'
FAILED tests/test_console_endpoint_registry_contract.py::test_advertised_contract_strings_are_recorded
FAILED tests/test_console_endpoint_registry_contract.py::test_advertised_contract_detector_normalizes_both_sides
2 failed, 18 passed in 1.33s
```

## 4. The recorded set was entirely false

Under the corrected normalization the complete advertised inventory is:

| advertised string | advertised by | served? |
|---|---|---|
| `/api/lab/engineering/sessions/{id}/execute` | `EngineeringLabPage.tsx`, `WeaverPage.tsx` | **yes** (`{session_id}/execute`) |
| `/solspire/proposals` | `SolSpirePage.tsx` | yes |
| `/solspire/workevents` | `SolSpirePage.tsx` | yes |
| `/solspire/enterprise/workspaces` | `SolSpirePage.tsx` | yes |
| `/solspire/voice/events` | `SolSpirePage.tsx` | yes |

`RECORDED_ADVERTISED_DRIFT` is therefore `set()` — measured, not assumed. Every one of the
six entries it previously held was a detector false positive. A non-empty entry is now a
real drift rather than a convention, and a new invented string fails immediately.

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
| full suite (`-q -rEf --continue-on-collection-errors`) | see §6 |

The file restored byte-identically after each control (`diff -q` clean) and the suite
re-run green, so the controls did not leave residue.

## 6. Regression boundary

The guard's own node count moves 17 → 20 (+3: two negative controls and the reworked
recorded-set node). No console source file, no other lane's file, and no workflow is
touched, so the console-contract CI gate's derived domain is unchanged.

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
