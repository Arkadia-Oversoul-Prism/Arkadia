# Baseline reproducibility preflight (gate-hygiene)

**Workstream:** GATE-10 / gate-hygiene — baseline-fingerprint reproducibility
**Branch:** `gate-hygiene/baseline-reproducibility-preflight-01`
**BASE_MAIN:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Status:** OBSERVED (implementation + tests pass; not merged — human merge required)

## 1. Defect

The documented reproduction command for the baseline test-debt fingerprint

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
    --continue-on-collection-errors -rEf
```

run **verbatim** in a shallow clone yields **21** failing/error nodes, while the
canonical recorded set is **16**. Nothing in the command is wrong. The
*environment* is wrong, and no gate names the precondition.

Two environment properties silently change the node set:

1. **Clone depth.** `tests/test_agents_md_encoding_adjudication.py` resolves its
   oracle with `git show <ORACLE_REV>:AGENTS.md` (`ORACLE_REV = 6c43218a48a4`,
   from `scripts/agents_md_encoding_audit.py`). When the revision is absent the
   live-file tests **error rather than skip**, adding four nodes. Measured:
   same file, shallow clone → **4 failed, 13 passed**; full clone → **0 failed,
   18 passed**. The four are:
   `test_live_file_verdict_matches_its_state`,
   `test_corruption_origin_is_re_derivable`,
   `test_cli_summarises_the_oracle_without_crashing`,
   `test_exit_code_does_not_call_a_divergent_clean_file_verified`.
2. **Missing declared dependency.** `requirements.txt` is the contract. Measured
   on the two explicitly-declared-as-contract deps:
   - `pdfminer.six` absent → `test_market_data.py::`
     `test_nepc_unparseable_pdf_fails_closed_at_fetch_boundary` fails on import.
   - `pytest-asyncio` absent → async tests collect but never await; three passing
     boundary nodes turn into failures
     (`test_authority_api_enterprise_boundary.py::`
     `test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`,
     `test_arkana_signal_schema_guard.py::test_route_emits_a_conforming_signal`,
     `::test_route_normalizes_ordinary_model_output`).

Measured, these two properties fully account for the 21→16 delta. A third
property sometimes assumed to matter — `PYTHONPATH` — does **not**: the suite
reports the identical 16-node set with and without `archive/legacy_python` on the
path.

## 2. Delivered: `scripts/baseline_preflight.py`

Read-only, stdlib-only, no test execution, no mutation, never prints a token. It
probes, before a fingerprint is derived:

| probe | consequential? | source of truth |
|---|---|---|
| clone shallow / oracle revision resolvable | yes | `git rev-parse --is-shallow-repository`, `git cat-file -e <ORACLE_REV>` |
| declared requirements importable | yes for `pdfminer.six`, `pytest-asyncio` | `requirements.txt` + `importlib.util.find_spec` |
| `weaver.autonomy` module-vs-package collision (CE-01) | report-only | filesystem |

Design notes:
- `ORACLE_REV` is **imported** from `scripts/agents_md_encoding_audit.py`, not
  restated — the preflight cannot drift from the test it describes.
- Requirements are parsed from the real `requirements.txt`, with extras/pins
  normalised. Names with no import mapping are reported as `retained`, so an
  unchecked requirement is never treated as satisfied.
- Exit status: `0` no blocking finding, `1` a finding that would change the node
  set, `2` usage/IO fault. `--json` for machine output.
- A probe that cannot run (subprocess/OSError) fails **closed** (treated as
  shallow), so an unprobeable environment is never reported clean.

## 3. Proof

- **Guard:** `tests/test_baseline_preflight.py` — **16 passed**, network-free.
  It exercises the git probes against real throwaway repositories (full clone,
  `--depth 1` clone, absent revision), the requirement parser (absent mapped
  module, unmapped name retained, comments/extras ignored), and `collect()` under
  pinned probes (clean / shallow / consequential / non-consequential).
- **Negative control:** `test_negative_control_naive_probe_misses_the_shallow_clone`
  feeds the *naive* environment check (trusts the constant is configured, never
  resolves the revision) the same shallow clone and asserts it reports
  reproducible while the real probe bites. The harness cannot be gutted to a
  constant-`True` check without this node failing.
- **Live negative control (measured, manual):**
  `git clone --depth 1 file://<repo> /tmp/shallow_demo` then
  `python scripts/baseline_preflight.py --repo /tmp/shallow_demo` →
  `clone shallow: True`, `oracle … : ABSENT`, `[BLOCKING] SHALLOW_CLONE`,
  **exit 1**. On the full clone the same command → **exit 0**.

## 4. Regression boundary

| measurement | main `f9ced6b6` | branch | delta |
|---|---|---|---|
| failing/error node **set** | 16 (15F/1E) | 16 (15F/1E) | **none** |
| outcomes fingerprint | `bfcfe592…` | `bfcfe592…` | identical |
| ids fingerprint | `ed5e4714…` | `ed5e4714…` | identical |
| architecture fitness | 11 passed | 11 passed | none |
| full-suite passed | 1854 | 1870 | **+16** = the new guard suite |
| CP10 mutation-boundary judge | — | PASS (RC 0) | — |

`api/main.py` is **untouched** (`git diff --name-only main...HEAD | grep -c
api/main.py` → 0).

Re-measured after the wiring commit, `main` in a clean detached worktree at
`f9ced6b6` and the branch tree side by side, same command, same environment:

| measurement | main `f9ced6b6` | branch | delta |
|---|---|---|---|
| failing/error node **set** | 16 (15F/1E) | 16 (15F/1E) | **none** |
| node-set sha256 | `facc29a91e12fa34…` | `facc29a91e12fa34…` | identical |
| full-suite passed | 1854 | 1870 | **+16** = the new guard suite |

The `+16` is the new guard suite's own nodes; the failing/error node *set* is
byte-identical, which is the load-bearing claim. Counts alone are not.

## 5. CI wiring — the guard is executed, not decoration

As introduced, `grep -rn baseline_preflight .github/workflows/` returned **0**: the
preflight and its guard suite held only when a human invoked them by hand. The
repository already names that defect class — *a guard no workflow executes is
decoration* — and closed it once for `tests/test_baseline_fingerprint.py`
(`.github/workflows/baseline-fingerprint.yml`). This pass closes it for the preflight.

Added:

- `.github/workflows/baseline-preflight.yml` — runs
  `pytest tests/test_baseline_preflight.py tests/test_baseline_preflight_ci_wiring.py`,
  `fetch-depth: 0` (a shallow checkout here would make the gate's own environment
  indistinguishable from the defect it detects).
- `tests/test_baseline_preflight_ci_wiring.py` — states the invariant generically over
  every workflow that runs the guard: (1) some workflow must run it, selected on
  `pull_request` by the guard file and **every input the script reads**; (2) full
  history; (3) the guard step must be able to fail the job.

**The input set is derived, not restated.** The script's inputs are read from
`scripts/baseline_preflight.py` by AST: `from scripts.<module> import …` (it imports
`ORACLE_REV` from `scripts/agents_md_encoding_audit.py`, a module the guard suite never
names) and `<CONST> = REPO_ROOT / "<name>"` (`requirements.txt`). A hand-maintained copy
would drift and make the coverage assertion vacuous. Accepted consequence: adding an
import or a repo-root path literal to the script requires adding the same path to the
workflow filter in the same change.

### Proof (negative controls)

| control | action | result |
|---|---|---|
| wiring removed | `mv .github/workflows/baseline-preflight.yml /tmp` | `test_a_workflow_executes_the_preflight_guard` **FAILED** (5 passed, 3 skipped) |
| input dropped from filter | delete `- "requirements.txt"` | `test_guard_workflow_is_selected_by_every_input[baseline-preflight.yml]` **FAILED** (8 passed) |
| restored | both reverted | **9 passed** |
| guard suite | `pytest tests/test_baseline_preflight.py tests/test_baseline_preflight_ci_wiring.py -q` | **25 passed** |
| live preflight | `python scripts/baseline_preflight.py` | full clone → 0 blocking findings, **exit 0** |

The generic CI-scanner suites gain passing nodes by construction (three iterate
`.github/workflows/*.yml`); measured together: **189 passed**, with the only 3 failures
being the pre-existing CP10 `deploy/n-atlas-server/` allowlist omission, reproduced on
`main` itself (see §4). `tests/test_ci_gate_trigger_coverage.py::`
`test_push_and_pull_request_filters_are_identical` passes: the new workflow's `push` and
`pull_request` filters are identical, as that guard requires.

### Runtime proof (the wiring is executed, not merely present)

Wiring is no longer a source-level claim. At head `d4f07881` the workflow ran under
CI: run **`38001869735`**, `event=pull_request`, `status=completed`,
`conclusion=success`, `headSha=d4f0788103ac1355506c389005ce57884f66192b`. All **7**
check-runs on that commit are `completed/success`, including `baseline-preflight` and
`Full-history secret scan`.

## 6. Authority boundary

A read-only preflight script and its guard test. No merge, no push to `main`, no
authority/mutation/identity path touched, no scope expansion. `AGENTS.md`
untouched. **Human merge required.**

## 6. Remaining uncertainty / adjacent, NOT performed here

- **Fixture reconciliation** (PASS-3 §8) — `tests/fixtures/baseline_node_set.txt`
  records 10 nodes while a live run reports 16. This branch does **not** touch it.
  Six of the live nodes are owned by open PRs (CP10 `deploy/` omission → PR #354;
  three unowned drift). Re-pinning the fixture before those merge would make it
  immediately stale. It remains a separate bounded task.
- **`tests/test_market_data.py` import style** — `import pdfminer.high_level`
  without `pytest.importorskip` means the declared dep is assumed, not guarded.
  Proposing it is scope beyond this pass; recorded only.
- **The 4 adjudication tests error rather than skip in a shallow clone.** Whether
  a skip is preferable is a test-side design question owned by the
  encoding-adjudication workstream; this pass makes the precondition visible
  instead of changing the tests.
- Gate 2 production parity remains `BLOCKED` on Vercel Deployment Protection;
  unchanged by this pass.
