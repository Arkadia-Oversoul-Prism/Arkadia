# Gate-02 — canonical Render alias observation + marker-oracle polarity

Workstream: gate-hygiene / Gate-02 production observation.
Base main: `07834232`.

## Defect 1 (primary) — the harness never observed the SPA

`scripts/gate2_production_observation.py` fetched the canonical alias `ALIAS`
(`https://arkadia-qzu4.onrender.com/`) with **no `Accept` header**. The canonical
runtime (`api/main.py::root`) serves the Prism SPA at `/` only to a browser
navigation carrying an HTML `Accept` header, and returns the liveness JSON
otherwise. Under the previous Vercel runtime every path was rewritten to
`index.html`, so the missing header was invisible; on Render it read a 40-byte
JSON document, found no `assets/` reference, reported `manifest: none`, and
scored a marker table against an artifact it had never opened — a phantom
SG-04 regression (`in_deployed_artifact: 0` from an unobserved artifact).

**Repair:** `head()` takes an explicit `accept` parameter and the alias
observation passes `BROWSER_ACCEPT`. The alias marker walk now reads the served
SPA bundle.

Measured live (main `07834232`):

```
ALIAS https://arkadia-qzu4.onrender.com/ -> HTTP 200
manifest: assets/index-BzLymmg4.js, assets/index-CnHIcYxe.css
bundle  : assets/index-BzLymmg4.js (892397 bytes)
SG-04   in source: True  in deployed artifact: 1  => REGRESSION: False
```

## Defect 2 (exposed by the repair) — marker oracle is polarity-blind

`classify_marker_oracle` tested `all(count > 0)` and named every zero-count
literal as absent. The marker table carries **one control literal** whose
declared expectation is *absent* (`separate downstream stages`, `expected=False`).
Once the artifact could actually be read, the correct control reading of `0` was
scored as a divergence, so a sound artifact produced a false `CONTRADICTED`.

**Repair:** a marker violates when its reading disagrees with its declared
polarity `(v == 0) != (not MARKERS[k][1])`. Controls are now scored by their own
expectation. Live verdict: `marker-set oracle VERIFIED (marker set observed in
served artifact)`.

## Defect 3 (unobserved-artifact guard)

`classify_sg04` now treats `in_artifact is None` (nothing fetched) as
non-evaluable, distinct from a fetched artifact reading `0` (a real absence that
still scores). The call site passes `None` rather than a defaulted `0`. The
existing predicate tests (`classify_sg04(MARKER_APP, MARKER_APP, True, 0)` →
`regression True`) still hold: an integer `0` remains a real absence.

## Defect 4 (test-side) — live root-config test pinned the pre-retirement tree

`tests/test_gate2_alias_app_binding.py::test_live_root_config_names_a_known_frontend`
asserted `output is not None` unconditionally. Root `vercel.json` was retired
(removed at `5a292e11`) when the canonical runtime moved to Render, so the test
was red on live `main` — the single baseline failure in this pass. Repaired to
assert the *transition*: when the file is absent the binding is undetermined
(`None`); when present it must still name a known frontend (repoint guard kept).

## Test-side polarity pins corrected

`tests/test_gate2_production_observation.py` asserted that an all-ones marker
reading is `VERIFIED` and that an all-zeros reading lists *every* marker as
absent. Both encode the refuted assumption that every literal is positive. They
are now polarity-aware (`_polar_reading`, `_positive_markers`) and a new
negative control (`test_a_present_control_marker_is_contradicted`) asserts an
all-ones reading is **not** `VERIFIED`.

## Verification

| Command | Result |
|---|---|
| `pytest tests/test_gate2_production_observation.py tests/test_gate2_alias_app_binding.py -q` | **52 passed** |
| live `python scripts/gate2_production_observation.py` | marker oracle `VERIFIED`, SG-04 `False` |
| full suite `pytest tests/ -q -rEf --continue-on-collection-errors` | 30 failed / 2028 passed / 20 skipped / 1 error |

## Regression boundary

Failing/error node set on `main` `07834232` = **32** nodes
(`sha256 9450088c…`); on the branch = **31** nodes (`sha256 a6f0e671…`). The only
delta is the repaired `test_live_root_config_names_a_known_frontend`. Zero new
failures. The remaining `ERROR tests/test_autonomy.py` is the pre-existing CE-01
`weaver.autonomy` module-vs-package collision — sovereign-reserved, not touched.

## Boundary status (unchanged where not observed)

`deployment build output observed` stays **BLOCKED** (Vercel Deployment
Protection / SSO on the deployment-specific URL). `build <-> source lineage`
reads `UNKNOWN` because the newest Production record `078342327942` is *not*
among the 12 scanned candidate SHAs; this is a repository-source statement about
the harness, not a production-parity claim. Production acceptance remains
**NOT CLAIMED** (human authority).
