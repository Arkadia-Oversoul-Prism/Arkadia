# WORKSTREAM STATE — gate-hygiene / AGENTS.md repair fingerprint

Persisted so the next heartbeat reconstructs from evidence, not memory.

## Reconstructed state at BASE_MAIN

```
BASE_MAIN = 002b189dd95e41c9b4f4cca33d08b4121453d289   (origin/main, 2026-09-30)
```

Open PR queue (live, via `gh`):

| PR | head -> base | mergeable | Subject |
| --- | --- | --- | --- |
| #142 | `gate-hygiene/sh05-gate-artifact-provenance-01` -> `main` | CLEAN | SH-05 gate/ artifact provenance |
| #143 | `gate-hygiene/gate2-production-parity-02` -> `main` | CLEAN | gate2 production parity chain |
| #147 | `gate-hygiene/gate2-agents-md-encoding-repair` -> `gate-hygiene/gate2-production-parity-02` | CLEAN | AGENTS.md repair (stacked on #143) |
| #150 | `gate-hygiene/gate2-agents-md-cp866-repair-01` -> `main` | CLEAN | AGENTS.md cp866 repair |
| #151 | `gate-hygiene/agents-md-encoding-adjudication-01` -> `main` | CLEAN | byte-oracle adjudication |

## Adjudication (bytes, not prose)

| Candidate | Cyrillic | Extra non-ASCII vs true alphabet | Verdict |
| --- | --- | --- | --- |
| `main` | 182 | 0 | unrepaired input |
| #143 | 0 | 26 (incl. `U+252C` `U+255D`), 84 lines replaced, cruft +594 | **rejected** — wrong codec |
| #147 | 188 | 7 (incl. `U+21D2` `U+00D7` `U+0410` `U+0416` `U+0422` `U+0424` `U+0442`) | **rejected** — does not repair |
| #150 | 0 | 0 | **correct** |
| #151 | 182 | 0 | not a repair; `AGENTS.md` byte-identical to `main`; compatible with #150 |

Recovered alphabet (12 codepoints):
`00a7 00b7 2013 2014 201c 201d 2026 2192 2194 2260 2b06 1f512`.

Decisive identity: `recover(main)` is an exact byte-for-byte **prefix** of #150's `AGENTS.md`
(382 lines), with 29 lines appended after it. `invertible=True` holds for every candidate, so
the alphabet-subset test — not invertibility — is the discriminator.

Merge-order constraint: #147's base is #143's head, so #147 must not merge before #143 — and
on the merits #147 should be superseded by #150.

## This pass

- Branch: `gate-hygiene/agents-md-repair-fingerprint-01`
- Added: `tests/test_agents_md_repair_fingerprint.py` (2 tests, no skips, no history, no network)
- Added: `docs/control-plane/evidence/gate-hygiene-agents-md-repair-fingerprint-01/EVIDENCE.md`
- Added: this file.

## Baseline fingerprint (recorded, not fixed)

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
  20 failed, 1041 passed, 13 skipped, 2 errors
```

Contract prose records `804 passed / 54 failed / 12 skipped` at `main := 6038989` — STALE.
Live evidence supersedes it. Do not attribute the difference to this change: this change adds
tests only.

Architecture: `python -m pytest tests/architecture -q` -> **11 passed** (contract says 10/10;
observed 11).

## Evidence states

- AGENTS.md encoding adjudication: **VERIFIED** (byte-measured across all four candidates).
- Fingerprint guard: **IMPLEMENTED** (tests exist, discriminate, and pass on live `main`).
- Merge of #150 / closure of #143 / #147: **BLOCKED ON HUMAN AUTHORITY** (merge is sovereign).

## Next bounded task

- Repair-carrier selection is a human merge decision and is not advanced by further machine work.
- If #150 merges: re-run this guard on the merged `main`; it must remain green. That is the
  invariant check, and it is the only follow-up this pass creates.
- Independent, non-consequential candidate: classify the 20-test failure fingerprint in §6 of
  EVIDENCE.md as its own bounded workstream. Do not begin it inside this PR.
