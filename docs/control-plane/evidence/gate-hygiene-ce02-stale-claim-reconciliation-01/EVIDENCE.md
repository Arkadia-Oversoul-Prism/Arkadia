# EVIDENCE — gate-hygiene · CE-02 stale-claim reconciliation

**Workstream:** `gate-hygiene` (repository-truth reconciliation)
**Gate:** GATE-01 (canonical authorship — narrative/evidence truthfulness)
**Pass:** 1
**Class:** docs-only (narrative correction + evidence). No source, test, governance, or boot file modified.

---

## 1. Objective

Correct three **stale claims** in the repository's own persistent memory (`AGENTS.md`) that
were carried forward as fact and would otherwise mislead the next pass:

1. `vite build` is "environment-blocked (no npm registry access)".
2. `ActivityRuntime` (SG-04) is "absent from the production bundle … not yet fixed".
3. Full-suite reproducibility yields "exactly the documented **2** collection errors
   (`test_autonomy.py` …, `test_render_codex.py` …)".

Each is contradicted by live, re-derived evidence below. The claim classes were already
flagged for correction by PR #149 ("the *explanation* is wrong and has been propagated into
`AGENTS.md` … not edited here — recorded for the sovereign") and by the CE-01 disposition
("`vite build` | environment-blocked … unchanged"). This pass performs the recorded handoff.

**Non-goals / not re-litigated:** the CE-01 `weaver.autonomy` module-vs-package collision is
**not** adjudicated. It is a governance question reserved to the sovereign and is recorded
here only as the one remaining collection error.

---

## 2. Start state (live, not prose)

| item | value | source |
|---|---|---|
| canonical repo | `Arkadia-Oversoul-Prism/Arkadia` | remote |
| branch | `main` | `git` |
| **BASE_MAIN** | **`0c8a9f6276354fc2eb8c9a3da805d0878946abc7`** | `git log -1 origin/main`; GitHub `commits/main` agree |
| HEAD commit | `fix(android): restore Oracle backend connectivity` (2026-10-02 11:04 +0100) | `git log -1` |
| open PRs | **0** | GitHub `pulls?state=open` |
| `tests/architecture` | **11 / 11 passed** | live run |
| `api/main.py` | `py_compile` clean; **2571** lines (budget 2600) | live |
| full suite | **20 failed / 1252 passed / 17 skipped / 1 error** | `pytest tests/ -q --continue-on-collection-errors` |
| fingerprint | `a59453b8…` / `9a35c812…`, **21 nodes** | `scripts/baseline_fingerprint.py` |

Credential: the ambient `github_token` authenticated (repo `push: true`, `admin: true`);
`GITHUB_PERSONAL_ACCESS_TOKEN` returned 401 and was not used.

---

## 3. Claim 1 — `vite build` is NOT environment-blocked

**Stale text (before):** `vite build` is environment-blocked (no npm registry access), so
changes are inspection-verified only unless the sandbox has `node_modules`.

**Measured:** the npm registry is reachable (HTTP 200) and a clean install + build succeeds:

```
$ corepack pnpm install      # node v24.21.0, pnpm 10.26.1
$ corepack pnpm build
✓ 3441 modules transformed.
dist/assets/index-*.js … emitted
exit 0
```

`pnpm`'s own activation symlink hit `EACCES`; `corepack pnpm` works and is the documented
invocation. The `dist/assets/` output is generated and **untracked** (`.gitignore` covers
`dist/`), so no build artifact is committed.

**Verdict:** the blocked claim is **stale**. Corrected to instruct future passes to attempt
the build and report the measured result.

---

## 4. Claim 2 — SG-04 `ActivityRuntime` absence was real, and is repaired in source

**Stale text (before):** "`ActivityRuntime` (SG-04) is absent from the production bundle …
`tests/test_spiral_grove_activity_runtime.py` is **4F/8P** … Not yet fixed".

**Measured at `0c8a9f6`:**

| check | result |
|---|---|
| `tests/test_spiral_grove_activity_runtime.py` | **12 passed** (was 4F/8P) |
| `CapabilityChamber.tsx` | imports `useEffect` (line 1), imports `ActivityRuntime` (line 4), **renders** it (line 58); `surfaceMeta` anchor present |
| marker `activity-runtime-draft.v1` in `src/` | present (`ActivityRuntime.tsx:4`) |
| marker in a clean local build | **1 occurrence** (was 0 in the deployed asset) |
| repair carrier | PR **#185** merged, merge commit `52973d9987…` |

**Boundary that must not be overstated:** the *production* bundle will carry the mount only
once a deployment ships post-#185 source. Deployment identity and runtime observation remain
the open Gate-2 boundary (`gate-hygiene-gate2-production-parity-02`). This pass makes a
**repository-source** claim only, not a production-parity claim.

**Verdict:** the "not yet fixed" claim is **stale**; the historical observation was accurate
for its revision and is preserved with its date/context.

---

## 5. Claim 3 — there is ONE collection error, not two

**Stale text (before):** "with those the suite yields exactly the documented **2** collection
errors (pre-existing: `test_autonomy.py` `load_autonomy_config`, `test_render_codex.py`
`arkadia_drive_sync`)".

**Measured at `0c8a9f6`:**

```
$ python -m pytest tests/ -q --continue-on-collection-errors
20 failed, 1252 passed, 17 skipped, 1 error
ERROR tests/test_autonomy.py
```

- `tests/test_render_codex.py` **does not exist**. `git ls-files tests/` returns only the
  non-collected `tests/render_codex_probe.py` (renamed by `00271b2` "Correct render codex test
  collection naming"). The `arkadia_drive_sync` half of the pair is therefore not merely
  fixed — it is **absent**.
- The single remaining error is CE-01: `from weaver.autonomy import load_autonomy_config` →
  `ImportError`, because the `weaver/autonomy/` package shadows the `weaver/autonomy.py`
  module that defines the symbol. `weaver/session_kernel.py:11` imports
  `.autonomy.guard`, so un-shadowing is not a neutral repair — this is the **sovereign
  decision** already recorded in `gate-hygiene-ce01-autonomy-collision-disposition-01`.

**Reproducibility note also corrected:** without `--continue-on-collection-errors`, a bare
`pytest tests/` **interrupts** at the collection error (exit 2) and under-reports the run.
The reproducibility command in `AGENTS.md` now names the flag.

**Verdict:** the "two collection errors" pairing is **stale**. The corrected figure matches the
recorded baseline fingerprint exactly.

---

## 6. Baseline / regression evidence

Fingerprint comparison — the attribution unit is the **node set**, not the raw count:

| | recorded baseline | this pass at `0c8a9f6` |
|---|---|---|
| failing/error nodes | 21 | 21 |
| outcomes fingerprint | `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` | **identical** |
| ids fingerprint | `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` | **identical** |

**Zero regression.** The 20 failures + 1 error are pre-existing `main` debt, unchanged and not
addressed here. `AGENTS.md` is prose; no node depends on it. Confirmed by re-running the three
`AGENTS.md`-reading tests after the edit:

```
tests/test_agents_md_repair_fingerprint.py
tests/test_m02a_ci_gate_integrity.py
tests/test_engineering_lab.py
→ 59 passed
```

Encoding integrity of `AGENTS.md` preserved after the edit: Cyrillic/mojibake count **0**.

---

## 7. Files changed

| path | change |
|---|---|
| `AGENTS.md` | 3 stale claims corrected + insertion-only invariant recorded (33 insertions, 9 deletions vs `main`; **0 alterations vs oracle**) |
| `docs/control-plane/evidence/gate-hygiene-ce02-stale-claim-reconciliation-01/EVIDENCE.md` | this artifact |
| `docs/control-plane/evidence/gate-hygiene-ce02-stale-claim-reconciliation-01/WORKSTREAM_STATE.md` | state/next-action |

`AGENTS.md` is admitted by CP10 `LEGIT` (`LEGIT.search('AGENTS.md') is True`) and is **not** in
`FORBID_V2`/`FORBID_V3`. No protected, constitutional, boot, or governance file is touched.

---

## 7a. Method correction — the edit must be insertions-only over the oracle

The first attempt applied the three corrections **in place**. That is a regression, and the
mechanism is not obvious from the rendered file:

- `scripts/agents_md_encoding_audit.py` audits the **working tree** against oracle
  `6c43218a48a4` and requires the recovered text to relate to it by **insertions only**
  (`oracle_alterations == []`).
- One of the three stale claims — the "exactly 2 collection errors" sentence — sits on an
  **oracle line** (`AGENTS.md:233–234` at `6c43218a48a4:216–217`). Rewriting it produced
  `alterations=1` → `decidable=False` → CLI **exit 2**, breaking
  `test_live_file_verdict_matches_its_state` and `test_cli_summarises_the_oracle_without_crashing`.

Measured delta from the in-place attempt (the fingerprint change the pass must avoid):

| | in-place rewrite | insertions-only (this PR) |
|---|---|---|
| `agents_md_encoding_audit.py` | `alterations=1`, `decidable=False`, exit **2** | `alterations=0`, `oracle_reproduced=True`, exit **1** |
| `test_agents_md_encoding_adjudication.py` | 4F / 15P | **2F / 17P** (baseline) |
| full-suite fingerprint | `f1c7c0c3…` / 23 nodes | **`a59453b8…` / 21 nodes** (baseline) |

**Repair:** the oracle-line claim is now corrected by an **appended, dated** insertion
("Measured at `0c8a9f6`: **1** collection error … supersedes the above") instead of a rewrite;
the two post-oracle claims are edited directly, which the invariant permits. Net diff is
33 insertions / 9 deletions against `main` while `alterations` against the oracle stays **0** —
i.e. every deletion is on a post-oracle line.

The invariant is recorded in `AGENTS.md` itself so a future pass does not repeat the mistake.

---

## 8. Remaining uncertainty

- Production runtime observation (Gate-2) is untouched — this is repository-source evidence.
- The 20 pre-existing failures are unattributed by this pass; they are baseline debt.
- CE-01 awaits the sovereign autonomy-shape decision; it is deliberately left red.

## 9. Authority boundary

Docs-only. No merge, no push to `main`, no force-push, no self-authorization, no identity or
authority-model change, no new mutation/authorization path, no scope expansion.

**READY_FOR_SOVEREIGN_MERGE.** Human-only merge.
