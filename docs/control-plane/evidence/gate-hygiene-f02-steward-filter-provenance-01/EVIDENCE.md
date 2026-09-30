# F-02 — steward_filter node provenance (Genesis-origin, never-passing)

**Workstream:** `gate-hygiene` / `SH-02` (STALE_ASSERTION migration)
**Bounded question:** are the three `tests/test_steward_filter.py` nodes — ledger rows
**27–29**, registered as `F-02` by PR #140 — *stale assertions* (test drifted away from intact
behaviour) or *defects*? PR #138 §7 calls them "a plausible in-envelope candidate, now queued";
PR #140 calls them a decision. Both cannot be right, and the disposition of 3 of the 35 ledger
rows depends on which is true.
**Classification:** `VERIFIED` (repository-layer). **Evidence-only — no test, source, workflow,
governance, or constitutional file is modified.**
**Base:** `df7a99a067382401c00de5e7bbaaac0125ba2088` (`main` @ merge of #131).

---

## 1. Answer

**They are not stale assertions. They have never passed in this repository, and the module
contradicts its own declared contract.**

Three independent facts settle it:

1. **Neither the test nor the module has been modified since the Genesis root commit.** Both
   files are blob-identical to `9ab26fc`.
2. **All three nodes fail identically at the Genesis commit.** There is no commit at which they
   were green, so no "assertion drifted from intact behaviour" story is available.
3. **Each failure is a module-vs-own-docstring contradiction**, not a test-vs-module mismatch.
   The test is the faithful reading of the contract; the module is not.

Consequence: PR #138's "plausible in-envelope candidate" is **falsified**. These are not
repairable by re-pointing an assertion — there is no correct surface to re-point to. PR #140's
"a decision, not a batch" is **confirmed and strengthened**: `F-02` is a *defect*, and the
ledger's `SH-06` fold-in was correct.

---

## 2. Provenance — unchanged since Genesis

```
$ git log --oneline --follow -- tests/test_steward_filter.py
9ab26fc Genesis: Stone 5 Ascension Finalized
$ git log --oneline --follow -- weaver/filters/steward.py
9ab26fc Genesis: Stone 5 Ascension Finalized

$ git log --oneline 9ab26fc..HEAD -- tests/test_steward_filter.py weaver/filters/steward.py
(no output — zero commits since Genesis touch either path)

tests/test_steward_filter.py   HEAD=893871f8a2  GENESIS=893871f8a2  IDENTICAL
weaver/filters/steward.py      HEAD=2959898210  GENESIS=2959898210  IDENTICAL
```

`--follow` is rename-aware, so a rename-and-edit would still appear. The blob comparison is the
stronger statement: the *content* has not moved at all, not merely the path.

## 3. Negative control — the nodes fail at Genesis too

The claim "these assertions are stale" requires a prior green state. Reproduced in a detached
worktree at the Genesis commit:

```
$ git worktree add --detach /tmp/wt/f02 9ab26fc
$ cd /tmp/wt/f02 && PYTHONPATH=/tmp/wt/f02/archive/legacy_python \
    python -m pytest tests/test_steward_filter.py -q
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_compress_to_choices
3 failed, 5 passed in 0.03s
```

Identical result on `main` @ `df7a99a`: `3 failed, 5 passed`.

| revision | `test_blocks_identity_claims` | `test_allows_mythic_with_action` | `test_compress_to_choices` |
|---|---|---|---|
| `9ab26fc` (Genesis, 2026-01-01) | FAILED | FAILED | FAILED |
| `df7a99a` (main) | FAILED | FAILED | FAILED |

Because the only commit that ever touched either file is Genesis, and the nodes fail **at**
Genesis, the full-history node set is: `{FAILED}`. There is no green revision. The
`STALE_ASSERTION` bucket definition — *"assertion drifted from reworded-but-intact behaviour"* —
has no support here.

## 4. Each node contradicts the module's own documented contract

### 4.1 `test_blocks_identity_claims` — `test_steward_filter.py:12`

```python
assert steward_filter("You have transcended") is None
```

`weaver/filters/steward.py:30` forbids `"transcendent"`. The substring `"transcendent"` does not
occur in `"you have transcended"` (`transcend` + `ed` ≠ `transcendent`), so the filter returns
the text and the assertion fails. The module's docstring says *"Blocks identity inflation"* and
the list is plainly intended as a stem family — the module under-enforces its own contract.

### 4.2 `test_allows_mythic_with_action` — `test_steward_filter.py:33`

```python
assert steward_filter("The field resonates. I will do this.") is not None
```

Traced through the module:

| rule | line | evaluation |
|---|---|---|
| Rule 1 identity | `:28–32` | no forbidden word — pass |
| Rule 2 pure symbolism | `:35` | `count("symbolism") == 0` — pass |
| Rule 3 action language | `:38–41` | `len == 36`, not `> 200` — **not evaluated** |
| Rule 4 mythic density | `:44–47` | `"field"×1 + "resonance"×1 = 2`; threshold `len/100 = 0.36`; `2 > 0.36` → **`return None`** |

Rule 4 rejects the input *before* Rule 3 is ever consulted. The test's intent — *mythic language
is allowed when action-grounded* — is expressed in the module's docstring (*"Block symbolism
without action"*) and by Rule 3's existence. Rule 4 as written makes Rule 3 unreachable for any
short, densely mythic input, i.e. it negates the stated design.

### 4.3 `test_compress_to_choices` — `test_steward_filter.py:55`

```python
compressed = compress_to_choices("Many words here. Do this. More noise. Quit that. Final thought.")
assert "More noise" not in compressed
```

`compress_to_choices` (`:58–74`) splits on `"\n"` and keeps lines containing an action verb.
The input is a **single line**, so it is kept whole — the `"More noise"` sentence is never a
candidate for removal. The module's docstring says *"Keep only sentences with action verbs"*;
the implementation keeps *lines*. It never strips non-action sentences from within a line.

## 5. Why this is a decision, not a batch

All three are the same defect class: **the implementation is narrower than its own documented
contract.** Repairing them requires a change to `weaver/filters/steward.py`:

| node | required module change |
|---|---|
| `test_blocks_identity_claims` | stem-match the identity family (`transcend*`) |
| `test_allows_mythic_with_action` | reconcile Rule 3 vs Rule 4 — either scope Rule 4 to long inputs, or lower its density threshold |
| `test_compress_to_choices` | split on sentence boundaries, not `"\n"` |

Every one of these is a **behaviour change to a filter**, not a test edit. That places them
outside the `SH-02` envelope, whose rule is *"re-point the assertion at the surface that now owns
the behaviour … test-only edits."* There is no surface that owns the asserted behaviour; the
behaviour does not exist.

## 6. Blast radius — the module is unwired

```
$ grep -rn "steward_filter\|compress_to_choices\|check_sustainability" --include=*.py . \
    | grep -v tests/test_steward_filter.py | grep -v weaver/filters/steward.py
(no output)
```

`weaver/filters/steward.py` has **no importer anywhere in the repository** — only its own test.
`docs/verification/P1-1_PRIVATE_BETA.md:42` independently records it as
**"EXISTING + UNWIRED … no runtime import"**.

Two consequences:

- The defect is **latent**, not a live behaviour failure. Nothing in the running system is
  affected today. This lowers severity and *supports* deferring rather than rushing a fix.
- Conversely, repairing it changes the semantics of a module that no production path exercises,
  so the change cannot be validated against real usage. That is an argument for the sovereign
  deciding the intended contract explicitly, rather than an implementer inferring it.

Governance: `governance/proposals/P-010-steward-filter.md` is the module's originating proposal
(*"Proposal-only logic"*, *"Blocks symbolic drift without action"*). It is **consistent with the
test**, not with the implementation. `P-010` therefore already supplies the intent; what is
missing is a sovereign ruling on whether to enforce it.

## 7. Recommendation (sovereign authority)

**Disposition: keep red. Do not repair in `SH-02`. Do not add to a batch.**

Rationale, in contract terms:

- Repairing would mean editing a filter's behaviour to make three long-red tests pass — the
  inverse of *"re-point the assertion at the surface that now owns the behaviour."*
- The module is unwired, so there is no runtime evidence available to justify either semantic
  choice; *"DECLARE_VERIFIED_WITHOUT_RUNTIME_EVIDENCE"* is forbidden.
- PR #140's disposition of these 3 rows as a **decision** is correct. PR #138 §7's
  "plausible in-envelope candidate" should be treated as **superseded** by this artifact.

If the sovereign wishes to close them, the bounded task is a **module repair under a new
workstream id** (`SH-06`-scoped), with an explicit ruling on the three contract questions in §5,
plus negative controls proving each repaired rule can still fail. That work is **not** proposed
for execution here — it is recorded for the queue.

---

## 8. Provenance of this artifact

- `BASE_MAIN` = `df7a99a067382401c00de5e7bbaaac0125ba2088`; local `main` / `origin/main` /
  `origin/HEAD` agree; tree clean at branch creation.
- The clone is **full, not shallow** (`git rev-parse --is-shallow-repository` → `false`; 1393
  commits; no `.git/shallow`), so the Genesis-era claims above are **directly verifiable here**
  and are not inferred. (This corrects a standing repo note that describes the clone as
  grafted; `df7a99a` carries its parents and ancestor walks succeed.)
- The Genesis worktree was created detached, used read-only, and removed
  (`git worktree remove --force`). No worktree remains.
- `api/main.py` untouched — 2519 lines, `py_compile` clean.

## 9. Uncertainty

- **Unwired-ness is a static claim.** A dynamic import (e.g. `importlib` on a configured path)
  would not appear in the grep. No such mechanism was found, and `P1-1_PRIVATE_BETA.md`
  agrees, but this is repository evidence, not runtime observation.
- **Intent is inferred from docstrings and `P-010`.** A maintainer could hold a different
  contract. §4 reports what the module *says* it does; §7 leaves the ruling to the sovereign.
- **Severity is unranked here.** These nodes are outside `SH-02`; no product priority is claimed.
