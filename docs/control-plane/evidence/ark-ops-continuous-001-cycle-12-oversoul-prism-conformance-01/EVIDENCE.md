# ARK-OPS-CONTINUOUS-001 — Cycle 12: the Oversoul Prism 144 conformance claims

**Cycle:** 12 · **Date:** 2026-11-24 · **Contract:** `ARK-OPS-CONTINUOUS-001` (rev. 2026-11-22)
**Branch:** `gate-hygiene/oversoul-prism-conformance-01` · **Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`

This cycle performs no merge, no deployment and claims no acceptance. Merge execution is
human-only under GOV-03; `main` is connected to production, so a merge is a release event.

## 1. Reconstructed state

| fact | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:49Z) |
| local `HEAD` at cycle start | `bb19aabd` (identical; working tree clean) |
| production `/api/version` | `200` / 643 B, `source_revision` = `bb19aabd…`, `revision_conflict: false`, `canonical_deployment: one_reconciled_deployment` |
| open PRs | **42**, every one a draft, every one `base: main` |
| previous cycles | 09 (`#717`, Gemini model ladder), 10 (`#718`, Knowledge OS 5xx contract), 11 (`#719`, Sonata unit-test classpath) |

The first `/api/version` probe exceeded the 30 s soft timeout; the retry of the same URL answered
`200` / 643 B in **0.18 s**. Recorded as a Render cold start, not a defect.

Production identity is necessary evidence of source-to-runtime consistency. It is **not** proof
that the application behaves correctly and **not** deployment acceptance.

## 2. The verified gap

`research/oversoul_prism_144/README.md` states what the 9-cell harness checks, including:

> authority-shaped fields are rejected at the transformation boundary

The test that asserts it calls `transform_node` — a name the module never imports:

```console
$ python -m pytest research/oversoul_prism_144/test_substrate.py -q
......
E           NameError: name 'transform_node' is not defined
research/oversoul_prism_144/test_substrate.py:105: NameError
1 failed, 8 passed in 0.15s
```

The call sits inside `try: … except ValueError:`, so the module raised `NameError` instead of
exercising the boundary. **The README's claim rested on an assertion that never ran.** The file is
syntactically valid, so `tests/test_boot_syntax_boundary.py` (the P1-A `compile()` guard) is blind
to it by construction.

Two surfaces in this domain were also executed by **no** workflow, measured before this change:

```console
$ grep -rn "oversoul_prism_144\|research/" .github/workflows/      # before
(no match)
$ grep -rn "validate_oversoul_prism" .github/ tests/              # before
(no match)
```

- `research/oversoul_prism_144/test_substrate.py` — 9 nodes, one of them the broken boundary test.
- `scripts/validate_oversoul_prism_12x12_registry.py` — validates all 144 registry cells
  (`12 functions × 12 layers`, every cell `authority: none`, `execution_implemented: false`).
  It **passes** today (`OK: 12 functions × 12 layers = 144 historical registry cells`, exit `0`);
  nothing kept it passing.

So a documented conformance claim and the registry it rests on held only when a human ran them.

## 3. The repair and the guards

| path | change |
|---|---|
| `research/oversoul_prism_144/test_substrate.py` | import `transform_node` (**one line**) |
| `tests/test_python_global_reference_integrity.py` | **new** guard, 8 nodes — the defect class |
| `tests/test_oversoul_prism_conformance.py` | **new** guard, 5 nodes — the wiring |
| `.github/workflows/oversoul-prism-conformance.yml` | **new** gate: registry validator + conformance harness + its wiring guard |
| `.github/workflows/boot-syntax.yml` | executes the global-reference guard in the existing dependency-free step |

### The class guard is derived, not restated

`tests/test_python_global_reference_integrity.py` states one invariant over the corpus the
repository actually tracks:

> for every tracked `.py` file, every name referenced as a global resolves at module scope or is
> a builtin.

- **Domain** — `git ls-files -z -- '*.py'`: **718** files at this revision, derived at test time.
- **Detector** — `symtable`: module symbols ∪ `dir(builtins)` ∪ the interpreter's implicit module
  names, compared against every `is_global() and is_referenced()` symbol in every nested scope.
  Stdlib only (`ast`, `symtable`, `subprocess`), so it runs in the boot-syntax job, which installs
  no application dependency.
- **Exemptions** — a module that binds globals dynamically (star import, `globals()`/`exec`/`eval`)
  cannot be judged statically; it must be pinned in `DYNAMIC_BINDING_EXEMPT` with a reason.
  **Measured: the set is empty**, so the guard judges all 718 files. A new exemption is a visible
  change, and `test_every_exemption_is_pinned_with_a_reason_and_exists` rejects a stale one.
- **Negative control** — the detector is fed the *verbatim* pre-repair import blocks and must
  report exactly `["transform_node"]`.
- **Positive control** — the same source with the import must report `[]`.

### The wiring guard derives the gate's inputs from the gate

`tests/test_oversoul_prism_conformance.py` requires a workflow to **execute** (not mention) both
surfaces — `echo pytest <file>` tokenises but is not an invocation — and then collects every repo
path the workflow's own commands name and asserts the `paths` filter selects each one. Adding an
input to the workflow without adding it to the filter reddens the guard, and no remembered list is
restated.

## 4. Verification

| command | result |
|---|---|
| `python -m pytest research/oversoul_prism_144/test_substrate.py -q` | **9 passed** (was 1 failed, 8 passed) |
| `python scripts/validate_oversoul_prism_12x12_registry.py` | `OK: … 144 historical registry cells`, exit `0` |
| `python -m pytest tests/test_python_global_reference_integrity.py -q` | **8 passed** |
| `python -m pytest tests/test_oversoul_prism_conformance.py -q` | **5 passed** |
| every workflow-scanning suite (32 files) | **823 passed** |
| gate-integrity bundle + `tests/architecture` | **407 passed** |
| `git diff --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, exit `0` |

### Live negative controls (each applied to the real file, then restored)

| control | observed |
|---|---|
| A — remove the import from `test_substrate.py` | guard: `1 failed, 7 passed` — `assert not ['research/oversoul_prism_144/test_substrate.py: transform_node']`; conformance: `1 failed, 8 passed`. Restored -> **17 passed** (8 + 9) |
| B — make the real workflow step `echo pytest research/oversoul_prism_144/test_substrate.py` | `1 failed, 2 passed, 2 skipped` — `test_a_workflow_executes_the_conformance_harness_and_the_registry_validator` |
| C — drop the guard from the real boot-syntax step | `1 failed, 5 passed, 2 skipped` — `test_a_workflow_executes_this_guard` |
| D — drop `research/**` from the real `paths` filter | `1 failed, 4 passed` — `test_gate_selects_every_input_its_commands_name[oversoul-prism-conformance.yml]`, naming `research/oversoul_prism_144/test_substrate.py` |

Both workflow files were restored byte-identically and verified by `sha256sum -c`
(`oversoul-prism-conformance.yml: OK`, `boot-syntax.yml: OK`).

### CI on this PR — the gates executed, read from the step logs

Head `0d5e98c22e8163538eaa033f328db75f6715bf58`:

| check | conclusion |
|---|---|
| `boot-syntax` | **pass** — step log: `python -m pytest tests/test_boot_syntax_boundary.py tests/test_boot_syntax_ci_wiring.py tests/test_python_global_reference_integrity.py -q` → **`20 passed in 3.87s`** |
| `conformance` (new gate) | **pass** — `OK: 12 functions × 12 layers = 144 historical registry cells`; then **`14 passed in 0.62s`** (9 harness + 5 wiring guard) |
| `console-contract`, `test`, `trigger-coverage`, `verdict-step-integrity`, `posture-currency`, `provider-forensics`, `Full-history secret scan` | **pass** |
| `beta-beta-02-hausa`, `bundle-beta-evidence` | **failure** — external N-ATLAS family. `beta-beta-01-english` **passed in the same run** (`45415081609`), and the failing job's own evidence records `errors = []`, i.e. the request completed and the verdict is a model-output judgement. Recorded as external flakiness, not attributable to this change and **not** a pass |

The two new guards are therefore proven to *execute in CI*, not merely to exist in the tree.

### Full suite, same environment, both trees

`python -m pytest tests/ -q -rEf --continue-on-collection-errors`
(`PYTHONPATH=<repo>/archive/legacy_python`, `pip install -r requirements.txt`):

| | branch | recorded baseline at this SHA |
|---|---|---|
| counts | `19 failed, 4270 passed, 22 skipped, 1 error` in 289.96 s | `19 failed, 4250 passed, 22 skipped, 1 error` |
| failing/error nodes | **20** | **20** |
| outcomes sha256 | `8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` | `8d70e46e…` |
| ids sha256 | `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` | `d6101722…` |

The branch reproduces the recorded baseline fingerprints exactly. A targeted re-run of the same
ten files on a `main` worktree (`/tmp/wt_main` @ `bb19aabd`) yields **19** nodes; the single
difference is
`tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`,
which **passes in isolation on both trees** (`2 passed` each) and is the order-dependent
shared-runtime class this ledger already records. It is not attributable to this change, and this
change touches nothing under `knowledge/`.

`--collect-only`: `main` **4290**, branch **4310** (**+20**), decomposed per file rather than
inferred from the delta — **13** new guard nodes (8 + 5) and **7** the generic workflow-scanning
suites gain from one new pytest workflow
(`ci_gate_trigger_coverage` +3, `ci_suite_collection_continuation` +2, `gate_filter_selection` +1,
`workflow_injection_boundary` +1), all passing.

## 5. Limitations

- The repair is an **import**. It changes no application behaviour, no route, and no deployment
  configuration. `api/main.py` is untouched.
- The guard is **static**. It proves a referenced global resolves at module scope; it does not
  import the module, so a name that resolves but raises on use is outside its domain (that is the
  test suite's job).
- The exemption rule is deliberately conservative: a module containing `globals()`, `exec` or
  `eval` is exempted rather than analysed. The set is empty today, and a pinned exemption is a
  visible change — but a future module that rebinds globals through another route could be
  exempted rather than judged.
- `research/oversoul_prism_144` is a **non-governing research prototype** by its own README. Making
  its harness executable does not promote it: it authorizes nothing, creates no WorkEvent and
  claims no verification.
- A green conformance gate is not deployment acceptance and does not observe the running system.

## 6. Recorded, not repaired (unchanged)

- `scripts/prism_coherence_check.py` — exits 1 with findings, executed by no gate; its scope
  decision (which READMEs count as documented surfaces) is sovereign.
- CE-01 `weaver.autonomy` module-vs-package collision (`tests/test_autonomy.py` collection error);
  FINDING F-01 persistence boundary — both sovereign-reserved.
- `arkadia-console-android/app/build.gradle.kts` still defaults `ORACLE_BASE_URL` to the retired
  host; a second Render service answers on that host at the same revision (ADR-016 drift to
  record, not adopt).
- The 20-node baseline is unchanged: 10 environment-only (`node_modules/typescript` absent in this
  sandbox; CI provisions it), 2 sovereign-reserved, 8 repaired by open PRs `#690`, `#691`, `#693`,
  `#698`, `#700`.

## 7. Next authorized action

Human review of the 42-PR queue. This PR is a draft; an agent marking it ready, merging it,
deploying, or accepting production state is prohibited.

No agent merge, no push to `main`, no deployment, no acceptance.
