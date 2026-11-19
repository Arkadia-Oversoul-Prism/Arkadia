# EVIDENCE — Lane 4: bounded views disclose their own truncation

**Pass:** `lane4/truncation-disclosure-01`
**Base:** `main` = `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` (freshly fetched this pulse)
**Lane:** 4 (Arkana + Weaver + Engineering Lab) — owned paths only
**Disposition:** bounded source repair + guard. No authority, identity, governance or
deployment surface touched.

---

## 1. Defect — a bounded render presented as a complete record

The Lab's own convention is that a bounded render **states its bound**: the repository
surface says *"Showing the first N entries; the observation is capped at M"*, and the
bounded-test surface appends *"… truncated in this view; the server record is
authoritative"*. Three lane-4 renders broke that convention by capping a reader-visible
string with a bare `slice` and no disclosure:

| File | Render | Pre-repair form |
|---|---|---|
| `MissionWorkspace.tsx` | run observation body | `{(o.content ?? "").slice(0, 4000) \|\| "— empty —"}` |
| `MissionWorkspace.tsx` | artifact/provenance JSON | `encoded.slice(0, 400) : fallback` |
| `LabWorkerDispatch.tsx` | model turn text | `{(turn.text ?? "").slice(0, 2000) \|\| "—"}` |

A reader sees a complete-looking value that is actually a prefix. On an evidence surface
whose whole purpose is to *not* overstate what was observed, a silent prefix is the
failure mode it exists to prevent.

The third row was **found by the detector**, not by inspection: after repairing the two
sites I had located by hand, the guard still failed on `recordJson` — which is the
detector demonstrating it measures the class rather than the two literals I already knew.

## 2. Repair

One shared helper, `web/arkadia_console/src/components/lab/renderClip.ts`:

```ts
export const VIEW_CLIP_NOTICE = "… truncated in this view; the server record is authoritative";
export function clipForDisplay(value: string, limit = OBSERVATION_CLIP_LIMIT): string {
  if (value.length <= limit) return value;
  return `${value.slice(0, limit)}\n${VIEW_CLIP_NOTICE}`;
}
```

The three sites call it; `LabBoundedTest.tsx`'s local `clip` becomes a one-line delegate
to it (same signature, same 4000 default, byte-identical output), so the disclosure text
now lives in exactly one place and a surface cannot reintroduce a silent cap by writing
its own `slice`.

## 3. Guard

`tests/test_lab_mission_workspace_contract.py` (already in the derived console-contract
domain — **no new wiring**) gains four nodes:

- `test_bounded_views_disclose_truncation` — the invariant over the two components.
- `test_the_clip_helper_is_the_single_source_of_the_disclosure`.
- `test_negative_control_detector_flags_a_silent_cap` — feeds the detector both
  pre-repair shapes and the repaired form, asserting both polarities.

`_silent_clips` is a pure source detector. It excludes `toISOString().slice(0, 19)`
(fixed-shape date formatting hides nothing) so the rule targets content, not formatting.

## 4. Live negative control on the real component

Not a synthetic fixture — the real `MissionWorkspace.tsx` was reverted to the pre-repair
shape, measured, then restored byte-identically:

```
$ # plant: {(o.content ?? "").slice(0, 4000) || "— empty —"}
FAILED tests/test_lab_mission_workspace_contract.py::test_bounded_views_disclose_truncation
1 failed, 32 passed
$ # restore
33 passed

$ # plant: {(turn.text ?? "").slice(0, 2000) || "—"}
FAILED tests/test_lab_mission_workspace_contract.py::test_bounded_views_disclose_truncation
1 failed, 32 passed
$ # restore
33 passed
```

Restored md5: `MissionWorkspace.tsx` `614afc2a13c6945ac2ba1a0833ab314d`,
`LabWorkerDispatch.tsx` `dac7ad307a232782fdc19871a0c142c1`.

## 5. Verification

| Check | Result |
|---|---|
| `pytest tests/test_lab_mission_workspace_contract.py -q` | **33 passed** (was 29; +4 = the new nodes) |
| `pytest $(python scripts/console_contract_domain.py) -q` | **1171 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `corepack pnpm build` (web/arkadia_console) | **exit 0**, `dist/assets/index-_MfLJoBa.js` 424.63 kB |
| Clean-`main` build (same toolchain) | exit 0, `dist/assets/index-DEGLdObN.js` 424.58 kB |

The bundle hash moves with the source change, as expected; the build is the load-bearing
check, not the hash.

## 6. Boundaries preserved

- Files touched are all inside Lane 4's exclusive ownership
  (`src/components/lab/**`, `tests/test_lab_mission_workspace_contract.py`).
- No `api/main.py`, no authority/identity/governance surface, no deployment config, no
  `api/lab_routes.py` (an authority surface) — the mutation boundary is untouched.
- The new `renderClip.ts` exports `clipForDisplay`, not a component, so the lane-4
  orphaned-projection guard (`test_prism_w4_lane4_render_integrity.py`) is unaffected.

## 7. Not claimed

This is a **repository-source** repair. It is not deployment verification and not
production acceptance. Merge remains human-only under GOV-03.

---

## 8. Addendum — the disclosure assertion was bound to prose, not to the value (2026-11-19)

Appended record. Sections 1-7 remain the record of what they measured and are not rewritten.

### Defect

`test_the_clip_helper_is_the_single_source_of_the_disclosure` asserted

```python
assert "truncated in this view" in clip_source
```

against the whole of `renderClip.ts`. That substring is also present in the module
**docstring** (line 6), so the assertion was satisfied by prose rather than by the constant
the helper emits. Measured on this head (`75455e6`):

| Control | Result |
|---|---|
| Replace `VIEW_CLIP_NOTICE` (line 15) with `"CLIPPED"`, docstring intact | **33 passed** — the guard did not bite |
| Make `clipForDisplay` return a bare `value.slice(0, limit)` (silent cap), constant intact | **33 passed** — the guard did not bite |

Both are the exact defects the file exists to prevent. A guard silent on the defect and its
absence is not a guard.

### Repair

`_disclosure_bindings(source)` takes its domain as an argument and reports two facts:

- `declared` — `VIEW_CLIP_NOTICE` is declared *with* the disclosure text;
- `emitted` — `clipForDisplay` interpolates `${VIEW_CLIP_NOTICE}`, so a declaration nothing
  reads cannot satisfy it.

`test_negative_control_the_disclosure_binding_detects_a_neutered_constant` feeds the
predicate the neutered module and the emission-stripped module, and asserts it stays silent
on the real one, so it cannot report unconditionally.

### Proof

| Check | Before | After |
|---|---|---|
| `pytest tests/test_lab_mission_workspace_contract.py -q` | 33 passed | **34 passed** |
| Live control: `VIEW_CLIP_NOTICE` → `"CLIPPED"` on the real tree | 33 passed (blind) | **2 failed, 32 passed** |
| Restore byte-identically | — | **34 passed** |

`--collect-only`: 33 → 34 (+1 = the new control node). Only
`tests/test_lab_mission_workspace_contract.py` is modified (53 insertions, 1 deletion); no
source, workflow, or authority surface is touched.

### Not claimed

Repository-source test-soundness repair only. No deployment, no acceptance. Merge remains
human-only under GOV-03.
