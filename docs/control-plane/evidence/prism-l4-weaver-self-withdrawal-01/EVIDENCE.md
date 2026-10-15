# Lane 4 — Weaver approval ledger: a self-rejection is a permitted withdrawal, not a boundary violation

**Branch:** `feat/prism-l4-weaver-self-withdrawal-01`
**Starting `main`:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
**Lane:** 4 — Arkana / Weaver / Engineering Lab (`AGENT-04-ARKANA-WEAVER-LAB.md`)
**Ownership:** Weaver feature-local components + their tests. No shared shell file touched.
**Authority:** no merge, deployment, or acceptance. Draft PR only.

---

## 1. Defect reproduced (before any change)

`web/arkadia_console/src/components/weaver/approvalLedger.ts` derived one flag from
one condition:

```ts
const self_decided = subject_ref !== null && decided_by !== null && subject_ref === decided_by;
const boundary_violation = self_decided || contradictory;
```

Every self-decision — approval **or** rejection — was therefore reported as a
boundary violation. Executing the real projection (node imports the `.ts` and runs it — not a source
substring) from the **base revision `7580bd8f`**, against a self-rejection the
backend *does* produce:

```
$ git show 7580bd8f:web/arkadia_console/src/components/weaver/approvalLedger.ts > /tmp/pre/weaver/approvalLedger.ts
$ node /tmp/pre/run.mjs      # buildApprovalLedger over one self-rejected approval
[
  {
    "id": "r1",
    "phase": "DECIDED",
    "self_decided": true,
    "boundary_violation": true,
    "note": "Boundary violation: a principal may not decide its own request (the backend refuses self-approval)."
  }
]
```

The record is a `DECIDED` self-rejection yet carries `boundary_violation: true`.

## 2. Why that is wrong — the backend does two different things

Measured from the serving handler, `api/approval_routes.py`:

| Act | Backend behaviour | Source |
|---|---|---|
| self-**approval** | refused, `403` | `api_approve`: "A principal may not approve its own request" |
| self-**rejection** | **permitted** | `api_reject` docstring: "Self-rejection is permitted: withdrawing one's own request is not a governance decision over another's consequential operation." |

A read-only surface that labels a legitimate, backend-produced self-rejection as a
boundary violation is asserting a boundary the backend does not enforce. That is a
false accusation on a governance surface — the reviewer is told a record is
illegitimate when it is an ordinary withdrawal.

## 3. Repair

`approvalLedger.ts` now derives the two self-decisions separately and narrows the
violation to the act the backend actually refuses:

```ts
const self_approved = self_decided && status === "approved";
const self_rejected = self_decided && status === "rejected";
const boundary_violation = self_approved || contradictory;
```

- `record.self_approved` (new) — the refused act.
- `record.self_rejected` (new) — the permitted withdrawal; own note, own copy.
- `record.self_decided` — retained as the neutral observation.
- `noteFor` gains `self_rejected` and emits "Withdrawn by the requester. Self-rejection
  is permitted — withdrawing one's own request is not a governance decision over
  another's operation."
- `ApprovalLedger.tsx` renders a `withdrawn` marker (`data-testid="weaver-approval-withdrawn-<id>"`)
  so the distinction is visible, not only in the projection.

The docstring's boundary rule is corrected to match (`Self-approval is a violation;
self-rejection is not.`), quoting `api_reject`.

## 4. Proof

### 4.1 Targeted suite — the lane's own guard

```
$ python -m pytest tests/test_prism_w4_weaver_approval_ledger.py -q -rEf
15 passed in 1.73s          # was 13 passed at 7580bd8f; +2 = the two new nodes
```

New nodes:

- `test_self_rejection_is_a_permitted_withdrawal_not_a_violation` — a **negative
  control** comparing a self-rejection and a self-approval that name the *same*
  identity. A projection flagging every self-decision reddens the withdrawal
  assertion; one flagging no self-decision reddens the approval assertion. Neither
  can pass by accident.
- `test_a_distinct_decider_is_never_a_self_decision` — the guard must not widen:
  a decision by a different principal stays ordinary for both statuses.

### 4.2 Live negative control on the real file

Restoring the pre-repair expression **in the working tree, in place** and re-running
the guard reddens exactly the new node, then the file was restored byte-identically:

```
$ cp web/arkadia_console/src/components/weaver/approvalLedger.ts /tmp/ledger.bak
$ sed -i 's/const boundary_violation = self_approved || contradictory;/const boundary_violation = self_decided || contradictory;/' \
    web/arkadia_console/src/components/weaver/approvalLedger.ts
$ grep -n "boundary_violation = " web/arkadia_console/src/components/weaver/approvalLedger.ts
171:  const boundary_violation = self_decided || contradictory;      # defect reintroduced
$ python -m pytest tests/test_prism_w4_weaver_approval_ledger.py -q -rEf
FAILED tests/test_prism_w4_weaver_approval_ledger.py::test_self_rejection_is_a_permitted_withdrawal_not_a_violation
1 failed, 14 passed in 1.72s
$ cp /tmp/ledger.bak web/arkadia_console/src/components/weaver/approvalLedger.ts   # restored
$ grep -n "boundary_violation = " web/arkadia_console/src/components/weaver/approvalLedger.ts
171:  const boundary_violation = self_approved || contradictory;    # repaired; file byte-identical
```

The failure lands on the new node's own assertion (`tests/test_prism_w4_weaver_approval_ledger.py:222`,
`assert withdrawn["boundary_violation"] is False`), not on an unrelated parsed node.

The pre-existing `test_self_decision_is_a_boundary_violation` (self-**approval**)
still passes on both sides — the repair narrowed the flag, it did not remove it.

### 4.3 Related Lane-4 surfaces

```
$ python -m pytest tests/test_prism_w4_weaver_approval_ledger.py \
    tests/test_prism_w4_automation_grammar.py tests/test_prism_w4_run_evidence_trace.py \
    tests/test_lab_automation_grammar_contract.py tests/test_prism_w4_lane4_render_integrity.py -q -rEf
90 passed in 6.76s
```

### 4.4 Typecheck and build (the console is TypeScript; the guard is Python)

```
$ cd web/arkadia_console && corepack pnpm install --frozen-lockfile --prefer-offline
Done in 3.2s
$ corepack pnpm exec tsc --noEmit                                   # exit 0
$ corepack pnpm build
✓ built in 1.59s
```

`build` is `tsc --noEmit && vite build`, so the new fields and JSX marker are
type-checked, not merely executed by Node.

### 4.5 Mutation boundary

```
$ printf 'docs/control-plane/evidence/prism-l4-weaver-self-withdrawal-01/EVIDENCE.md\n
  tests/test_prism_w4_weaver_approval_ledger.py\n
  web/arkadia_console/src/components/weaver/approvalLedger.ts\n' |
  python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

## 5. Regression boundary

No shared shell file (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`,
`types.ts`, `SurfaceLenses.tsx`) and no backend authority file is touched. The
change is confined to Weaver feature-local components and their guard.

## 6. Unresolved / next bounded move

- The projection reads `status` and the record's identity fields. It does **not**
  verify the handler's `decided_by` was recorded by a `Govern` principal — a record
  crafted outside the handler would still read as an ordinary decision. The ledger
  is a projection of what is served; it cannot re-derive authority the handler did
  not record. Recorded, not repaired: it needs a serving-side field.
- Next Lane-4 read surface, per `AGENT-04`: the Arkana thread-history slice
  (continuation of PR #428's family), still read-only.
