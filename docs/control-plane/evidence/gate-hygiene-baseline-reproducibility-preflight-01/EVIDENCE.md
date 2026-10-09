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

## 5. Authority boundary

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
