# Opportunity Radar — project-board prospect create/edit entry flow

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: add create/edit prospect entry controls to the **selected
project board**, using only the two verified write handlers. Authority: human
retains merge, production deployment, and acceptance. Nothing here claims any of
the three.

## Revision binding

- Work branch: `feat/prism-next2-02-opportunity-entry-flow` (draft PR #430).
- `origin/main` at the start of this pass: `f390526ab14e122fef358ef9b9e1cd438509463c`
  (`feat(arkana): add verified thread and Lab read surfaces`).
- Branch head before this pass: `e6780d47` (docs-only; the two commits on the
  branch touched only `AGENT-02-NOVANET-OPPORTUNITY.md`).

## 1. Verified route contract (measured, not assumed)

Read from `solspire/buyer_recon_router.py`, mounted under
`solspire/console_router.py` (`prefix="/solspire"`,
`dependencies=[Depends(require_auth)]`):

| Method | Path | Auth | Owner check | Success |
|---|---|---|---|---|
| GET | `/solspire/buyer-recon/projects/{project_id}` | `require_auth` | `require_project_owner` | 200 |
| POST | `/solspire/buyer-recon/projects/{project_id}/entries` | `require_auth` | `require_project_owner` | 201 |
| PATCH | `/solspire/buyer-recon/projects/{project_id}/entries/{entry_id}` | `require_auth` | `require_project_owner` | 200 |

Request bodies are the handlers' own declarations: `BuyerReconEntryInput`
(create, `prospect` required) and `BuyerReconEntryPatch` (edit, `extra="allow"`).
Both responses are `{"entry": {...}}`.

`require_project_owner` raises **404** — for a missing project *and* for a
non-owner. The two are deliberately indistinguishable, so the UI must not claim
which one occurred; it says the project is not available to this identity.

Measured live in this environment (temporary DB, composed console router):

```
create blank prospect:  400 {"detail": "prospect is required"}
create ok:              201 {'prospect': 'Buyer A', 'buyer_price': 'UNKNOWN',
                              'status': 'UNCONTACTED', 'evidence_status': 'NONE', 'evidence': []}
patch blank prospect:   200 ''          <-- a PATCH accepts a blank prospect
patch evidence:         200 [{'kind': 'quote', 'ref': 'x'}]
patch supplier:         200 ACME
patch bogus status:     400 {"detail": "invalid status"}
create bogus status:    400 {"detail": "invalid status"}
response keys:          ['entry']  (both routes)
```

Two consequences shaped the implementation:

1. **A blank `prospect` is refused on create but accepted on edit.** Sending an
   empty one on edit would blank a recorded prospect, so the edit body omits
   `prospect` unless the operator supplied a value.
2. **`prospect is required` is the only server rule an operator can break
   locally.** The control mirrors it as a pre-flight explanation; the server
   remains the authority and still refuses it.

## 2. What changed

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts` | Added the write contract: `ProspectDraft`, `DESCRIPTIVE_FIELDS`, `COMMERCIAL_FIELDS`, `emptyDraft`, `isSupplied`, `createEntryBody`, `editEntryBody`, `prospectRequired`, `isNoOpEdit`, `draftFromEntry`, `parseEntryResponse`, `upsertEntry`, and the board-derived path helpers `entriesPathFromBoard` / `entryPathFromBoard`. |
| `web/arkadia_console/src/components/opportunities/ProspectEntryForm.tsx` | **New.** The create/edit control. Feature-local; no shared file edited. |
| `web/arkadia_console/src/components/opportunities/ProjectOpportunityRadar.tsx` | Wired the form in (create button, per-entry edit button), added the confirmed-response upsert and per-entry commercial facts. The existing read contract, states and pinned copy are preserved verbatim. |
| `tests/test_prism_opportunity_entry_flow.py` | **New.** 38 tests: backend write contract, executed frontend contract probe, and a cross-layer binding that feeds the frontend-built bodies into the real handler. |

No shared router, navigation, endpoint registry, type registry, shell test, or
backend file was edited. `api/main.py` is untouched.

## 3. Truthfulness rules held

- **An unverified commercial fact stays `UNKNOWN`.** Commercial inputs default to
  the backend's own sentinel and are **omitted from the body** when left there, so
  the server applies its default rather than the client asserting a value it does
  not hold. A descriptive field left blank is likewise omitted.
- **Nothing is recorded until the server confirms it.** The saved entry is the one
  the response carried (`parseEntryResponse`), never the submitted draft; a body
  without the declared `entry` key is reported as an unrecognised shape.
- **Evidence is never asserted.** `evidence_status` / `evidence` are never sent —
  capturing a prospect does not assert that evidence exists, so the backend's
  `NONE` / `[]` stand.
- **No delete, bulk, spend, approve, or execute control.** Those have no verified
  handler and would imply authority this surface does not have.
- **`EXECUTED` / `SETTLED` are readable, never settable** (§3a). Recording one
  claims that money moved, and this board's own response declares
  `execution_authority: "NONE"` / `budget_authority: "NONE"`. The settable
  vocabulary stops at `READY_TO_EXECUTE`, and the ceiling is enforced in the body
  builders — not only in the `<select>`'s option list. An entry already at a
  terminal status renders read-only.
- **No-op edits are explained, not sent.** Saving an unmodified form reports
  "No change to save" rather than issuing a write that records nothing.
- **A board switch clears the form and the locally held entries**, so an edit
  control can never address an entry id belonging to another project's board.

## 3a. The reconnaissance ceiling — a correction to the above

**Measured at `8c0f5dd4` and corrected here.** The earlier wording — "No delete,
bulk, spend, approve, or **execute** control … those have no verified handler" —
was true about *handlers* and false about the **status field**. `BuyerReconEntryPatch`
validates against the full `STATUSES` tuple, which includes `EXECUTED` and
`SETTLED`, and the form's `<select>` offered the whole vocabulary. There was no
button named Execute, but the outcome was one click away, and the form's own copy
("Recording a status is reconnaissance. It authorizes no spending, approval, or
execution.") sat directly beneath a control that could record exactly that.

Measured before the repair, by executing the contract module under Node 24:

```
BUYER_RECON_STATUSES.includes("EXECUTED")   -> true
createEntryBody({status:"EXECUTED"}).status -> "EXECUTED"
editEntryBody({status:"EXECUTED"}, entry)   -> {status:"EXECUTED"}
```

The repair adds `SETTABLE_STATUSES` (the vocabulary through `READY_TO_EXECUTE`,
mirroring the archived Prism `ProjectOpportunityRadar`'s `RECONNAISSANCE_STATUSES`
column set) and `TRANSACTION_OUTCOME_STATUSES`. `createEntryBody` and
`editEntryBody` gate on `isSettableStatus`, so the ceiling is **structural**: a
caller that hands them an `EXECUTED` draft cannot produce a body that records the
outcome. The form offers only `SETTABLE_STATUSES` and renders a recorded terminal
status as a read-only field.

**Both halves are stated, not implied.** `test_measured_the_exposure_the_ceiling_closes`
records that the *server* still accepts `EXECUTED` through this PATCH. The ceiling
is a product decision on the surface's side; there is no server-side guard, and
none is claimed.

## 4. Tests

`python -m pytest tests/test_prism_opportunity_entry_flow.py -q` → **48 passed**
(38 at `8c0f5dd4`; +10 are the reconnaissance ceiling and MEASURED DEFECT 3
sections added at this revision — §3a, §6).

Covered: create success + persisted state; the entry lands on the project board
and not the workspace board; omitted commercial facts keep the `UNKNOWN` default;
blank/missing prospect refused on create; invalid status refused on create **and**
edit with the store unchanged; unauthenticated and non-owner create/edit refused
**with no write**; cross-project and project↔workspace edit refusal asserted on
persisted state; partial update leaves untouched fields alone; `updated_at`
advances; the response equals the persisted row; a 404 for an unknown entry.

The frontend half is **executed, not string-matched**: Node 24 runs TypeScript
directly, so `opportunityRadarContract.ts` is imported through a subprocess and
its body builders are driven against the shapes the handlers return.

**Cross-layer binding.** The bodies the contract module produces are then POSTed
and PATCHed into the *real* handler by the backend tests. A frontend change that
emits a field the handler rejects, or omits one it needs, therefore fails a Python
test rather than only showing up in a browser. The minimal body produces a wholly
unverified entry; the rich body records exactly the supplied fields and leaves the
rest at the backend default; the single-field edit leaves the recorded commercial
fact intact.

### Negative controls (all present)

- A supplied commercial fact *is* recorded (proves the `UNKNOWN` pin is not vacuous).
- A declared status *is* accepted.
- The owner identity *is* what admits the write (same request, identity changed).
- The own-board edit still succeeds (the narrowing did not break the guarded path).
- The probe distinguishes a wrong body builder.
- A body the frontend must not send (invalid status, sentinel written out) is
  refused at the boundary with nothing persisted.

### Mutation check — the detectors bite (live, then restored)

Each mutation was applied to the working tree, the suite re-run, and the tree
restored. Restored byte-identically (`sha256sum` of all three files unchanged):

| Mutation | Result |
|---|---|
| Contract asserts `UNVERIFIED` commercial facts on the wire | 3 failed |
| Surface resolves transport itself (`fetch`) | 2 failed |
| Form trusts the draft instead of the server response | 1 failed |
| `SETTABLE_STATUSES` → `BUYER_RECON_STATUSES` in the form's `<select>` **and** `isSettableStatus` → `isKnownStatus` in both body builders | 2 failed |
| `isSettableStatus(draft.status) ?` → `true ?` (terminal status rendered as a select) | 1 failed |
| Edit body rewrites every field (non-partial PATCH) | 2 failed |
| Create body asserts evidence the operator did not record | 2 failed |
| Create body sends the `UNKNOWN` sentinel explicitly | 2 failed |

Two test-side defects were found and fixed during this pass: the method-selection
assertion targeted the surface instead of the form, and the forbidden-token
detector matched the *prose* that documents the absence of a delete control.
`_code_only()` now strips comments before scanning, so the detector reads code.

## 5. Build and suite evidence

- `corepack pnpm install --frozen-lockfile` → done; `corepack pnpm build`
  (`tsc --noEmit && vite build`) → **passed**, `dist/assets/index-DY1OtSNU.js`
  73.86 kB.
- `python -m pytest tests/architecture -q` → **11 passed**.
- Full suite, same environment, `-q -rEf --continue-on-collection-errors`:

| Tree | Result | Failing/error node set sha256 |
|---|---|---|
| `main` `f390526a` | 27 failed, 2342 passed, 17 skipped, 1 error | `92fcd59cb4f0aee3249c93045c3d1ddd5bfd591c24d5b628db829c0fd1645048` (28 nodes) |
| branch | 27 failed, 2380 passed, 17 skipped, 1 error | `92fcd59cb4f0aee3249c93045c3d1ddd5bfd591c24d5b628db829c0fd1645048` (28 nodes) |

`comm -3` on the sorted node sets is **empty** — zero regression. The `+35
passed` is exactly this file's node count (`--collect-only` → 35). The 27
pre-existing failures and the `tests/test_autonomy.py` collection error (CE-01,
reserved to the sovereign) are unchanged by this pass and were not repaired here.

### Re-measured at this revision (48 tests, the reconnaissance ceiling)

| Tree | Result | Node set (sorted `FAILED`/`ERROR` ids) |
|---|---|---|
| branch before this pass (`8c0f5dd4`) | 27 failed, 2342 passed, 17 skipped, 1 error | 28 nodes, `67745e62…` |
| branch after this pass | 27 failed, 2390 passed, 17 skipped, 1 error | 28 nodes, `67745e62…` |

`comm -3` on the sorted node sets is **empty** on both trees; the `+48 passed` is
exactly this file. Note the fingerprint above (`92fcd59c…`) and this one
(`67745e62…`) are **different conventions over the same 28 nodes** — the
fingerprint script emits `ids` and `outcomes` digests, and a digest quoted from a
different extractor is not comparable. The load-bearing fact is the node
**identity** delta, which is empty.

- `corepack pnpm build` after the ceiling change → **passed**,
  `dist/assets/index-DGoSeuIt.js` 74.38 kB.

CP10 mutation boundary: `python scripts/cp10_mutation_boundary_policy.py --judge`
over every planned path → **PASS**.

`python-multipart` had to be installed in this sandbox to import
`solspire/console_router.py` at all; that is an environment gap, not a repository
defect, and it affects `main` identically.

CP10 mutation boundary: `python scripts/cp10_mutation_boundary_policy.py --judge`
over every planned path → **PASS**.

## 6. Unknowns (preserved, not resolved)

- **No buyer, contact, demand, or pricing fact is verified by this surface.** It
  records what an operator types; it establishes no commercial truth. Every
  commercial field the operator leaves untouched remains the backend's `UNKNOWN`.
- **`evidence_status` / `evidence` have no verified write path from this UI.** The
  backend accepts both; no control was added, because asserting evidence from a
  capture form would misrepresent reconnaissance as proof.
- **The status vocabulary is transcribed, not enforced client-side beyond a
  membership check.** *Superseded at `8c0f5dd4`:* the client now enforces the
  reconnaissance ceiling as well — see §3a. The server still validates the full
  vocabulary, and the ceiling is the surface's own narrower rule.
- **MEASURED DEFECT 3 (backend, not repaired).** `BuyerReconManager.update_entry`
  validates `status.upper()` against `STATUSES` and then persists the original
  value: `PATCH {"status": "conversation"}` answers `200` and stores
  `"conversation"`, which is outside the declared vocabulary. `create_entry`
  normalizes; `update_entry` does not. Pinned by
  `test_update_does_not_normalize_a_lowercase_status` with
  `test_create_normalizes_a_lowercase_status` as the control. `solspire/buyer_recon.py`
  is byte-identical to `main`; repairing it is a separate bounded change needing
  its own authorization (`SHARED-CONTRACTS` §1/§7.1).
- **Runtime observation of this UI is NOT CLAIMED.** The build and the tests pass;
  no browser or deployed-runtime observation was made in this pass.
- **Production deployment and acceptance are NOT CLAIMED.**

## 7. Next task (one, bounded)

The next verified Opportunity Radar capability on this branch's successor: the
`evidence_status` / `evidence` capture path, if and only if a handler that records
evidence with an owner- and board-scoped contract is independently verified. Until
then it stays visibly unwired rather than approximated.
