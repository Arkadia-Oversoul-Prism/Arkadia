# Engineering Lab event log — an unsandboxed runtime path inside the working tree

Bounded repo-hygiene repair. No authority surface, no application behaviour change, no
merge, no deployment.

- **BASE_MAIN** := `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
- **Measured** 2026-11-22, canonical clone (`is-shallow-repository` -> `false`),
  pytest 9.2.0 / Python 3.13.15.
- **Branch** := `gate-hygiene/engineering-lab-event-log-sandbox-01`
- **Files changed** := `.gitignore`, `conftest.py`,
  `tests/test_repo_hygiene_gitignore.py`, this record.

## 1. The defect, measured

A full-suite run on `main` left an untracked runtime artifact in the working tree:

```
$ python -m pytest tests/ -q -rEf --continue-on-collection-errors
$ git status --porcelain
?? data/engineering_lab/

$ find data/engineering_lab -type f
data/engineering_lab/agent_events.jsonl

$ git check-ignore -v data/engineering_lab
(exit 1 -- not ignored)
```

`lab/engineering_lab/events.py` snapshots its log destination at **import** time:

```python
_DEFAULT_LOG = os.path.join(
    os.environ.get("ENGINEERING_LAB_DATA_DIR", "data/engineering_lab"),
    "agent_events.jsonl",
)
```

and `lab/engineering_lab/runtime.py:299` falls back to
`get_event_stream()` — the process-wide singleton — when a runtime is constructed without
a stream. So any session that reaches that path appends telemetry **into the repository**,
and `.gitignore` had no rule for it. A `git add -A` in a hygiene pass would have folded
runtime telemetry into canon. This is the same class already recorded for the canonical
SolSpire store and the economic-seam store; the third member of the family was unguarded.

### The writer, identified by isolation

Each candidate file was run alone with the sandbox fixture absent, clearing
`data/engineering_lab/` first:

```
WRITER: tests/test_gate2_revocation_consistency.py -> data/engineering_lab/agent_events.jsonl
```

Several sibling modules call `monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", ...)`, which
**cannot** reach an already-snapshotted constant — they look sandboxed and are not. That
is the same failure the SolSpire fixture exists to prevent: patching one copy of a
module-level constant leaves every other copy writing to the real path, and the tests
still pass.

## 2. Repair

| Element | Change |
|---|---|
| `.gitignore` | `data/engineering_lab/` (rule names the tree, not all of `data/`) |
| `conftest.py` | `_sandbox_engineering_lab_events` — forces `ENGINEERING_LAB_DATA_DIR` and rebinds every `_DEFAULT_LOG` whose basename is `agent_events.jsonl`, mirroring the SolSpire and economic-seam fixtures |
| `tests/test_repo_hygiene_gitignore.py` | pins the path is ignored, is not tracked, the rule is scoped, **and** that the constant no longer resolves into the repository |

Ignoring the residue hides the symptom. The load-bearing assertion is that
`lab.engineering_lab.events._DEFAULT_LOG` does not resolve inside the working tree, so
removing the fixture reddens a test rather than silently re-opening the leak.

## 3. Paired control (the artifact, not the intention)

Same file, same command, fixture present vs absent:

```
$ rm -rf data/engineering_lab
$ python -m pytest tests/test_gate2_revocation_consistency.py -q     # fixture absent
22 passed
$ ls data/engineering_lab/agent_events.jsonl
data/engineering_lab/agent_events.jsonl          <-- written into the repository

$ rm -rf data/engineering_lab
$ python -m pytest tests/test_gate2_revocation_consistency.py -q     # fixture present
22 passed
$ test -d data/engineering_lab && echo PRESENT || echo ABSENT
ABSENT
$ ls /tmp/arkadia_pytest_session_*/engineering_lab/agent_events.jsonl
... 3704 bytes                                   <-- the telemetry landed in the sandbox
```

The test count is identical on both sides: the leak was invisible to the suite. That is
why it survived.

## 4. Live negative controls (each disables one half of the repair)

```
$ sed -i '/^data\/engineering_lab\/$/d' .gitignore
$ python -m pytest tests/test_repo_hygiene_gitignore.py -q
1 failed, 20 passed
FAILED tests/test_repo_hygiene_gitignore.py::test_engineering_lab_event_log_is_never_stageable
(restored byte-identically -> 21 passed)

$ <remove the _sandbox_engineering_lab_events fixture from conftest.py>
$ python -m pytest tests/test_repo_hygiene_gitignore.py -q
1 failed, 20 passed
FAILED tests/test_repo_hygiene_gitignore.py::test_engineering_lab_default_log_is_sandboxed
(restored byte-identically -> 21 passed)
```

Each control reddens exactly one node — the one that names the removed half. A control
that reddened all five, or none, would be measuring something else.

## 5. Regression measurement

`tests/test_repo_hygiene_gitignore.py`: **16 -> 21** nodes (`--collect-only` per file).

Full suite, `-rEf --continue-on-collection-errors`, same environment, both trees:

| Tree | Result | failing/error nodes |
|---|---|---|
| `main` `034d8879` | `78 failed, 4018 passed, 22 skipped, 27 errors` | 105 — `sha256 ee415edd…` |
| this branch | `78 failed, 4023 passed, 22 skipped, 27 errors` | 105 — `sha256 ee415edd…` |

`data/engineering_lab/` is **absent** after the branch's full-suite run (it was present
after `main`'s, which is how the defect was found). `tests/architecture`: unaffected —
`.gitignore`, `conftest.py` and a test file add no layer edge.

## 5.1 Node-set delta

```
main   nodes=105 sha256=ee415edd6ea7e9dc597562ab59312f681116600fead26613c6f7cac3bb964549
branch nodes=105 sha256=ee415edd6ea7e9dc597562ab59312f681116600fead26613c6f7cac3bb964549
$ comm -3 /tmp/nodes_main2.txt /tmp/nodes_lab.txt
(empty)
```

**Zero node-set delta.** The `+5 passed` is exactly the five added nodes. Absolute counts
are this sandbox's, not CI's; the node *set* is the environment-independent claim.

## 6. What this does not claim

- **No application behaviour changed.** The log destination is unchanged in production;
  only the test-session default is redirected, and the env var still wins.
- **The ignore rule is a guardrail, not an authority boundary.** A `git add -f` still
  works. The sandbox fixture is the actual repair.
- **`data/engineering_lab/` was never tracked** at `034d8879`; this change prevents it
  from becoming tracked, and does not rewrite any history.
- **No merge, deployment, or acceptance** is performed or authorized by this record.

## 7. Next permitted action

Human review of the draft PR. Merge execution is human-only under GOV-03.
