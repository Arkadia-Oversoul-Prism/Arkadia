# EVIDENCE — gate-hygiene/upstream-causal-schema-fixture-01

Bounded objective: repair the baseline test node
`tests/test_upstream_causal_continuity_01.py::test_api_approval_does_not_create_enterprise_authorization`
so it measures the invariant it claims (an API approval creates no enterprise
authorization) instead of failing on an absent schema. Test-side only.

BASE_MAIN: `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
Branch: `test-hygiene/upstream-causal-schema-fixture-01`
Observation timestamp: 2026-10-03T13:06Z

## 1. Defect

The node failed with `sqlite3.OperationalError: no such table: ew_authorizations`
from a raw `sqlite3.connect(db)` probe, before any assertion about the boundary
could run.

Root cause: `EnterpriseOrchestrationStore()` does **not** create the database or
its schema — the constructor only resolves the path. Schema materialization is
deferred to the first store operation (`weaver/enterprise_orchestration.py::_db()`,
`CREATE TABLE IF NOT EXISTS …`). The test's fixture pointed `ew._DB_PATH` at a
`tmp_path` file, constructed the store, then drove an approval through the API
route; because the approval path never touches the enterprise store, no operation
ever ran, so no schema existed when the probe connected.

Reproduced directly:

```
file exists after store(): False
BEFORE repair -> OperationalError no such table: ew_authorizations
AFTER repair count: 0
```

## 2. Repair (test-side only)

Materialize the schema in the fixture, so the raw probes measure record absence
rather than table absence. Two sites in the same module:

- `_ops()` fixture: `with ew_mod._db(): pass` after constructing the store.
- `test_api_approval_does_not_create_enterprise_authorization`: same, before the
  probe.

No production source, workflow, governance, or constitutional file changed.

## 3. Evidence

| Check | Command | Result |
|---|---|---|
| Target module | `pytest tests/test_upstream_causal_continuity_01.py -q` | **3 passed** (was 1F/2P) |
| Full suite | `pytest tests/ -q --continue-on-collection-errors` | 19F / 1307P / 17S / 1E (was 20F / 1306P) |
| Regression boundary | failure-node set delta | `-1` (`test_upstream…`), `+0` — exactly the target node |
| Architecture fitness | `pytest tests/architecture -q` | 11 passed |
| Boot compile | `python -m py_compile api/main.py` | OK |
| Budget | `wc -l api/main.py` | 2582 / 2600 |
| CP10 mutation boundary | `git diff --name-only main...HEAD \| scripts/cp10_mutation_boundary_policy.py --judge` | PASS (rc=0) |

Fingerprints (canonical `scripts/baseline_fingerprint.py`):

| Tree | outcomes fingerprint | ids fingerprint |
|---|---|---|
| `origin/main` (`162f574b`) | `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` | `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` |
| this branch | `b45c07534bcf19ca3fb28631246f84f578e41e5e735d94d36e95fdf12e2f6f92` | `e029bf886c1efccb81e219669c7ede615e1690f411e4135a11429e63a3585859` |

The delta is a single removed node; no new node was introduced.

## 4. Cross-check against the recorded baseline fixture

`tests/fixtures/baseline_node_set.txt` (20 nodes) carries outcomes fingerprint
`a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1` / ids
`8036fc0692eb0358f037adb2cf9e2b234db1f41a4586ca0162f4e52350cfa713`, and does
**not** include `test_upstream…`. That fixture is the recorded 20F set with the
upstream node absent and `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
present. On this clone the live set is 21 nodes: the recorded 20 plus
`test_shadow…`. The extra node is an artifact of clone depth
(`test_agents_md_encoding_adjudication.py` depends on
`scripts/agents_md_encoding_audit.py`'s oracle-revision access, which PR #215
addresses via a fixture revision pin) — a separate, already-tracked workstream.
It is recorded here as **UNKNOWN/external**, not repaired in this PR.

After this repair, the branch set is 20 nodes: the recorded fixture's 20 minus
`test_upstream…`, plus `test_shadow…`. The two deltas are independent and both
attributed.

## 5. Remaining uncertainty

- Whether `test_shadow…` fails on a full-history CI checkout is not decided here;
  PR #215 is the owning workstream.
- No production/runtime claim is made. This is a repository-source test-hygiene
  repair only.
- Not merged; merge is a human authority act.
