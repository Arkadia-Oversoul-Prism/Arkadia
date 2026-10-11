# Federation MVP-01 — versioned Agent Card / Passport schema v0.1

**Workstream:** Federation (isolated; issue #433)
**Branch:** `openhands/federation-agent-card-01`
**Base (`main` at read time):** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Authority:** schema + tests only. No merge, deployment, production route, or acceptance is
claimed or performed. Canonical deployment remains the single Render service under ADR-016.

---

## 1. Reconstructed truth before coding

| Fact | Measurement |
|---|---|
| `origin/main` at start | `f390526ab14e122fef358ef9b9e1cd438509463c` (`git fetch origin main`; `git rev-parse origin/main`) |
| Local `HEAD` at start | `f390526ab14e122fef358ef9b9e1cd438509463c` — identical to `origin/main` and to the SHA the issue cites |
| Pre-existing `federation/` tree or package | none — `git ls-files federation` → 0 paths; `grep -rn federation tests/ api/ scripts/` → 0 matches |
| Installed third-party `federation` package | none — `importlib.util.find_spec("federation")` → `None` |
| `pydantic` available | `2.14.0` (already a declared dependency in `requirements.txt`) |

Baseline full-suite fingerprint at `f390526a` (command in §3): **18 failed, 2351 passed,
17 skipped, 1 error**, i.e. **19** failing/error nodes. Recorded so the branch result can be
compared by node identity rather than by counts.

## 2. Conventions the slice had to satisfy (measured, not assumed)

* **Model style.** `alxai/protocol.py` is the closest precedent: a pure-domain package using
  `pydantic` v2 `BaseModel` + `ConfigDict` + `field_validator`. `federation/agent_card.py`
  follows it.
* **CP10 mutation boundary.** `scripts/cp10_mutation_boundary_policy.py` is the single source
  of the allowlist, and `tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
  asserts **every** tracked path is admitted. A new top-level tree that is not enumerated
  reddens the CP10 gate on `main`.
* **Architecture layer map.** `tests/architecture/LAYER_MAP.py` has no entry for `federation/`
  — which is consistent with all nine comparable domain packages (`alxai`, `economic_seams`,
  `research`, `schemas`, `deploy`, `growth`, `opportunity_radar`, `reconciliation`,
  `musical-intention-engine` are all unmapped). Unmapped files are skipped by the detector
  (`collect_violations`: `if importer_layer is None: continue`), and the contract imports only
  stdlib + `pydantic`. **No `LAYER_MAP` edit was made or needed.**

## 3. Commands and measured results

Environment note: the repository's documented full-suite invocation needs `pyyaml` and
`PYTHONPATH=<repo>/archive/legacy_python`, and `--continue-on-collection-errors` to reach the
pre-existing collection error instead of aborting on it.

```bash
# focused
python -m pytest tests/test_federation_agent_card.py -q -rEf
# -> 94 passed

# architecture fitness
python -m pytest tests/architecture/ -q -rEf
# -> 11 passed

# full suite, baseline (main f390526a) and branch
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Run | Result |
|---|---|
| Focused (`tests/test_federation_agent_card.py`) | **94 passed** |
| Architecture (`tests/architecture/`) | **11 passed** |
| Full suite, `main` `f390526a` | 18 failed, 2351 passed, 17 skipped, **1 error** → 19 nodes |
| Full suite, branch | 18 failed, **2449** passed, 17 skipped, **1 error** → 19 nodes |
| Failing/error node set, `comm -3 main branch` | **empty** — identical by node identity |
| Node-set sha256 (outcomes), both trees | `204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` |
| Node-set sha256 (ids only), both trees | `1422ef3215ead13037d1e7e24df6bf77f269ae1d315042a3ae96ce67e7f2998b` |

The passed delta is `+98`, fully attributed by `--collect-only`: **94** from
`tests/test_federation_agent_card.py` (94 tests collected) plus **4** from the new
`federation`-named CP10 admission tests in `tests/test_m02a_ci_gate_integrity.py`
(`-k federation` → 4 collected). The delta is the addition itself, not a side effect.

## 4. What the contract defines

`federation/agent_card.py` — `AgentCard` (schema `federation.agent-card/0.1`):

| Requirement | Field |
|---|---|
| Opaque federation subject id | `subject_id`, `fed:`-prefixed, bounded length, regex-checked |
| Subject kind | `subject_kind` ∈ `agent`, `agent_society`, `partner` |
| Issuer | `issuer` (required, non-empty) |
| Declared operator relationship | `operator_assertion: OperatorAssertion` (attributed, optional) |
| Membership status | `status` ∈ the nine required values |
| Declared vs verified capabilities | `declared_capabilities: [DeclaredCapability]` / `verified_capabilities: [VerifiedCapability]` — **different types** |
| Provenance state | `provenance: [ProvenanceRecord]` ∈ `declared`, `pending`, `verified`, `rejected` |
| Key / endpoint references | `public_keys: [PublicKeyReference]`, `endpoints: [CommunicationEndpoint]` (optional) |
| Issuance / expiry metadata | `issued_at`, `expires_at`, `withdrawn_at` (optional, timezone-aware) |

## 5. The four hard boundaries, and how each is enforced

1. **A declared capability is not a verified capability.** They are different classes with
   disjoint permitted `state` values. `DeclaredCapability` rejects `state="verified"`;
   `VerifiedCapability` rejects `state="declared"` and requires a non-empty `verifier` **and**
   `evidence_ref`. `VerifiedCapability` also rejects `assertion_source="subject"` — a subject
   cannot attest its own capability. Promotion is therefore a *different object*, not a flag flip.
2. **Membership is not personhood, authority, or authorization.** The contract has no field
   named `authority`, `authorization`, `permissions`, or `legal_person`, and a test asserts
   that absence against `AgentCard.model_fields` — so a later slice cannot grant authority by
   writing into a field that already exists.
3. **An operator relationship is not inferred from self-description.** `OperatorAssertion`
   records *who asserted* (`source`) and its provenance. A `subject`-sourced assertion cannot
   be `verified`; a `verified` assertion requires an `evidence_ref` and must come from a party
   other than the subject.
4. **No execution path, no canonical-graph change.** The module has no router, no store, no
   network client, and no signer. Tests assert the module imports only
   `__future__/re/datetime/enum/typing/pydantic` and that no `sqlite3`/`requests`/`httpx`/
   `fastapi`/`jwt`/`cryptography` import appears in it.

## 6. Negative controls (the evidence that the guards are not decoration)

**(a) CP10 gate — live, before the allowlist entry existed.** The new tree was measured
against the gate *before* it was admitted:

```
printf 'federation/agent_card.py\n' | python scripts/cp10_mutation_boundary_policy.py --judge
# -> "Unexpected path outside legitimate surfaces: federation/agent_card.py"   exit=1
```

After the entry, the shipped change set passes (`exit=0`) while the lookalikes
`federation_evil/x.py`, `federations/x.py`, `federation2/agent_card.py`,
`.federation/agent_card.py`, bare `federation`, and `secret-backdoor/bin/x` all still return
`exit=1`. The admission is narrow: it admits the tree and nothing shaped like it.

**(b) Contract guards — 10 live mutations, each must redden the suite.** A temporary driver
removed one guard at a time from `federation/agent_card.py`, ran the focused suite, and
restored the file:

| Mutation (guard removed) | Result |
|---|---|
| `DeclaredCapability` rejects `verified` state | DETECTED (1 failed) |
| `VerifiedCapability` requires `verifier`/`evidence_ref` | DETECTED (1 failed) |
| `ProvenanceRecord` verified-state requires evidence | DETECTED (3 failed) |
| Operator self-description cannot be `verified` | DETECTED (1 failed) |
| Subject-id shape | DETECTED (5 failed) |
| `schema_version` known-value check | DETECTED (1 failed) |
| `expires_at` after `issued_at` | DETECTED (1 failed) |
| Timestamps timezone-aware | DETECTED (1 failed) |
| `extra="forbid"` | DETECTED (1 failed) |
| Endpoint uri scheme | DETECTED (1 failed) |

`all 10 mutations detected`; the module was restored **byte-identical**
(`sha256 3e2e83bc3806cf2075b6d55f68c19f17d537cd9e3af86709e16f46dd201918cd`), and the driver
was deleted — it is not part of the change set.

**(c) Two-sided in-suite controls.** The capability-conflation and operator-inference
detectors are each proven on a **hand-built defective card** (must be reported) *and* a
**correct card** (must stay silent), plus a third test proving the defective shape is
**unrepresentable through the public API**. A detector that is silent on both the defect and
its absence is not a detector.

## 7. Limitations — stated plainly

* **No production route exists.** Nothing serves, persists, or reads an Agent Card. There is
  no `/api/federation/*` handler and no store; this slice is a contract module and its tests.
* **No passport verification exists.** No signature is checked, no key is resolved, no
  endpoint is contacted. `VERIFIED` records *an assertion by a named verifier with an evidence
  reference*; the contract does not and cannot attest that the reference is true.
* **`is_expired()` is a statement about the declared window**, not a judgement about a
  subject's standing.
* **`operator_assertion` is an attributed assertion, never a resolved fact.**
* **The `fed:` id is opaque and unregistered.** No federation registry, allocation authority,
  or uniqueness guarantee exists.
* **No legal effect.** No membership value, subject kind, or card field confers legal
  personhood, authority, authorization, or permission to act.
* The `+98 passed` delta is the new file (94) plus four additive CP10 admission tests; no
  pre-existing test was modified in behaviour.

### CI execution of the new tests (measured, not assumed)

* **No workflow names `federation/**`** (`grep -rn federation .github/workflows/` → 0). A
  future commit touching *only* `federation/**` would therefore not trigger the CP10 gate.
  This change set does trigger it, because it also edits
  `scripts/cp10_mutation_boundary_policy.py` and `tests/test_m02a_ci_gate_integrity.py`, both
  of which are in `sg-02-fe-2-v.yml`'s `pull_request` filter (verified by parsing the
  workflow's `on.pull_request.paths`).
* The new tests **are collected** by that gate's `CP10-B broader backend regression` step
  (`python -m pytest tests/ -q`, which collects `tests/` wholesale). However that step is
  `continue-on-error: true` and the workflow's enforcement step reads
  `steps.<id>.outcome`, which GitHub does not expose inside a `run:` block — a documented,
  pre-existing self-satisfying guard. **The new tests are therefore not CI-enforced in this
  slice**; they are proven locally (§3) and by the mutation controls (§6b). Wiring a
  dedicated `federation/**` trigger is proposed work, not performed here.


## 8. Files changed

| Path | Change |
|---|---|
| `federation/agent_card.py` | new — the versioned contract |
| `federation/__init__.py` | new — explicit public surface of the package |
| `tests/test_federation_agent_card.py` | new — 94 focused tests incl. negative controls |
| `tests/test_m02a_ci_gate_integrity.py` | additive — 4 CP10 admission tests for `federation/` |
| `scripts/cp10_mutation_boundary_policy.py` | one narrow allowlist entry for `federation/` |
| `docs/control-plane/evidence/federation-agent-card-01/EVIDENCE.md` | this note |

## 9. Next permitted action

Human review of the contract. **Persistence and a read-only endpoint may be proposed only
after this contract is reviewed** — and that slice must not convert a declared claim into a
verified one, and must not present a stored card as a verified passport.
