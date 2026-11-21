# Lane 1 — bind the lens-strip owner detector to a control

**Lane:** 1 (shell / navigation / design system / integration seam)
**Base:** `main` @ `1bff8c42e78f153203641db6d8a90818f7ff6ab2` (2026-11-21T07:43:32+01:00)
**Scope:** `tests/test_console_shell_nav_contract.py` (lane-1 owned) + this record.
**Disposition:** IMPLEMENTED, draft. Merge execution is human-only (GOV-03).

## 1. The defect

`test_the_lens_strip_is_declared_once` decides its verdict with

```python
owners = _lens_testid_owners(_ts_sources())
assert owners == ["web/arkadia_console/src/components/SurfaceLenses.tsx"]
```

That is a **one-element equality**, not an emptiness check, so the assertion is
satisfied by a detector that returns that element without reading its argument at
all. Measured on this branch's parent: replacing the body of `_lens_testid_owners`
with

```python
return ["web/arkadia_console/src/components/SurfaceLenses.tsx"]
```

leaves the live node **passing** (see §3, mutation A). The guard reads green while
judging nothing — the same silent-pass direction already repaired for the
surface-ownership classifier in #671.

The file's header states that "each detector carries a negative control". For
`_lens_testid_owners` that claim was not true: the two neighbouring controls
(`test_detector_flags_a_decorative_lens_control`,
`test_detector_reads_the_whole_tag_when_a_handler_contains_an_arrow`) both exercise
`_decorative_lens_controls`, which is a different function. A control that calls a
sibling never binds the detector under test.

## 2. The change

One node added after the live assertion it protects:

`tests/test_console_shell_nav_contract.py::test_detector_flags_a_second_lens_strip_owner`

It holds `_lens_testid_owners` to its contract in **both** polarities, through the
same function the live assertion calls:

| input | expected | why |
| --- | --- | --- |
| two files, each with a per-lens `data-testid` | both reported, in order | a second lens strip is the defect the live node exists to catch; a constant cannot answer this |
| the strip *container* only (`data-testid={`${surface}-lenses`}`) | `[]` | the container is not a per-lens control; this is the scope boundary the live node relies on |
| `{}` | `[]` | an empty tree declares no strip |

The container case is not hypothetical: `SurfaceLenses.tsx` declares exactly these
two testids (`${surface}-lenses` on the container at line 40, `surface-lens-${l.id}`
on each control at line 49). The `-lens-` terminator in `LENS_CONTROL_TESTID` is
what separates them; a prefix-only regex lets the container borrow ownership.

No console source, registry, backend contract, workflow, lane doc or snapshot is
touched, so `lane-doc-currency` cannot redden on merge and no other lane's owned
path is edited.

## 3. Proof, bound to this tree

Measured on the working tree at the branch head named in the PR.

**Live module:** `python -m pytest tests/test_console_shell_nav_contract.py -q`
→ `55 passed` (parent tree: 54 nodes; `+1` is the new control, confirmed by the
per-run totals below rather than inferred).

**Mutation A — constant return** (the silent-pass shape):

```
FAILED tests/test_console_shell_nav_contract.py::test_detector_flags_a_second_lens_strip_owner
1 failed, 54 passed
```

Exactly one node fails, and it is the new one. `test_the_lens_strip_is_declared_once`
stays green under a detector that reads nothing — which is the defect, reproduced.

**Mutation B — prefix-only regex** (`re.compile(r"-lens")`):

```
FAILED tests/test_console_shell_nav_contract.py::test_no_lens_control_is_decorative
FAILED tests/test_console_shell_nav_contract.py::test_detector_flags_a_second_lens_strip_owner
2 failed, 53 passed
```

**Restored** byte-identically (`diff -q` against the pre-mutation copy is empty) and
re-run: `55 passed`.

**Architecture fitness:** `python -m pytest tests/architecture -q` → `11 passed`.
**Mutation boundary:** both changed paths piped through
`scripts/cp10_mutation_boundary_policy.py --judge` → `PASS` (exit 0).

## 4. What is not claimed

- No merge, deployment or acceptance. Merge execution is human-only (GOV-03); this
  record is an eligibility input, not authority.
- `console_contract_domain.py` derives its domain at test time and already selects
  `tests/**`, so no workflow edit is needed; CI execution of the new node is
  expected but is not asserted here — it is read from the gate's step log once the
  run exists.
- The live detector's correctness on the *real* console tree is unchanged; this
  change adds proof that the detector can distinguish the shapes it is asked about,
  not new coverage of the console source.
