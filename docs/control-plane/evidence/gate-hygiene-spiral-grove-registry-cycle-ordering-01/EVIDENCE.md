# gate-hygiene/spiral-grove-registry-cycle-ordering-01

Bounded repair of two pre-existing `test_spiral_grove_registry.py` failures recorded as
baseline debt in
`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md` §4.4.

Not a Gate-00…13 advance. Baseline-debt workstream only.

## Provenance

| | |
|---|---|
| Base `main` | `73b65bac34056cb4fbc58c486ad5348df4885cab` |
| Head | `5b25ef5c3f3c340676b082e0bc7365cba1a4be2d` |
| Branch | `gate-hygiene/spiral-grove-registry-cycle-ordering-01` |
| PR | #256 |

## Changed paths

- `spiral_grove/registry.py` (+26 / −3)
- `tests/test_spiral_grove_registry.py` (+14 / −3)

`python -m py_compile api/main.py` OK; `api/main.py` untouched (2582 lines, budget 2600).
No `tests/architecture/**`, `LAYER_MAP.py`, ADR or governance file touched.
`scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths → PASS.

## Defect A — cycle detection unreachable under incremental registration

`CapabilityRegistry.__init__` registers capabilities one at a time; `register()` called the
full `_validate_references()` after **each** insertion. A batch cycle spanning two
not-yet-complete capabilities therefore raised `UnknownCapabilityError` from the first
insertion and never reached a cycle check:

```
CapabilityRegistry([cap("cap-a", ["cap-b"]), cap("cap-b", ["cap-a"])])
  -> UnknownCapabilityError("cap-b")     # expected: CapabilityCycleError
```

Repair: `register()` runs a tolerant cycle-only check `_validate_cycles()`, which treats
not-yet-registered prerequisites as leaves; `_validate_references()` keeps the strict
missing-reference pass and then delegates to `_validate_cycles()`.

## Defect B — brittle ordering pin on a diamond

`test_ais_catalog_supports_progressive_creative_workflow` pinned an exact list for a diamond
whose two branches (`cap-ai-prompt-engineering`, `cap-content-systems`) are unordered
siblings over the shared `cap-digital-intelligence` root. It failed on a correct
dependency-first order. Replaced with a set assertion plus the genuinely load-bearing
ordering (shared root precedes both dependents).

## Verification (measured)

| Command | Result |
|---|---|
| `pytest tests/test_spiral_grove_registry.py -q` | 10 passed (was 8 passed / 2 failed) |
| `pytest tests/architecture -q` | 11 passed |
| `python -m py_compile api/main.py` | OK |

Negative controls (all observed):

| Control | Expected | Observed |
|---|---|---|
| batch cycle via constructor | `CapabilityCycleError` | `CapabilityCycleError: cap-a` |
| incremental cycle via `register()` | `CapabilityCycleError` | `CapabilityCycleError: cap-a` |
| self-cycle | `CapabilityCycleError` | `CapabilityCycleError: cap-a` |
| unknown prerequisite at construction | `UnknownCapabilityError` | `UnknownCapabilityError: cap-missing` |
| forward reference then completion | accepted | accepted |
| linear chain order | dependency-first | `['cap-a', 'cap-b']` |

## Regression boundary — node set, not counts

Full suite, `main` `73b65ba` vs head, sorted `FAILED`/`ERROR` node lists:

```
< FAILED tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow
< FAILED tests/test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle
```

Exactly the two target nodes removed; **0 new failures, 0 new errors**. Counts are not the
oracle — `test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository` is
order-dependent under the full suite.

## CI observed on head `5b25ef5c`

| Check | Result |
|---|---|
| `validate` (SG-02-FE.2-V) | success |
| `Full-history secret scan` | success |
| `Vercel Preview Comments` | success |
| `Vercel – arkadia-prism` (commit status) | success |

`Vercel – console` (commit status) reports **failure on this head and identically on
`main` `73b65ba`** — pre-existing baseline debt, not introduced here. This change touches no
frontend or console source. Recorded as a separate proposed workstream, not repaired in this
pass.

## Remaining uncertainty / not in scope

- `test_steward_filter.py` (3), `test_authority_api_enterprise_boundary.py` (1),
  `test_solspire_r*`, and the other §4.4 nodes — separate bounded workstreams.
- `tests/test_autonomy.py` collection ERROR (`weaver.autonomy` module-vs-package collision) —
  untouched, sovereign-reserved.
- `tests/fixtures/baseline_node_set.txt` still lists the two now-passing nodes. Retiring stale
  fixture entries is the separate proposed workstream
  `gate-hygiene/baseline-node-set-reconciliation-02`; deliberately not done here so this pass
  keeps a single bounded change.

## Authority boundary

Read-only measurement, one bounded source+test repair, one PR. No merge, no push to `main`,
no deployment, no production-parity claim. Human authority required to merge.
