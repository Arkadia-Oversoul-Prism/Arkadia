# GATE-10 · CP10 allowlist omission — `research/` and `schemas/`

Bounded workstream: `gate10/cp10-allowlist-research-schemas-01`
Branch base: `main` @ `4550531e1912e46d231a45f27ca801810def699d`
Classification: **IMPLEMENTED** (repository evidence complete; merge is human authority)

## 1. Defect (measured, not inferred)

`scripts/cp10_mutation_boundary_policy.py` (`LEGIT`) omitted two trees that `main`
tracks. The policy module's own invariant — asserted by
`tests/test_m02a_ci_gate_integrity.py` against the live `git ls-files` corpus — is:

> every path in `git ls-files` must be admitted by the policy module.

On `main` @ `4550531` that invariant is false for **18** tracked paths:

| tree | paths | introduced by |
|---|---|---|
| `research/` | 17 | PRs #277–#290 (Oversoul Prism corpus) |
| `schemas/` | 1 | PR #286 `ARCH-01: define Arkana Signal Fabric v1` |

The count was 16 when this pass began (base `ebe09a6`, `research/` = 15). `main`
advanced mid-pass to `4550531` (#289 merge + #290), which added
`research/oversoul_prism_review_completion/{README.md,probe.py}` — both under the
already-admitted `research/` prefix, so the repair absorbed them without change.
No new top-level tree appeared (`diff <(git ls-tree ebe09a6) <(git ls-tree 4550531)`
is empty).

Measured on `4550531` with the repair stashed:

```
$ git ls-tree -r --name-only 4550531 | python -c "<LEGIT filter>"
offenders: 18
  research/oversoul_prism_3x3/README.md
  research/oversoul_prism_3x3/topology.json
  research/oversoul_prism_3x3/validate.py
  research/oversoul_prism_acceptance/{README.md,probe.py}
  research/oversoul_prism_conflict/{README.md,probe.py}
  research/oversoul_prism_convergence/{README.md,probe.py}
  research/oversoul_prism_node_transform/{README.md,probe.py}
  research/oversoul_prism_resolution/{README.md,probe.py}
  research/oversoul_prism_review_completion/{README.md,probe.py}
  research/oversoul_prism_verification/{README.md,probe.py}
  schemas/arkana/signal/1.0/arkana-signal.schema.json
```

17 of the 18 offenders sit under `research/`; the 18th is
`schemas/arkana/signal/1.0/arkana-signal.schema.json`.

### Why it did not redden CI at merge time

`sg-02-fe-2-v.yml` is **path-filtered** (`web/public_prism/**`, `spiral_grove/**`,
`lab/**`, `api/lab_routes.py`, named test files, and the boundary's own contract
surfaces). A PR that touches none of those paths never executes the boundary, so
`research/` and `schemas/` were tracked without ever being judged. This is the
recurring omission class recorded in `AGENTS.md` (`GATE-10`) — the allowlist is an
inventory of what the repository tracks, not a filter.

### Consequence (the failure mode, with a negative control)

The gate does not fail on a *missing* path; it fails on the **next ordinary commit
that touches the tree**. The policy rejects the first unadmitted path in the change
set, so a legitimate frontend change is reddened by an unrelated file:

```
$ printf '%s\n' "web/public_prism/src/App.tsx" \
                 "research/oversoul_prism_3x3/validate.py" | python scripts/cp10_mutation_boundary_policy.py --judge
Unexpected path outside legitimate surfaces: research/oversoul_prism_3x3/validate.py
RC=1
```

The mixed change set contains a fully admitted product path and is rejected anyway.
Before this repair, *any* commit touching `research/` or `schemas/` turned the
canonical branch red.

## 2. Change

Two files, both already trigger paths of the gate it repairs:

- `scripts/cp10_mutation_boundary_policy.py` — enumerate `research/` and `schemas/`
  in `LEGIT`, with the omission provenance and the measured offender count recorded
  in place.
- `tests/test_m02a_ci_gate_integrity.py` — per-surface admission tests, a
  shipped-changeset test carrying the exact rejected change set, and **negative
  controls** proving the admission is not overbroad.

## 3. Proof

### 3.1 Positive — the invariant now holds

```
$ git ls-files | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
RC=0
```

```
tests/test_m02a_ci_gate_integrity.py    60 passed   (was 3 failed / 52 passed)
tests/architecture                      11 passed
```

### 3.2 Negative controls — the gate is not weakened

| control | result |
|---|---|
| unknown root `secret-backdoor/bin/x` | rejected, RC=1 |
| prefix lookalikes `research_evil/x.py`, `schemas_evil/x.json`, `schema/x.json`, `research2/x.py`, `researches/x.py` | rejected |
| constitutional `SolSpireExperienceV3.tsx` | rejected — `Forbidden V3 dual shell` |
| mixed changeset (admitted + previously-offending path) | now RC=0 |

`FORBID_V3`/`FORBID_V2` and the unknown-root rejection are untouched. Breadth was
added to the admit-list only; the boundary's teeth are the denylist stage and the
rejection of unknown roots.

### 3.3 Full-suite node-set delta (the load-bearing comparison)

Both runs are the full suite on the same tree, with the repair stashed for the
baseline run so the comparison is same-environment and same-base:

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| base | failing/error nodes | outcomes fingerprint |
|---|---|---|
| `ebe09a6` before (repair stashed) | 18 (17 failed, 1 error) | `c3c319f0161456ec9b4de7fae9ac4103296f69c376479c2e282a7de4f667b3ce` |
| `ebe09a6` after | 15 (14 failed, 1 error) | `093938e8aa68086d838772a048564f44239643da7122401f697aa201573c4ce8` |
| `4550531` before (repair stashed) | 16 (15 failed, 1 error) | `b3adfbc018854a8bbfcafbda9ba981f8f49f0a6e25a12b19b5bba8eea5267319` |
| `4550531` after | *(measured on the rebased branch; see PR check-runs)* | — |

Node-set delta at `ebe09a6` — attributed by **node identity**, never by counts:

```
FIXED   (3)
  tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix
  tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface
  tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface

NEW     (0)
unchanged 15
```

`tests/architecture` is **10/11** on `4550531` (was 11/11 on `ebe09a6`) — not a
regression in this workstream. The new failure is
`test_api_main_line_count_within_budget`, caused by `main` advancing: `api/main.py`
is **2805** lines on `4550531` against a 2600 budget. See §7.

### 3.4 Boot code untouched

`api/main.py` is not in the change set. `python -m py_compile api/main.py` → OK.
`main` @ `4550531` carries **2805** lines, already over the 2600 budget before this
pass; this pass neither grows nor repairs it (§7).

## 4. Remaining uncertainty

- The unchanged failure nodes are pre-existing main debt, unchanged in identity.
  They are **not** repaired here: baseline debt is a separate bounded workstream and
  repairing it inside an architectural gate is out of scope.
- `tests/fixtures/baseline_node_set.txt` records a 10-node set while live `main`
  measures 16 (`4550531`) / 18 (`ebe09a6`). The recorded fixture has drifted from live
  evidence. Reconciling it is a **separate** bounded workstream; this pass does not
  rewrite the fixture, because doing so would mix a fixture reconciliation into a
  boundary repair and make the delta unattributable.
- `AGENTS.md` carries `decidable=False` in `scripts/agents_md_encoding_audit.py`
  (Cyrillic 0, round-trip holds, but the oracle relation is not decidable on this
  shallow clone). It is under an insertion-only constraint and was **not** edited.
- The task prompt's "D-07-5 CI claim" is **not addressable**: the token `D-07-5`
  (and any `D-NN-N` deliverable identifier) appears **nowhere** in the repository —
  `grep -rn "D-07-5" .` → 0 matches; `grep -rhoE "\bD-[0-9]{2}(-[0-9]+)?\b" research/ docs/`
  → 0 matches. Classified **UNKNOWN** / non-reproducible citation. This pass therefore
  measured the live CI state directly instead (§6).

## 5. Authority boundary

Branch `gate10/cp10-allowlist-research-schemas-01` → commit → push → pull request.
No merge. Human sovereign authority is required to merge.

## 6. CI state (live, measured — the "D-07-5 CI claim" replaced by evidence)

`D-07-5` is not in the repository (§4), so no CI claim can be verified *about* it.
The live CI state was measured directly instead.

The change set touches **both** trigger paths of the SG-02 boundary
(`scripts/cp10_mutation_boundary_policy.py`, `tests/test_m02a_ci_gate_integrity.py`,
both explicitly listed in `sg-02-fe-2-v.yml`), so this PR is judged by the boundary it
repairs. `security-secret-scan.yml` runs on every `pull_request` (no path filter).

Measured on the merged PR #289:

| revision | check-runs | conclusions |
|---|---|---|
| merge `3b713ce` | 4 | `Full-history secret scan` success · `browser` success · `validate` success · `weaver_evolution` skipped |
| head `106f93e` | 2 | `Full-history secret scan` success · `validate` success |

`weaver_evolution` is `skipped` (the Genesis Agent workflow is not triggered by this
change). Vercel reported **deployment failure** on both projects with
`api-deployments-free-per-day` (more than 100 deployments in 24h) — a provider rate
limit, not a build defect. **Deployment identity is therefore `BLOCKED` on provider
quota**, and no production-parity claim is made anywhere in this document.

## 7. `api/main.py` budget breach on `main` (found, not caused, not repaired)

`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
**fails on `main` @ `4550531`**:

```
$ git show 4550531:api/main.py | wc -l
2805          # budget: 2600
```

This is pre-existing debt introduced before this pass (PRs #289/#290 grew the file).
It is recorded, **not repaired**: shrinking boot code is a consequential change to the
production boot path and is out of scope for a boundary-allowlist repair. It belongs
to a separate bounded workstream.

## 8. PR #289 (`ARK-01` Signal Gate 01) — independent validation vs the frozen contract

PR #289 is **merged** (`3b713ce`, 2026-10-05T00:10:36Z, `merged: true`), so its changes
are now `main` state. Validated against the frozen contract from #286
(`schemas/arkana/signal/1.0/arkana-signal.schema.json`).

### 8.1 What is correct

- Route shape is as described: `POST /api/arkana/signal/ingest` (`api/main.py:1082`)
  and `POST /api/arkana/signal/respond` (`api/main.py:1219`).
- Raw bytes are hashed server-side (`hashlib.sha256(raw_bytes)`) — the client-supplied
  `sha256` is retained separately as `raw.client_sha256` rather than trusted.
- Envelope structure, required keys, `provenance.derived_from`,
  `integrity.raw_preserved`, and the `interpretation_is_derived` const all conform.
- Raw audio is preserved client-side (`client://indexeddb/arkana-signal/<id>`) and the
  contract's separation of raw evidence from derived interpretation is honoured in the
  object shape.

### 8.2 Two contract violations (measured with `jsonschema` 4.26.0)

The prompt asks the model for JSON with `responseMimeType: application/json`, but the
model output is placed into the envelope **without normalisation**. Both violations
are reachable from ordinary model output:

| # | trigger | schema path | message |
|---|---|---|---|
| 1 | model returns candidates without `status` (e.g. `{"value":"play_loop"}`) | `interpretation.references[0]` (and `intent_candidates[*]`) | `'status' is a required property` |
| 2 | model returns `null` for `transcript_confidence` | `interpretation.confidence.transcript` | `None is not of type 'number'` |

The contract's `$defs.candidate` **requires** `status` and its enum is
`["candidate","unknown","resolved","uncertain_derived_signal"]` — it is the mechanism
by which "keep uncertainty explicit" is enforced. The route copies the model's list
verbatim (`"intent_candidates": derived.get("intent_candidates") or []`), so a model
that returns bare values yields a **non-conforming `arkana.signal` object** on the
very route whose purpose is to emit canonical signal objects.

Violation 2 is sharper than a type error: the schema deliberately declares
`confidence` as `["number","null"]` at the *candidate* level, so a conforming producer
must express "unknown confidence" by omitting the key or using a candidate `status` —
not by emitting `null` into the `number`-only `interpretation.confidence` map. The
route emits `{"transcript": None}` whenever the model reports no confidence, which is
the normal case for uncertain audio.

Verified conforming cases (negative controls on my own harness): the happy path and
the "model omits `intent_candidates` entirely" case both validate, so the harness is
not failing everything.

### 8.3 No producer-side schema enforcement exists

`grep -rn "arkana-signal.schema.json\|arkana/signal/1.0" tests/ scripts/ api/` returns
**0** producer/consumer references. The only two hits in the repository are the CP10
allowlist entry and its admission test in this change set — i.e. the frozen contract is
referenced only as a *path to be admitted to the mutation boundary*, never as a
*validation constraint*. Nothing pins the implementation to the contract it was built
against, which is why §8.2 could ship.

### 8.4 Disposition

Classification: **CONTRADICTED** — repository evidence (the emitted object) conflicts
with the frozen contract for ordinary model output. **Not repaired here**: it is a
consequential change to a merged, production-boot-path route, it needs a bounded
workstream with its own tests (a conformance test over the emitted envelope with a
negative control for each violation), and repairing it inside a boundary-allowlist PR
would mix two workstreams. PR #289's own body already records "Device verification is
still required before Gate 01 can be marked CLOSED" — this finding sharpens that:
Gate 01 cannot be closed on a producer that emits non-conforming objects.

## 9. Not in scope (recorded, not executed)

- `#270` — `require_project_owner` is imported from `api/auth` but defined in
  `solspire/console_router`, so the import raises and the bare `except Exception`
  at `api/main.py` silently drops the entire SolSpire Console from the composed app.
  Independently confirmed in this pass. Belongs to the PR's own workstream.
- `#273` — build-breaking (missing `ArkanaWeaverCanvas`). Do not merge.
- §7 budget breach and §8 contract violations — each needs its own bounded branch/PR.
