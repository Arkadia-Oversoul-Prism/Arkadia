# GATE-10 / CP10 — Boundary Continuity — Evidence

**Gate:** GATE-10 (Governed Execution) — CP10 mutation boundary / M02A CI gate integrity
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `8843fd589f62eebea7815367e2e37f2648ca758e`
**Branch:** `gate10/cp10-boundary-continuity-01`
**Status:** VERIFIED (tests + runtime inspection); merge is human-only.

## 1. Objective (bounded)

Make agent-facing memory in the repository agree with the boundary the repository actually
executes, and leave the next heartbeat a state file it can reconstruct from.

The `gate10/cp10-delegated-boundary-judge` pass (PR **#120**, merged as `8843fd5`) removed the
inline `legit=` allowlist from `sg-02-fe-2-v.yml` and replaced it with
`python scripts/cp10_mutation_boundary_policy.py --judge`. `AGENTS.md` was not updated by that
pass and still instructed future agents that:

- the allowlist "is written twice" and that the two copies "**must stay in sync**";
- the "workflow mirror must agree with the policy module";
- keeping "the shell literal only as a mirror assertion" was the recommended structural fix.

Each of those statements is now false, and the last one describes the state the fix deliberately
reversed. This is a documentation-continuity defect, not an architecture change.

## 2. Scope

In scope — one existing file plus this evidence bundle:

- `AGENTS.md` — the CP10 / GATE-10 block only.
- `docs/control-plane/evidence/gate10-cp10-boundary-continuity-01/` (this file and
  `WORKSTREAM_STATE.md`).

Out of scope, explicitly:

- `scripts/cp10_mutation_boundary_policy.py` — the policy itself is **not** touched. No path was
  added to or removed from `LEGIT`.
- `.github/workflows/sg-02-fe-2-v.yml` — not touched.
- The `forbid` stage (constitutional `SolSpireExperienceV2/V3.tsx`), the unknown-root rejection
  stage, and the no-autonomy assertions — not touched.
- `api/main.py` — not touched; remains 2519 lines against a 2600 budget
  (`python -m py_compile api/main.py` → OK).
- Pre-existing baseline test debt — not touched. See §5.

## 3. What changed

Two passages in `AGENTS.md`, both now stating the single-copy reality:

1. The "written twice / must stay in sync" bullet became "**the allowlist is written once**",
   naming `--judge` as the execution path, recording that the duplication was removed in the
   `gate10/cp10-delegated-boundary-judge` pass, and warning against reintroducing a shell-side
   copy — which `tests/test_m02a_ci_gate_integrity.py` asserts the absence of.
2. The "workflow mirror must agree with the policy module" clause was dropped from the invariant
   statement; the surviving invariant is that every path in `git ls-files` must be admitted by
   the policy module, asserted against the live tracked corpus.

No executable line changed, so the change cannot alter the gate's verdict.

## 4. Evidence

Verified on this branch at BASE_MAIN `8843fd5`:

```
python -m pytest tests/test_m02a_ci_gate_integrity.py tests/architecture -q
  -> 60 passed in 1.45s

python -m py_compile api/main.py
  -> OK   (api/main.py = 2519 lines, budget 2600)
```

Single-copy confirmation — the only surviving allowlist definition is the policy module; the
only remaining `legit=` occurrence in the repository is the test that asserts its absence from
the workflow:

```
scripts/cp10_mutation_boundary_policy.py:35:  LEGIT = re.compile(
tests/test_m02a_ci_gate_integrity.py:160:    assert not re.search(r"^\s*legit='", text, ...)
tests/test_m02a_ci_gate_integrity.py:161:        "the hand-maintained `legit=` regex is the drift defect; ..."
```

The workflow's mutation step reads:

```
if ! printf '%s\n' "$changed" | python scripts/cp10_mutation_boundary_policy.py --judge; then
```

## 5. Baseline comparison and remaining uncertainty

| | `main` @ `8843fd5` | this branch |
|---|---|---|
| `tests/architecture` + M02A gate test | — | **60 passed** |
| failure fingerprint | unchanged | unchanged — no executable code touched |
| `api/main.py` | 2519 lines | 2519 lines |

Remaining uncertainty, stated rather than hidden:

- This pass changes prose only. It is not claimed to alter any test outcome, and it does not.
- The contract's recorded baseline (`804 passed / 54 failed / 12 skipped / 2 collection errors`
  @ `6038989`) is anchored behind the current `main`; the **failure fingerprint**, not the raw
  count, is the attribution unit. Two pre-existing collection errors
  (`test_autonomy.py::load_autonomy_config`, `test_render_codex.py::arkadia_drive_sync`) remain
  untouched baseline debt.
- `.bootstrap/01_STATE.md` and `.bootstrap/03_SCOPE.md` are **stale**: they still describe K5
  static ingestion as pending, but K5 is merged (PR #109) as recorded in `AGENTS.md`. This pass
  does not edit them — rewriting bootstrap prose is its own bounded task. The staleness is
  recorded here and in `WORKSTREAM_STATE.md` so the next heartbeat does not act on it.
- A full-suite fingerprint run was **not** re-executed this pass; the change is non-executable,
  so the fingerprint is carried forward unchanged rather than re-derived. It is the next
  heartbeat's first reconstruction input if any executable change is proposed.

## 6. Authority boundary

No merge, no authorization, no identity change, no new mutation path, no new authorization path.
`OPENHANDS` implemented, tested, committed, branched, pushed, and opened a PR. Merge is reserved
to the human sovereign.
