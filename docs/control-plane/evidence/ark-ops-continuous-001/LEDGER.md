# ARK-OPS-CONTINUOUS-001 — cycle ledger index

**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
**Derived:** 2026-11-26, cycle 24, from the live open-PR file lists at `main` `cb284195`.

## Why this file exists

The contract's §1 requires that an agent "be able to resume without relying on
conversational memory". Before this index that was not satisfiable from the repository:

- `main` tracks **no** `ark-ops-continuous-001-*` evidence at all
  (`grep -rIl "ARK-OPS-CONTINUOUS-001" .` → no match), because the ledger lives in an
  unmerged PR; and
- the ledger is **not in one place**. Cycle records are carried by **16 different open
  PRs**, so a reader of any single PR sees a subset and cannot tell an unrecorded cycle
  from one recorded elsewhere.

A reader of this PR alone sees cycles 01–05, 13, 15, 19–23 and would reasonably conclude
that cycles 06–12, 14, 16–18 produced nothing. They exist — in `#712`–`#723`, `#729`,
`#731`, `#735` and `#736`.

## How this index is derived (do not hand-maintain from memory)

```bash
for n in $(gh api 'search/issues?q=repo:Arkadia-Oversoul-Prism/Arkadia+is:pr+is:open&per_page=100' \
             --jq '.items[].number'); do
  gh api "repos/Arkadia-Oversoul-Prism/Arkadia/pulls/$n/files?per_page=100" \
    --jq ".[] | \"$n \" + .filename"
done | grep 'ark-ops-continuous'
```

Re-run it before trusting any row. The index is a snapshot of **open** PRs; a merged
record moves from its PR into `main`, and a closed one disappears without the cycle being
retired. Neither transition is observable from this file.

## Index

| cycle | record directory | carried by |
|---|---|---|
| 01 | `…-cycle-01` | #705 |
| 02 | `…-cycle-02` | #705 |
| 03 | `…-cycle-03` | #705 |
| 04 | `…-cycle-04` | #705 |
| 05 | `…-cycle-05` | #705 |
| 06 | `…-cycle-06` · `…-cycle-06-root-doc-link-integrity-01` | #712 · #714 |
| 07 | `…-cycle-07` · `…-cycle-07-root-doc-module-map-01` | #713 · #715 |
| 08 | `…-cycle-08-orientation-doc-frontend-currency-01` · `…-cycle-08-root-doc-deployment-host-01` | #715 · #716 |
| 09 | `…-cycle-09-gemini-model-ladder-01` · `…-cycle-09` | #717 · #721 |
| 10 | `…-cycle-10-http-error-contract` | #718 |
| 11 | `…-cycle-11-android-unit-test-classpath-01` | #719 |
| 12 | `…-cycle-12-oversoul-prism-conformance-01` | #720 |
| 13 | `…-cycle-13` | #705 |
| 14 | `…-cycle-14` | #723 |
| 15 | `…-cycle-15` | #705 |
| 16 | `…-cycle-16-api-5xx-contract` | #729 |
| 17 | `…-cycle-17-auth-boundary-declaration-01` | #731 |
| 18 | `…-cycle-18-source-sync-error-disclosure` | #735 |
| 19 | `…-cycle-19` | #705 |
| 20 | `…-cycle-20` · `…-cycle-20-pr-wave-dry-run` | #705 · #736 |
| 21 | `…-cycle-21` | #705 |
| 22 | `…-cycle-22` | #705 |
| 23 | `…-cycle-23` · `…-cycle-23-home-portal-label-duplication-01` | #705 · #742 |
| 24 | `…-cycle-24` | #705 |

Every cycle through 23 has a record. Six cycle numbers — **06, 07, 08, 09, 20, 23** —
are carried twice, under different directories, by different PRs.

## The two-record convention

A cycle can produce both a reconciliation record and one or more fix records. They
coexist because the directories differ: the bare `…-cycle-NN` holds the reconciliation
record and `…-cycle-NN-<slug>` holds a fix record. This is the existing convention, not a
new one — 06, 07, 08, 09 and 20 already follow it.

**The collision, and its repair.** Cycle 23 was the first number where *both* records were
added at the bare path:

```
docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md
  #705  "cycle 23: the queue is not frozen, and one candidate is eligible"   (reconciliation)
  #742  "cycle 23: the home portal grid printed five labels twice"           (fix)
```

Both PRs report `mergeable` against `main`, because GitHub compares each PR with `main`
and never with the other. Merging either first made the other an **add/add** conflict,
measured in a detached worktree in both orders:

```
$ git merge --no-edit pr/742   # from pr/705 head
CONFLICT (add/add): Merge conflict in docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md
$ git merge --no-edit pr/705   # from pr/742 head
CONFLICT (add/add): Merge conflict in docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md
```

Repaired in #742 by renumbering its record to
`…-cycle-23-home-portal-label-duplication-01` (`27467ed7`), which restores the two-record
convention. Verified after the repair: merging `pr/705` into #742's new head exits 0 with
**zero** unmerged files and both records present.

**Rule for the next cycle:** never add a bare `…-cycle-NN/` directory. If the bare path
already exists in another open PR, the record being written is a fix record — give it the
slug.

## Known limits

- A snapshot of open PRs, not of history. It cannot tell whether a cycle's work was
  accepted, superseded, or abandoned.
- It cannot detect a duplicate that differs only by slug (`…-cycle-23-a` vs
  `…-cycle-23-b`), because two fix records for one cycle are legitimate.
- The numbering is not authoritative: two runners can both call the same hour "cycle 23",
  which is what produced the collision above. This index records the collision; it does
  not decide which runner owns the number.
