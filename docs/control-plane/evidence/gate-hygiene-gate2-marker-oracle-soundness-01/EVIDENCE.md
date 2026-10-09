# EVIDENCE — Gate-2 observation harness: marker-oracle soundness

Workstream: `gate-hygiene/gate2-marker-oracle-soundness-01`
Gate: GATE-02 (production parity observation)
Base main: `24a00f856a0286cbb464a4b585117dd57a2646fa` ("fix: complete HF auth on N-ATLaS Gradio SSE")
Branch: `gate-hygiene/gate2-marker-oracle-soundness-01`

Status: **IMPLEMENTED** (harness + tests + evidence; no runtime acceptance claimed)

---

## 1. Objective

Repair a soundness defect in `scripts/gate2_production_observation.py` — the read-only
harness every Gate-2 chain claim rests on. The harness conflated *the application it
observed* with *the application its marker list describes*, so it could report marker
agreement it never observed.

Bounded to: one script, one existing test file, evidence docs. No product code, no
`api/main.py`, no workflow, no merge.

---

## 2. The defect, measured

### 2.1 The alias serves a different application than the markers describe

The root `vercel.json` was repointed to the Console frontend at `404452e0`. Since then
the production alias `https://arkadia-prism.vercel.app/` resolves to the **Console**
app. All eight harness markers are **Prism** literals (`Spiral Codex`, `Arkana`,
`ReasoMate`, `solspire-object-summary`, `opportunity-radar`, …), so on the served
Console artifact every marker reads 0.

A live run of the pre-repair harness therefore printed, alongside a genuine source
closure:

```
VERIFIED (marker set matches, source closed)
```

An entirely-absent marker set — the strongest possible evidence that the artifact is
*not* this application — was fused into a `VERIFIED` verdict. The marker half could
never fail on its own.

### 2.2 Identity was read from neither the deployment nor the marker list

The single `DEPLOYED_APP` constant was used both as the closure-scope fallback *and*
as the application the markers describe. Two distinct facts were represented by one
name, which is how a Console artifact came to be scored against Prism markers.

---

## 3. The repair

`scripts/gate2_production_observation.py`:

- **`MARKER_APP = "arkadia-prism"`** — the application the marker list was drawn from.
  A property of the list, never inferred from a fetched artifact.
- **`DEPLOYED_APP = "console"`** retained — the application currently served.
- **`KNOWN_FRONTENDS`** — the disjoint build inputs of both apps, so a Console build
  can never be measured on Prism ancestry.
- **`frontend_of(environment)`** — reads app identity from the deployment label's
  project suffix (the only identity the API exposes), returning `None` for an unknown
  project. Splits on the en/em-dash or spaced hyphen separator, never a bare hyphen
  (which is part of `arkadia-prism`).
- **`last_build_input_commit(app)`** — closure scoped to one app's build input.
- **`classify_marker_oracle(app, observed, stale)`** — a separate boundary verdict.
  A different app returns `NOT OBSERVED`, not `CONTRADICTED`; an undetermined app
  likewise. Agreement requires a *positive* reading; `None` (nothing fetched) and `{}`
  (nothing found) are distinct states.
- The old `classify_source_lineage` verdict no longer claims a marker observation:
  `VERIFIED (source closed; marker set NOT observed)`.

`main()` scopes the closure call to `deployed_app or MARKER_APP` and adds the
`marker-set oracle` boundary; the SG-04 block reports `NOT EVALUABLE` rather than a
phantom regression when the served app has no SG-04 surface.

---

## 4. Verification

| command | result |
|---|---|
| `python -m pytest tests/test_gate2_production_observation.py -q` | **29 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile scripts/gate2_production_observation.py` | OK |
| live `python scripts/gate2_production_observation.py` | runs end-to-end, honest verdicts (below) |

Live boundary classification after the repair (main `24a00f85`, deploy `6939001431`):

```
current main resolved        VERIFIED
main -> deployment identity  VERIFIED  (deploy SHA == main)
deployment build output      BLOCKED   (Vercel Deployment Protection / SSO)
alias reachable              VERIFIED  (HTTP 200)
alias -> deployment SHA      UNKNOWN (immaterial: candidates share frontend source)
build <-> source lineage     VERIFIED (source closed; marker set NOT observed)
marker-set oracle            NOT OBSERVED (artifact is 'console'; markers describe 'arkadia-prism')
browser-rendered UI          UNKNOWN
production acceptance        NOT CLAIMED (human authority)
```

The pre-repair `VERIFIED (marker set matches, source closed)` is no longer reachable:
`test_the_pre_repair_verdict_is_unreachable_from_the_classifier` is the negative
control. `test_markers_present_is_the_only_verified_marker_verdict` is the positive
control — the verdict is still reachable, but only from a positive reading.

### Marker provenance (verified this pass)

All eight markers are Prism source literals. The served Console artifact reads
`0` on all eight, while Console-unique runtime literals (`reconciled`, `WORK_EVENT`,
`AUTHORIZATION`, `standing`) are present in the same fetch. This is the observed
evidence that the app-identity split, not marker drift, produces the zero counts.

---

## 5. What this does and does not change

- Does **not** close Gate-2. `deployment build output` stays `BLOCKED` on provider
  auth (Vercel SSO) and `browser-rendered UI` stays `UNKNOWN`. The harness is now
  honest about those, which is the precondition for any future closure.
- Does **not** claim production parity for the Prism surface. The alias serves
  Console, so the Prism artifact is not observable through it without a
  deployment-specific URL, which is SSO-protected.
- Corrects an instrument, not a product surface.

## 6. Authority boundary

Sovereign merge authority. No merge performed; no push to `main`; no force-push.
