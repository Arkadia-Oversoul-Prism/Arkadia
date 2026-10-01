# EVIDENCE — gate-hygiene: AGENTS.md repair fingerprint

Workstream: gate-hygiene / AGENTS.md encoding adjudication
Bounded objective: make the correct `AGENTS.md` repair mechanically decidable, so the
open repair queue can be adjudicated from the bytes instead of from prose.
Authority: none required beyond a pull request. No source, no repair, no encoding changed.
Result: IMPLEMENTED (tests exist and discriminate; merge remains human/MERGE authority).

## 1. Scope

One new test file. No production code, no existing test, no `AGENTS.md` byte touched.

| File | Change |
| --- | --- |
| `tests/test_agents_md_repair_fingerprint.py` | new — 2 structural fingerprint tests |
| `docs/control-plane/evidence/gate-hygiene-agents-md-repair-fingerprint-01/EVIDENCE.md` | new — this record |

## 2. BASE_MAIN

```
git rev-parse origin/main = 002b189dd95e41c9b4f4cca33d08b4121453d289
```

Live PR queue reconstructed at this SHA: #142–#151 open. Four of them claim to repair
`AGENTS.md`'s encoding corruption: #143, #147, #150, #151.

## 3. What the competing repairs actually are

Each candidate's `AGENTS.md` was fetched from its own head ref
(`https://raw.githubusercontent.com/.../refs/pull/<n>/head/AGENTS.md`) and measured.
The measurement reads bytes only; it consumes no candidate's narrative. Counts were
re-derived in this pass, not copied from the prior run — two were wrong.

| Candidate | Cyrillic | Cruft Δ vs `main` | Recovered alphabet ⊄ true | Line changes vs `main` | Verdict |
| --- | --- | --- | --- | --- | --- |
| `main` | 182 | — (baseline, 3) | no | n/a (is the input) | not yet repaired |
| #143 | 0 | 594 | **yes** — 26 extra incl. `U+252C` `U+255D` | **84 replaced** (0 deleted, 99 inserted) | **rejected** |
| #147 | **188** | 4 | **yes** — `U+0410 U+0416 U+0422 U+0424 U+0442 U+21D2` | 0 replaced, 116 inserted | **rejected** |
| #150 | 0 | 0 | no | 50 replaced, 0 deleted, 29 inserted | **correct** |
| #151 | 182 | 0 | no | **none** — `AGENTS.md` byte-identical to `main` | not a repair |

Decisive identity — the recovery of `main` is an exact **prefix** of #150:

```
recover(main)[:382] == AGENTS.md(#150)[:382]        # byte-for-byte
recover(main)[382:] == ""                           # 382 lines, all of them
AGENTS.md(#150)[382:]                               # 29 further lines — prose appended
                                                    # afterwards, not recovered content
```

This is what makes the adjudication decidable rather than merely plausible: the transform
applied to `main` lands exactly on the region a human already reviewed as clean, and the
only additional content is the append that follows it.

Evidence details:

- **#147 does not repair.** Its commit message and the sibling artifact describe pulling the
  region "verbatim from `main`". Its head still carries **188** Cyrillic look-alikes — **six
  more** than `main`'s 182, not fewer — under the title "repair encoding corruption". A repair
  that leaves a non-zero count is not a repair; its own verification command (`… must print 0`)
  fails on it. It also inserts `U+21D2` and `U+00D7`, neither of which the document ever used.
- **#143 is a different, whole-file transform.** It clears Cyrillic by decoding with the wrong
  codec, replacing **84** `main` lines rather than recovering them. The defect is visible from
  the first content line of the file (`AGENTS.md` line 12), where `main`'s corrupted arrow
  token — `U+0442 U+0416 U+0422`, the CP866 mojibake of `→` (`U+2192`) — becomes
  `U+00E9 U+0105 U+00A2 U+0105 U+00F3`. Those are Latin-1 / Latin Extended-A codepoints,
  not Cyrillic: the transform swapped one mojibake alphabet for another instead of
  recovering the original. It also introduces `U+252C`/`U+255D` — the box-drawing pair a
  mis-chosen codec regenerates from `U+00B7` — which never belonged to this document. Total
  cruft delta: **+594** characters.
- **#151 is not a repair at all.** Its `AGENTS.md` is byte-identical to `main` (`cmp` clean);
  it lands an adjudication *test* and defers the repair. It is compatible with #150.
- **#147 is stacked on #143.** `#147.base.ref = gate-hygiene/gate2-production-parity-02`
  (= `#143.head.ref`), so merging #147 before #143 would change its own base and invalidate the
  review. Merge-order-constrained.

## 4. The fingerprint

Two invariants, both history-free and network-free, so they run in a shallow clone and in CI:

1. **Invertibility.** `recover` must be exact on its own domain: the changed-line set must equal
   the classified-corrupted set, the line count must be preserved, and re-applying the forward
   transform (`utf-8` → `cp866`) over the recovered domain must return the input byte-for-byte.
   This is what makes the codec decidable instead of a matter of taste — a repair built on
   cp1250/iso-8859-2/cp1252 cannot round-trip its own output.
2. **Alphabet containment.** In the recovered text, `AGENTS.md`'s non-ASCII alphabet must be a
   subset of the document's true twelve-codepoint alphabet
   (`00a7 00b7 2013 2014 201c 201d 2026 2192 2194 2260 2b06 1f512`). Cyrillic is asserted
   separately for a clear failure message.

Why this is a fingerprint and not a formatting taste: the subset test is **monotone under
merging**. It passes on `main`, on #150, and on the file after #150 merges; it fails on #143 and
#147 both before and after merge. It names no candidate and no branch, so it cannot go stale
when the queue changes.

Honest scope: the guard polices what the document is *made of*, not how it reads. `U+2014` and
`U+2192` are members of the true alphabet, so a repair that pastes literal em dashes into prose
*about* em dashes passes here and still merits a review comment. That is a presentational call
and asserting it would break on the next legitimate em dash.

## 5. Verification

```
python -m pytest tests/test_agents_md_repair_fingerprint.py -q
  2 passed

python -m pytest tests/architecture -q
  11 passed
```

Discrimination harness (reads each candidate's bytes, applies the tests' own predicates —
re-measured this pass):

```
main  invertible=True  alphabet_subset=True   repaired_lines=50  extra=[]
143   invertible=True  alphabet_subset=False  repaired_lines= 0  extra=26 incl. 0x252c 0x255d
147   invertible=True  alphabet_subset=False  repaired_lines=50  extra=7  incl. 0x21d2 0xd7 0x410 0x416 0x422 0x424 0x442
150   invertible=True  alphabet_subset=True   repaired_lines= 0  extra=[]
151   invertible=True  alphabet_subset=True   repaired_lines=50  extra=[]
```

Note that `invertible=True` holds for *every* candidate, including the two rejected ones:
invertibility alone does not adjudicate the queue. The alphabet-subset test is the
discriminator, and it is the one that separates #150 from #143 and #147.

Full suite fingerprint recorded at BASE_MAIN — see §6.

## 6. Baseline comparison

Full suite at BASE_MAIN (`002b189dd95e`), environment commands from repo memory:

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
  20 failed, 1041 passed, 13 skipped, 2 errors in 109.54s
```

Observed fingerprint, recorded so a change can be attributed:

- **2 collection errors** — `tests/test_autonomy.py` (`load_autonomy_config`),
  `tests/test_render_codex.py` (`arkadia_drive_sync`). Documented pre-existing debt;
  reproduced, not caused. `--continue-on-collection-errors` is required or pytest aborts
  before running anything.
- **13 skipped.**
- **20 failed**, by module:
  `test_ais_w2_living_gate_grove_handoff.py` (1),
  `test_engineering_scheduler_bootstrap.py` (2),
  `test_gate_serve_script.py` (1), `test_gate_status.py` (1),
  `test_identity_spine_w1.py` (1), `test_m02_reasomate_truth.py` (1),
  `test_solspire_r1_governance_convergence.py` (2),
  `test_solspire_r2_github_mutation.py` (1),
  `test_solspire_r3_execution_runtime.py` (1),
  `test_spiral_grove_activity_runtime.py` (4), `test_spiral_grove_registry.py` (2),
  `test_steward_filter.py` (3).

This change adds two tests and touches no existing test or source file, so it cannot alter
any existing outcome. Its own contribution is 2 passing tests, which are not among the 20.

Note on the contract's stated baseline: it records `804 passed / 54 failed / 12 skipped`
at `main := 6038989`. The live repository has since moved to `002b189dd95e` and the
observed fingerprint above differs. Per the contract's own rule, status is derived from
live evidence; the prose baseline is `STALE` and the observed one supersedes it here.

## 6a. Relationship to the adjudication already in the queue

PR #151 (`gate-hygiene/agents-md-encoding-adjudication-01`) lands
`scripts/agents_md_encoding_audit.py` and `tests/test_agents_md_encoding_adjudication.py`.
That suite is more thorough than this one and reaches the same verdict. This guard is not a
replacement; it is the always-running subset, for two reasons that its own docstring must be
read against:

- **#151's live-file tests require git history.** `test_recover_is_decidable_on_the_live_file`,
  `test_recovered_text_equals_the_repaired_tip`, and `test_corruption_origin_is_re_derivable`
  shell out to `git show <rev>:AGENTS.md` and `pytest.skip` when the revision is unavailable.
  Local agent runs clone `--depth=1` and `actions/checkout@v4` defaults to `fetch-depth: 1`
  for every workflow except `sg-02-fe-2-v.yml` and the secret scan. In those contexts #151's
  three load-bearing tests skip; this module's two tests still run, because they read only
  the working tree.
- **The alphabet invariant is new.** #151 asserts the recovered file has zero Cyrillic. It
  does not assert that the recovered file introduces no *new* non-ASCII class — which is the
  exact defect that separates the correct repair from a wrong-codec one (#143's 26 extras,
  #147's `U+21D2`). That is what `test_recovered_agents_md_uses_only_the_established_alphabet`
  adds.

The round-trip check overlaps #151's `round_trip_holds` by intent: the same invariant is
worth asserting in a context that cannot skip. `recover` is self-contained rather than
imported from `scripts/agents_md_encoding_audit` because that module does not exist on
`main` — an import would make this guard error until #151 merges, defeating its purpose.

## 6b. Invariant, not snapshot

The guard holds **today on unrepaired `main`** (`alphabet_subset=True`, §5) and will hold
**after #150 merges**, because #150's recovered text is exactly what `recover` produces. It
fails on #143 and #147 in both states. The guard therefore does not need to be re-tuned when
the queue is resolved, and it cannot go red merely because `AGENTS.md` was correctly repaired.

## 7. Remaining uncertainty / authorization

- **Merge order.** #150 (`No-LLM`, `main`-based, CLEAN) is the correct repair carrier. #147 must
  not merge before #143 because it is stacked on it; and #147 should be superseded by #150 on the
  merits — it does not repair. #143 should be closed as a wrong-codec transform. #151 is
  compatible and can merge independently. **This is a human merge decision; no merge is
  performed by this pass.**
- **Presentational residue (non-blocking).** #150's appended section pastes literal em dashes and
  arrows into the prose that documents them. The guard permits this by design (§4). A reviewer
  may ask for codepoint phrasing; it does not affect correctness.
- **Alphabet growth.** If the document legitimately needs a thirteenth non-ASCII character, add
  it to `RECOVERED_NON_ASCII_ALPHABET` with evidence. Do not widen `recover` to pass.
- Nothing in this change requires or grants authority. No new mutation path, no new
  authorization path, no governance or identity surface touched.
