# EVIDENCE — Gate hygiene: stale-assertion repair (Pass C surface ownership)

- **Gate / workstream:** GATE-10 context — test-suite hygiene
- **Bounded task:** `SH-02b` — `tests/test_prism_pass_c_surface_ownership.py` (6 nodes),
  named as the next bounded task by
  `docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-solariun-consolidation-01/WORKSTREAM_STATE.md`
- **BASE_MAIN:** `417d32d6ccb6f0deb318b19028b828df5b1c1363` (see §1a — an earlier draft of this
  file recorded `ee3fac1`, which was the batch-2 base; the correction is documented, not hidden)
- **Branch:** `gate-hygiene/baseline-stale-assertion-repair-surface-ownership-01`
- **Authority:** test-hygiene only. No source, policy, governance, or architecture mutation.
- **Status:** IMPLEMENTED (targeted tests pass, protected regressions pass, negative controls
  fire, full-suite delta verified by node name; sovereign merge pending)

---

## 1. Scope

`tests/test_prism_pass_c_surface_ownership.py` holds Pass C's ownership claims: which
surface owns which legacy `View` id. The Solariun experience consolidation relocated those
surfaces, so 6 of the file's 9 nodes asserted mounts that no longer exist.

Per the workstream ledger this is **not** a string-repoint job. The `_block(view)` helper
regex-matched a parenthesised JSX expression
(`{view === '<v>' && (\(.*?\)\n\)}`) against `App.tsx`, but `App.tsx` no longer uses that
shape: each view is mounted inline as a single JSX element, and several legacy ids are
resolved through `handleNavigate` redirect rules rather than mounts. The helper therefore
raised `AssertionError: view block not found for loops`.

Files changed: `tests/test_prism_pass_c_surface_ownership.py` **only**.

| node | prior claim (now false) | repair |
|---|---|---|
| `test_spiral_codex_uses_feed_component` | helper could not extract the block | block extracted from the inline mount |
| `test_spiral_codex_not_solspire_field` | same | same |
| `test_echo_field_aliases_resolve_to_solspire_field` | echo-field → `SolSpireConsole initialSection="field"` | echo-field is a **live mount** (`UniversalEchofeildMatrix`) **and** a redirect alias to `solariun` + `observatory` |
| `test_nav_echo_field_opens_solspire` | nav targets `view: 'solspire'` | nav targets `view: 'personal-echofeild'` |
| `test_knowledge_os_resolves_to_solspire_knowledge` | `SolSpireConsole initialSection="knowledge"` | `SolariunConsole initialSection="knowledge"` |
| `test_codex_resolves_to_knowledge_lens` | `SolSpireConsole initialSection="codex"` | mount is `SolariunConsole initialSection="knowledge"`; redirect rule maps `codex → solariun` + `section:'knowledge'` — i.e. the **knowledge** lens (see §3.4) |
| `test_loops_resolves_to_solspire_loops` | `SolSpireConsole initialSection="loops"` | redirect to `solariun` + `tasks`; `SolariunConsole` maps `loops → tasks` |

Surfaces the repair asserts, read from live source:

- `App.tsx` — inline `{view === '<id>' && <motion.div …>}` mounts; `handleNavigate` redirect
  rules for retired ids.
- `web/public_prism/src/pages/SolariunConsole.tsx` — `LEGACY_MAP`
  (`codex:'memory'`, `loops:'tasks'`, `field:'overview'`); the `field` lens is retired and
  now maps to `overview`. Note `knowledge` is **not** a `LEGACY_MAP` key, so a
  `section:'knowledge'` passes through unchanged — see §3.4.
- `web/public_prism/src/components/ArkadiaNavigation.tsx` — the six-anchor vertical drawer.

## 1a. Base and attribution (corrected this pass)

An earlier draft of this file recorded `BASE_MAIN = ee3fac1`. That was wrong: `ee3fac1` is
the **batch-1** merge (PR #124); batch 2 landed as PR #125 on top of it. The repository checkout already contained
that batch-2 merge
(PR #125), so this branch was cut from `417d32d` (PR #126, GATE L1 native agent runtime) and
`ee3fac1..417d32d` carries the batch-2 evidence and that lab runtime change. The correction
is recorded here rather than force-pushed away (force-push is forbidden).

Because PR #126 merged mid-pass, the endorsed baseline fingerprint was **re-measured at the
true base** and the delta re-attributed, rather than reusing the earlier numbers:

```
base 417d32d (clean worktree) : 45 failed / 985 passed / 13 skipped / 2 errors   (47 nodes)
+ this repair (branch head)   : 39 failed / 991 passed / 13 skipped / 2 errors   (41 nodes)

removed : the same 6 nodes as §3a, all in test_prism_pass_c_surface_ownership.py
added   : (none)
```

The two independent measurements agree on both counts and node identity: re-measuring at the
true base changes **nothing** about the claim, it only removes the possibility that the delta
was inherited from a commit that landed between surfaces. None of this repair's target
surfaces moved between `ee3fac1` and `417d32d`.

Note also that a local branch `gate-hygiene/prism-pass-c-helper-rewrite-01` points at
`417d32d` and was never pushed — it is a stale local ref, not a competing PR. No duplicate
work exists on the remote.

## 2. The two mechanisms, kept distinct

The prior file assumed every claim was a mount. After consolidation a legacy id resolves by
exactly one of two mechanisms, and the repair asserts whichever one actually holds:

1. **Live mount** — `_block(view)` extracts the inline JSX for that id and the node asserts
   on the mounted component.
2. **Redirect rule** — `_redirect(view)` extracts the `handleNavigate` rule that mentions the
   id and the node asserts the `view`/`section` target, plus (where the id is legacy) the
   `LEGACY_MAP` entry in `SolariunConsole.tsx` that maps it to its lens.

For `personal-echofeild` / `echofeild-matrix` **both** hold, and the node asserts both.

## 3. Helper hardening (this pass)

`_block` carries a deliberate boundary guard:

```python
assert "{view === " not in block, f"block extraction crossed a view boundary for {view}"
```

A non-greedy `.*?` whose closing token is absent will swallow the following blocks and
return a *different* view's markup — every content assertion would then pass vacuously.
The guard converts that silent mis-extraction into a loud failure. §3.3 (NC1) proves it
fires on text that reproduces the crossing.

## 3a. Verification

Full suite measured twice on the same environment (identical runner, same `pyyaml` +
`PYTHONPATH=<repo>/archive/legacy_python`), comparing **sorted node lists by name**, never
counts alone: counted delta first on clean `main`, then with the repair applied.

```
clean main (BASE_MAIN ee3fac1) : 45 failed / 985 passed / 13 skipped / 2 errors   (47 nodes)
+ this repair                  : 39 failed / 991 passed / 13 skipped / 2 errors   (41 nodes)

removed (6, exactly the target nodes):
  test_prism_pass_c_surface_ownership.py::test_codex_resolves_to_solspire_codex
  test_prism_pass_c_surface_ownership.py::test_echo_field_aliases_resolve_to_solspire_field
  test_prism_pass_c_surface_ownership.py::test_knowledge_os_resolves_to_solspire_knowledge
  test_prism_pass_c_surface_ownership.py::test_loops_resolves_to_solspire_loops
  test_prism_pass_c_surface_ownership.py::test_spiral_codex_not_solspire_field
  test_prism_pass_c_surface_ownership.py::test_spiral_codex_uses_feed_component
added   : (none)   → zero new failures
```

Targeted file, before → after: `6 failed / 3 passed` → `9 passed`.

Protected regressions:

```
tests/architecture                       : 11/11 passed
CP10 mutation boundary (dry judge)       : PASS  (exit 0)
python -m py_compile api/main.py         : pass  (api/main.py = 2519 / 2600 lines)
vite build                               : environment-blocked (no npm registry access)
```

`git status --porcelain` in the working tree shows **only**
`tests/test_prism_pass_c_surface_ownership.py` modified — no frontend/source file is
touched by the negative controls (verified after the run).

## 3.3 Negative controls (every repaired node must still be able to fail)

Each control mutates the live source, runs the file, then restores it. An automated
mutation-anchor check verifies the mutation actually applied, so a no-op edit cannot be
mistaken for a passing control. `NC9` re-runs after restore and `git diff` confirms the
source tree is clean.

| # | mutation | result (expected) |
|---|---|---|
| NC0 | none (baseline) | 9 passed |
| NC1 | boundary guard on synthetic crossing text | `GUARD-RAISED` |
| NC2 | `SolariunConsole` `field:'overview'` → `field:'field'` | 1 failed |
| NC3 | `SolariunConsole` `codex:'memory'` → `codex:'knowledge'` | 1 failed |
| NC4 | `SolariunConsole` `loops:'tasks'` → `loops:'overview'` | 1 failed |
| NC5 | echo-field redirect retargeted `solariun`/`observatory` → `solspire`/`field` | 1 failed |
| NC6 | `knowledge-os` mount `SolariunConsole` → `SolSpireConsole` | 1 failed |
| NC7 | nav `Echo Field` `{view: 'personal-echofeild'}` → `{view: 'solspire'}` | 1 failed |
| NC8 | `spiral-codex` unmounted (`SpiralCodexFeed` → `NexusSpiralCodex`) | 2 failed |
| NC9 | restored | 9 passed, source clean |

**Honest correction to the control set.** The first attempt at NC1 was "wrap the
`spiral-codex` mount in parentheses" expecting the newly permissive `\(?` to break
extraction. It did not fail (9 passed), and on inspection that control was **vacuous, not
the assertion**: every block's asserted strings are unique to it, so a non-parenthesised
match still lands on the correct block. The `\(?` therefore adds nothing for the current
`App.tsx`. It is retained as harmless future-proofing only, and NC1 was rewritten to
exercise the boundary guard directly on text that genuinely reproduces a crossing — which
is what the guard is for. The guard is a defence against a future block whose closing token
disappears, not a fix for an observed mis-extraction.

## 3.4 Correction — `codex` lands on `knowledge`, not `memory` (this pass)

The `codex` node repaired above was correct in what it *asserted* but wrong in what it
*claimed*. Its docstring read "`SolariunConsole` maps codex -> memory, so the legacy id lands
on the project-memory lens". That is false, and it was false when written.

Live source, read this pass:

- `App.tsx` `handleNavigate`: `if (requested === 'knowledge-os' || requested === 'codex') next = {view:'solariun',section:'knowledge',…}`
- `App.tsx` mount: `{view === 'codex' && … <SolariunConsole … initialSection="knowledge" />}`
- `SolariunConsole.tsx`: `LEGACY_MAP = {field:'overview',codex:'memory',loops:'tasks',…}` and
  `initialSection={(LEGACY_MAP[initialSection]||initialSection) as SolSpireLens}`

`knowledge` is not a `LEGACY_MAP` key, so `LEGACY_MAP['knowledge']` is `undefined` and the
`||` fallback yields `'knowledge'`. **`codex` resolves to the knowledge lens.** The
`codex:'memory'` row describes the *pre-consolidation* meaning of the bare `codex` lens id;
it is not reachable from the `codex` `View` id, which is now rewritten before it ever reaches
`SolariunConsole`.

The assertion `re.search(r"codex:'memory'", …)` was therefore a **declaration-inventory
check** — it proved the row exists in the file, not that codex routes through it. Left
unqualified, it would have re-established exactly the class of stale claim this workstream
exists to remove.

Repair in this pass (test file + this document):

- Renamed the node `test_codex_resolves_to_knowledge_memory_lens` →
  `test_codex_resolves_to_knowledge_lens` (name matched the false claim).
- Docstring rewritten to state the real route and to label the `LEGACY_MAP` assertion as
  inventory, not routing.
- **Added** the two assertions that actually bind codex's route: the `codex` redirect rule
  flattens to `view:'solariun'` + `section:'knowledge'`. These are the teeth the node lacked.

Node-name safety: no other file in the repository referenced the old node name (checked with
`grep -rn` across `*.py` / `*.md` outside this file) — nothing else depends on the rename.

### Negative controls added (NC-A, NC-B, NC-C)

| # | mutation | result (expected) | result (observed) |
|---|---|---|---|
| NC-A | `codex` redirect `section:'knowledge'` → `section:'overview'` | 1 failed | 1 failed |
| NC-B | `codex` mount `initialSection="knowledge"` → `initialSection="overview"` | 1 failed | 1 failed |
| NC-C | `knowledge-os` redirect `section:'knowledge'` → `section:'overview'` | 1 failed | 1 failed |
| restore | — | 9 passed | 9 passed, `git status` clean |

NC-A/NC-B are the teeth the `codex` node lacked; NC-C is the teeth the `knowledge-os` node
lacked. Each was verified to have actually applied to the source before the run, so none is a
vacuous control (the §3.3 technique). NC3 remains valid — it mutates `LEGACY_MAP
codex:'memory'` and fires on the inventory assertion, which is now labelled as inventory
rather than routing, so the two assertion kinds are distinguishable where before they were not.

### Regression boundary

Measured back-to-back on the same runner, `PYTHONPATH=<repo>/archive/legacy_python`:

```
PR #127 head (A)                  : 41 failing/error nodes | 39 failed, 991 passed, 13 skipped, 2 errors
PR #127 head + this correction (B): 41 failing/error nodes | 39 failed, 991 passed, 13 skipped, 2 errors
diff A B                          : (identical)  -> 0 nodes moved
target file                       : 9 passed
architecture                      : 11/11
protected set                     : 71 passed
py_compile api/main.py            : pass (2519 / 2600 lines)
CP10 mutation boundary judge      : PASS (exit 0)
```

Attribution was done by **sorted node name**, not by count, per the workstream rule. No
source, policy, governance, or architecture file is touched by this correction.

## 4. Findings recorded, not acted on (no self-expansion)

These were observed while establishing ground truth. They are **out of scope** here and are
recorded so the next heartbeat does not rediscover them; none were changed.

- **`knowledge-os` — an earlier revision of this file got this backwards.** It claimed the
  legacy id has **no** `handleNavigate` rule and reaches the knowledge lens "only through its
  inline mount". That is false: the `knowledge-os` literal is present in `App.tsx` four
  times, including a grouped redirect rule
  (`if (requested === 'knowledge-os' || requested === 'codex') next = {view:'solariun',section:'knowledge',…}`)
  and a `'/knowledge-os'` path-table entry. The node asserted the mount only, so it
  under-described the route and the finding was wrong. Corrected this pass — the node now
  asserts both mechanisms (see §3.4). **There is no dead-id / DRIFT finding here**; the
  `SH-02c` row in `WORKSTREAM_STATE.md` is withdrawn.
- **`test_nav_echo_field_opens_personal_echofeild`** was renamed from
  `…_opens_solspire` to match its assertion; it was *passing* before (its assertion was
  already true), so it is not part of the 6-node delta.
- `vite build` cannot run in this sandbox, so the frontend assertions remain
  source-level and inspection-verified only, consistent with repo convention.

## 5. Authority boundary

Test-only. No change to `api/main.py`, `LAYER_MAP.py`, ADRs, policy modules, workflows, or
governance files. `REGISTERED_ARCHITECTURAL_DEBT` untouched. Nothing merged; the sovereign
decides what becomes canonical.