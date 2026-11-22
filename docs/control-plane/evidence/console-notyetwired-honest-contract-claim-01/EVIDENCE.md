# Console `NotYetWired` — the shared copy must not call a served contract unwired

**Contract:** ARK-OPS-CONTINUOUS-001 (continuous reconciliation, fail-closed).
**Branch:** `fix/console-notyetwired-honest-contract-claim-01`
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Authority:** none. No merge, no deployment, no production claim. Draft PR only.

## Defect

`web/arkadia_console/src/components/ui.tsx::NotYetWired` is the shared placeholder for
surfaces the console has not built. Its rendered copy read:

```
Surface scaffolded · contract not yet wired
Expected contract: <path>
```

That copy asserts the **backend contract is absent**. But the panel is used in two
different states, and the second one is the majority:

| state | what is missing | copy true? |
|---|---|---|
| contract absent | the backend does not serve the interface at all | yes |
| interface absent | the backend **serves** it; only the console surface is unbuilt, or the mutating act is deliberately not offered | **no** |

Measured at `main` `034d8879`, against the live route table from `api.main:app`
(300 served paths):

```
panels advertising a SERVED contract: 6
   /api/lab/engineering/sessions/{session_id}/transition    components/lab/LabCapabilityDisclosure.tsx
   /solspire/enterprise/workspaces    pages/SolSpirePage.tsx
   /solspire/voice/events             pages/SolSpirePage.tsx
   /solspire/proposals                pages/SolSpirePage.tsx
   /solspire/workevents               pages/SolSpirePage.tsx
   /api/lab/engineering/sessions/{id}/execute    pages/WeaverPage.tsx
```

Six panels told the operator a served contract was "not yet wired". The per-panel
`note` was already accurate in every case — the shared copy was the false part.

This is the class `SHARED-CONTRACTS.md` §3.5 governs ("Honest states … must be distinct
where relevant") and §3.6 ("If the required backend contract or authority is absent,
render a non-interactive, clearly marked blocked state") — the two states were not
distinct, and the shared copy asserted only the first.

## Repair

`components/ui.tsx` — shared copy only. No page-owned content, no endpoint, no route,
no authority behaviour changed:

```
- <p className="cg-eyebrow">Surface scaffolded · contract not yet wired</p>
+ <p className="cg-eyebrow">Surface scaffolded · interface not built</p>
-   Expected contract: <span className="text-azure">{contract}</span>
+   Backend contract: <span className="text-azure">{contract}</span>
```

The component docstring now names both states explicitly, so the next editor sees why
the copy may not assert contract absence.

## Guard

`tests/test_console_endpoint_registry_contract.py` gains
`test_shared_placeholder_does_not_call_a_served_contract_unwired`, plus two module-level
detectors so the controls exercise the same code the live assertion uses:

- `_not_yet_wired_body(source)` — the **rendered** body of the component, sliced from
  `export function NotYetWired` (so the docstring, which legitimately quotes the
  pre-repair wording, is not read as copy) with block and line comments stripped.
- `_served_contract_claimed_absent(ui_source, served_advertised)` — returns the served
  advertised contracts the copy still calls unwired. Returns `[]` when the copy makes no
  such claim **or** when no panel advertises a served contract (nothing is misstated), so
  the guard does not redden a legitimate future state where every advertised contract is
  genuinely unserved.

The verdict assertion runs first so a red tree names the offending contracts. The
controls then prove the detector is not inert:

| control | feeds | expected |
|---|---|---|
| pre-repair copy | synthetic source with the old eyebrow | reported |
| comment quoting the old copy | synthetic source, phrase inside a `/* */` | not reported |
| repaired copy | the live file | not reported |
| no served advertisement | the live file, empty premise | not reported |

## Verification

```
$ python -m pytest -q tests/test_console_endpoint_registry_contract.py
22 passed                      # 21 before; +1 is this guard

$ python -m pytest -q tests/architecture tests/test_console_shell_nav_contract.py \
    tests/test_console_posture_currency.py tests/test_console_posture_currency_ci_wiring.py \
    tests/test_console_legacy_route_coverage.py tests/test_canonical_frontend_routing.py \
    tests/test_prism_console_ci_wiring.py
165 passed

$ cd web/arkadia_console && corepack pnpm build
tsc --noEmit && vite build -> 170 modules transformed, built in 2.41s
```

### Live negative control (the real file, not a fixture)

Reverting only the eyebrow copy in `web/arkadia_console/src/components/ui.tsx`:

```
$ sed -i 's/Surface scaffolded · interface not built/Surface scaffolded · contract not yet wired/' \
    web/arkadia_console/src/components/ui.tsx
$ python -m pytest -q tests/test_console_endpoint_registry_contract.py -k served_contract
E  AssertionError: the shared NotYetWired copy claims a served contract is not yet wired;
   panels advertising a served contract: /api/lab/engineering/sessions/{id}/execute,
   /api/lab/engineering/sessions/{session_id}/transition, /solspire/enterprise/workspaces,
   /solspire/proposals, /solspire/voice/events, /solspire/workevents
1 failed, 21 deselected
```

Restored byte-identically (`cp` from a pre-edit backup) -> `22 passed`. The guard reads
the real component, so it cannot be satisfied by editing only the test.

## Regression

Full suite, same environment, `-q -rEf --continue-on-collection-errors` (the `-rEf` form
is required: `-rf` alone hides `ERROR` lines and yields a subset fingerprint). Compared by
failing/error **node identity**, never by totals — passed counts move with the installed
dependency set.

See `WORKSTREAM_STATE.md` for the measured node-set comparison at this head.

## Scope and non-goals

- No page-owned copy changed; the six `note` strings were already accurate.
- No endpoint, route, surface, auth, or authority behaviour changed.
- The deeper repair — giving the panel an explicit `state` prop so "contract absent" and
  "interface absent" render **differently** — needs a page-owned change in lanes 1–4 and
  is recorded here as proposed work, not performed. The copy fix removes the false claim;
  it does not make the two states visually distinct.

## Changed paths

```
web/arkadia_console/src/components/ui.tsx            (+16/-4)
tests/test_console_endpoint_registry_contract.py     (+~90)
docs/control-plane/evidence/console-notyetwired-honest-contract-claim-01/{EVIDENCE,WORKSTREAM_STATE}.md
```

## Next permitted action

Human review. Merge execution is human-only under GOV-03. No deployment and no
production acceptance is claimed.
