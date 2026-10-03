# gate-hygiene: #217 and #221 are lineage-equivalent — the cluster's order-insensitivity is provable

**Workstream:** `gate-hygiene` (open-PR queue composition; standalone, not an architectural gate)
**Bounded question:** The composable cluster is `#215–#219`. `#221` is a draft offshoot that also
edits `tests/test_agents_md_encoding_adjudication.py`. Is `#221` **additive** to the cluster
(should merge after `#217`) or **alternative** to it (same target, and therefore mutually
exclusive)?
**Classification:** `VERIFIED` (repository-layer, measurement-only; no source mutation).
**Base:** `main` @ `162f574b05dd839540d803aadda7608342618a84`
**Branch:** `gate-hygiene/pr-217-221-lineage-equivalence-01`
**Pass:** 7 (composition/queue line, continuing `gate-hygiene-open-pr-queue-merge-order-map-02`).

---

## 1. Answer

`#217` and `#221` are **lineage-equivalent**: they edit the *same* target node — the
`test_exit_code_does_not_call_a_divergent_clean_file_verified` fixture premise — and the
resulting failing-node sets after each is merged over `main` are **byte-identical**. They are
two revisions of one design, not two pieces of work.

Two independent proofs, each derived from a live merge (not from prose):

1. **Textual — one hunk, two revisions.** Both replace the single expression
   `_rev("AGENTS.md", "origin/main")` with `_rev("AGENTS.md", CORRUPTION_COMMIT)` in the same
   function (line ~427). `#217` does this in a focused `+10/-1` hunk; `#221` does the same
   substitution plus a provenance comment and a fixture-availability assertion (`+69/-5`).
   Neither deletes a node the other keeps, so merging both is impossible (conflict at that
   hunk), and merging either alone yields the same node set.
2. **Runtime — identical fingerprints.** Merged over `main` `162f574` in a lineage-complete
   worktree, the two trees produce the *same* full-suite fingerprint:

   | tree (over `main` `162f574`) | nodes | outcomes fingerprint | ids fingerprint |
   |---|---|---|---|
   | `#215 #216 #217 #218 #219` | 19 (18F/1E) | `c9ffdb62…d05c01` | `2c92cb38…c74a6e` |
   | `#215 #216 #218 #221` | 19 (18F/1E) | `c9ffdb62…d05c01` | `2c92cb38…c74a6e` |

   The fingerprints are the canonical derivation from `scripts/baseline_fingerprint.py`
   (log parser), not a hand-rolled count.

**Disposition:** `#221` is **not additive**. Any cluster containing `#217` already carries
`#221`'s effect. `#221` subsumes `#218` (`git merge-base --is-ancestor pr/218 pr/221` → true)
and is disjoint from `#215`/`#216`; it is therefore an **inclusive alternative for the
`#217 + #218` pair** — the `[215,216,218,221]` sequence composes clean and lands at the same
point. Merge **either** `#217` **or** `#221`, never both. Because `#217` is numbered into the
canonical `#215–#219` cluster and `#221` is a draft that re-branches `#219`'s ancestor
(`merge-base(pr221, main) = 162f574`), `#217` is the recomposed-cluster member; `#221` should
be closed as superseded once `#217` merges, or merged *in place of* `#217`/`#218` under a
separate authorized cluster. **This is a recommendation; the disposition (close/merge) is a
sovereign call on an external artifact.**

## 2. Live state (reconstructed, not inherited)

Timestamp of reconstruction: 2026-10-03T10:0xZ. Command: `gh pr list --state open`.

| PR | draft | head SHA | mergeable | title |
|---|---|---|---|---|
| #215 | false | `0c18fbb40` | MERGEABLE | baseline set depth-stable (skip shadow-oracle adjudication without its pinned revision) |
| #216 | false | `4747e4c62` | MERGEABLE | explain origin of the superseded baseline fingerprints |
| #217 | false | `3b5e4cdcc` | MERGEABLE | pin the live-file adjudication fixture to the corrupt revision |
| #218 | false | `54e2e988c` | MERGEABLE | pin the gate-2 adjudication fixture to the corrupt revision |
| #219 | false | `c3ddf61ca` | MERGEABLE | open-PR queue composability (pass 6) |
| #220 | **true** | `0893987be` | MERGEABLE | SH-05 retirement boundary — HOLD (sovereign call required) |
| #221 | **true** | `896033291` | MERGEABLE | close #218 residual origin/main fixture pin + clone-depth forensics |
| #222 | false | `88debcfb0` | MERGEABLE | test-hygiene: execute the API→enterprise authority boundary test |

`#220` is `HOLD`, out of scope (sovereign `SH-05` product ruling). `#222` is a standalone
`test-hygiene` offshoot, measured below as a separate step.

`#221`'s merge-base with `main` is `162f574` (it is **not** stacked on `#219`), and it
contains `#218` (`54e2e988`) as an ancestor. It contains neither `#217` (`3b5e4cd`) nor
`#216`.

## 3. Why the composition is order-insensitive (root cause)

`#215`, `#216`, `#217`, `#218` all edit `tests/test_agents_md_encoding_adjudication.py` and
`#219` edits `AGENTS.md`. Git auto-merges every one of these because each touches a
**disjoint hunk**. The cluster is therefore order-insensitive *by hunk disjointness* — a
property declared in `#219`'s pass-6 evidence and re-measured here, not a coincidence:

```
$ git merge pr/215 pr/216 pr/217 pr/218 pr/219   # over main 162f574
Auto-merging tests/test_agents_md_encoding_adjudication.py   (x2)
Auto-merging AGENTS.md
HEAD c7bf907   -> 19 nodes
```

`#217` and `#218` are **siblings, not the same node** — a correction to `#221`'s own
evidence, which claims `#221` "closes the latent fixture-pin defect #218 left on the very
node it did not touch". Measured:

- `#217` fixes `test_exit_code_does_not_call_a_divergent_clean_file_verified`
  (`git diff origin/main...tmp_pr217` → one hunk at `@@ -424,7`).
- `#218` fixes `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` (a
  different function).
- `#221` (because it contains `#218` and adds the same `test_exit_code…` substitution as
  `#217`) edits **both**.

So `#221` is not "closing a #218 gap that #217 also closes"; it is `#218 ∪ #217` on the
adjudication file. That is exactly why `#217` ⊻ `#221` are interchangeable once `#218` is
present.

## 4. Measurements (all on base `162f574`)

Environment: `PYTHONPATH=<repo>/archive/legacy_python`, `pytest 9.1.1`, `pytest_asyncio 1.4.0`,
lineage-complete worktree at `/tmp/wt-compose` (holds `7d79f38`).

```
plain main 162f574                 -> 21 nodes (20F/1E)   a59453b8…/9a35c812…
cluster  #215#216#217#218#219      -> 19 nodes (18F/1E)   c9ffdb62…/2c92cb38…
variantA #215#216#218#221          -> 19 nodes (18F/1E)   c9ffdb62…/2c92cb38…
cluster + #222 (test-hygiene)      -> 18 nodes (17F/1E)   4e189cac…/eae79aac…
```

Delta vs `main` (node-set diff, not counts):

- Cluster fixes **2** node families: both adjudication nodes
  (`test_exit_code_does_not_call_a_divergent_clean_file_verified`,
  `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`) plus
  `test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`.
- **Zero new failures** in every composed tree.
- `#222` alone removes one further node (`test_authorized_identity_is_the_control_case_and_creates_both_records`),
  the async node it exists to make executable — see §6.

## 5. Regression boundary

This artifact is **documentation only** — no source, test, or workflow file is modified. The
reviewable claim is the measurement, not a code change. Negative control: the two superseded
fingerprints above are *not* published as the cluster's baseline (they describe composed
trees, not `main`); the `main` fingerprint `a59453b8…` is the recorded
`tests/fixtures/baseline_node_set.txt` value at 21 nodes.

## 6. #222 (test-hygiene, separate) — composition status

`#222` adds a `pytest-asyncio` block to `requirements.txt` so
`tests/test_authority_api_enterprise_boundary.py`'s async node actually executes. Measured
over the composed cluster (not over `main` alone), it is **green and non-regressive**: it
moves the tree from 19 → 18 nodes by resolving the async node, and introduces no new node.
Residual failures in the composed tree are the classification: `test_gate_serve_script`,
`test_gate_status`, guardian/steward/registry/solarian nodes that were already failing on
`main` — the `test-hygiene` pass is not responsible for them and must not widen its scope to
them.

## 7. Side measurement — the recorded baseline fixture does not reproduce on plain `main` (recorded, not fixed)

While establishing the baseline for the comparison above, plain `main` `162f574` measured
**21** nodes, not the **20** recorded in `tests/fixtures/baseline_node_set.txt`. The delta is a
single node:

```
+ FAILED tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec
```

That node dereferences `GATE2_PARENT_REV = 7d79f38…`, which is reachable from no branch of
this repository (`git cat-file -t 7d79f38` → **absent**) but is present in a lineage-complete
developer clone. With the object present it **passes**; with it absent it **fails** (it does
not skip, because the guard calls `_rev()` before checking). So in *this* clone shape the
node is depth-dependent in the **failure** direction — the mirror of
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`, which the recorded set
excludes because it skips when the object is absent.

`tests/test_baseline_fingerprint.py` still passes 17/17 on this tree: the recorded set is
internally consistent with the extractor; it is the *node set itself* that does not reproduce
from a plain `main` run here.

This is **#215's** exact subject ("make the recorded baseline set depth-stable — skip the
shadow-oracle adjudication without its pinned revision"): after `#215`, the shadow node skips
when `7d79f38` is unreachable, restoring a 20-node set. **Recorded as an observation, not
repaired here** — repairing `main`'s fixture is #215's bounded scope, and this pass must not
duplicate it. It is noted so the next heartbeat does not misattribute the 21-vs-20 delta.

## 8. Remaining uncertainty

- The **disposition** (close `#221` vs merge it in place of `#217`/`#218`) is an external
  artifact action and a sovereign call; this pass supplies the evidence, not the decision.
- Whether the composed cluster is green on CI depends on the CI checkout *depth*. A
  `--depth=1` clone drops `CORRUPTION_COMMIT`/`ORACLE_REV` and reddens the adjudication file
  more broadly (5 failed, per `#221` §2); a lineage-complete CI checkout merges green. The
  locally measured composition is order-insensitive **given a lineage-complete checkout**.
- Counts vary between runs of the same tree because
  `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository` is
  order-dependent (documented in `AGENTS.md`); all claims here use the **node set**, not counts.
