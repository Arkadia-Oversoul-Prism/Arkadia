# WORKSTREAM STATE — gate02 / capability-chamber merge-loss repair 01

Reconstructed from live evidence at 2026-10-01T14:0xZ. Next heartbeat must reconstruct
again; do not treat this file as authoritative over the repository.

## Live state at pass start

| Fact | Value |
|---|---|
| BASE_MAIN | `002b189dd95e41c9b4f4cca33d08b4121453d289` (Merge PR #141) |
| Open PRs | 23 |
| Credential | ambient `github_token`, push/admin/maintain all `True` |
| `tests/architecture` | 11 passed |
| `api/main.py` | 2519 / 2600 lines, compiles |
| Frontend build | environment-blocked (no registry) |

## Active workstream

GATE-02 (human-origin authority), **bounded repair sub-stream**. GATE-00 baseline hygiene
remains active; no gate advance is claimed by this pass.

## Central PRs and the resolved contradiction

| PR | Head | Role |
|---|---|---|
| #163 | `gate-hygiene/queue-drain-verification-01` @ `1e9d40029486` | claimed the source-side defect |
| #165 | `gate02/independent-verification-163` @ `5a3d30201b5f` | competing "restore mount" design |

**Contradiction resolved by measurement.** All three revisions (`main`, `#163`, `#165`) of
`CapabilityChamber.tsx` are the same blob `0cde2f782f1c`; no open PR modifies it. The inline
design is canonical (pinned by 3 test files); the mount design is falsified (4→6 failures).

## Defect, confirmed and corrected

`ff80b8c` is a hand-resolved merge that invented a state present in neither parent: it took
the inline surface from parent 2 (`5c78fcb`) but the import line from parent 1 (`cef5a59`),
leaving a dangling `ActivityRuntime` import, a dropped `useEffect` binding, and a dropped
`surfaceMeta` anchor.

- #163's two-defect claim: **confirmed**, and **corrected upward to three** (dangling import).
- #163's `test_chamber_preserves_sg03_downstream_boundary` merge-loss attribution:
  **falsified** — the literal is absent in every revision, including the coherent one.
- #165's pass-4 citation `test_spiral_grove_boundary_is_enforced`: **non-reproducible**,
  absent from `#165` head, `main`, and `#165`'s own evidence.

## Repair

Mechanically determined: repaired blob `5c78fcb` == `ff80b8c^2` == `44e1c99`. Empty diff
against the merge's second parent. One file, `+2 -2`.

## Fingerprint

```
full suite (both trees) : 48 failed, 761 passed, 12 skipped, 27 errors
failing-node set delta  : NONE
sha256(main nodes)      : 113fa7fa6c950e424a60efa15cfff8322ff967cd57af127b13796ff55556da20
sha256(repaired nodes)  : 113fa7fa6c950e424a60efa15cfff8322ff967cd57af127b13796ff55556da20
architecture            : 11 passed
```

Absolute counts differ from the contract's recorded baseline (`6038989`); that is an
environment delta, measured on `main` directly. Only the **relative** claim is made.

## Unresolved / next bounded task

1. Four SG-04 failures remain — test-side defects and one design contradiction. Not fixed
   here (would be scope expansion). Needs its own bounded workstream.
2. `vite build` unverifiable in this environment.
3. #165's pass-4 fingerprint should be re-derived before being trusted.

## PR linkage

```
PR                : #166  https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/166
branch            : gate02/capability-chamber-merge-loss-repair-01
base              : main
head              : e1ea4f957006
commits           : 2978dbb (repair + evidence), e1ea4f9 (AGENTS.md forensics)
mergeable         : True    mergeable_state: clean
CI on head        : validate PASS · Full-history secret scan PASS · Vercel Preview PASS
glance comment    : #issuecomment-5933433773
status            : READY_FOR_SOVEREIGN_MERGE
```

## Standing boundary

`main` SHA → deployment SHA → production response → UI/runtime observation → evidence
artifact. This pass advances only the repository half. Production parity is **UNKNOWN** —
no deployment identity was inspected, and no parity is claimed.
