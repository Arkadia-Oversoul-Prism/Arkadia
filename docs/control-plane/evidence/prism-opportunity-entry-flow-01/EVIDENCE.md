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
| `tests/test_prism_opportunity_entry_flow.py` | **New.** 35 tests: backend write contract + executed frontend contract probe. |

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
- **No-op edits are explained, not sent.** Saving an unmodified form reports
  "No change to save" rather than issuing a write that records nothing.
- **A board switch clears the form and the locally held entries**, so an edit
  control can never address an entry id belonging to another project's board.

## 4. Tests

`python -m pytest tests/test_prism_opportunity_entry_flow.py -q` → **35 passed**.

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

### Negative controls (all present)

- A supplied commercial fact *is* recorded (proves the `UNKNOWN` pin is not vacuous).
- A declared status *is* accepted.
- The owner identity *is* what admits the write (same request, identity changed).
- The own-board edit still succeeds (the narrowing did not break the guarded path).
- The probe distinguishes a wrong body builder.

### Mutation check — the detectors bite (live, then restored)

Each mutation was applied to the working tree, the suite re-run, and the tree
restored. Restored byte-identically (`sha256sum` of all three files unchanged):

| Mutation | Result |
|---|---|
| Contract asserts `UNVERIFIED` commercial facts on the wire | 3 failed |
| Surface resolves transport itself (`fetch`) | 2 failed |
| Form trusts the draft instead of the server response | 1 failed |
| Edit body rewrites every field (non-partial PATCH) | 2 failed |

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
| branch | 27 failed, 2377 passed, 17 skipped, 1 error | `92fcd59cb4f0aee3249c93045c3d1ddd5bfd591c24d5b628db829c0fd1645048` (28 nodes) |

`comm -3` on the sorted node sets is **empty** — zero regression. The `+35
passed` is exactly this file's node count (`--collect-only` → 35). The 27
pre-existing failures and the `tests/test_autonomy.py` collection error (CE-01,
reserved to the sovereign) are unchanged by this pass and were not repaired here.

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
  membership check.** The server validates it; the client only offers declared
  values.
- **Runtime observation of this UI is NOT CLAIMED.** The build and the tests pass;
  no browser or deployed-runtime observation was made in this pass.
- **Production deployment and acceptance are NOT CLAIMED.**

## 7. Next task (one, bounded)

The next verified Opportunity Radar capability on this branch's successor: the
`evidence_status` / `evidence` capture path, if and only if a handler that records
evidence with an owner- and board-scoped contract is independently verified. Until
then it stays visibly unwired rather than approximated.
