# Open PR disposition record — 2026-10-15

## Authority and release boundary

Observed against repository state after merge of #545. Current `main` is
`04e1b83b89e51a994af68b529a1076665f9b3ae5` (merge of #545). Render auto-deploys
`main`; **merging any candidate is a production release**. This record does not
authorize a merge or deployment.

The 30 open PRs below were inspected for current head/base metadata, changed-file
overlap, and the latest available PR-triggered check runs on the reported head.
The heads are not rebased onto current `main`; green historical checks do not
establish current-base eligibility. “Integrate” here means the intended disposition
after fresh-base validation, not permission to merge.

## Per-PR record

| PR | Exact head SHA | Recorded base SHA | Changed-file overlap / concern | Latest reported checks | Disposition |
|---|---|---|---|---|---|
| #543 | `1a4b71aa37c38bcd00001d2e2b7c0b7530d5055b` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Overlaps #542 at `api/knowledge_routes.py` | 8/8 success | **Combine** with #542; retest timeline and graph scope together |
| #542 | `934037d9b892fe5604378eedc5485aa52c6d436f` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Overlaps #543 at `api/knowledge_routes.py` | 8/8 success | **Combine** with #543; revalidate accessible-subgraph behavior |
| #541 | `c9a96a03ee445a37db64e2493bfc251695c14c54` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Weaver approval-ledger UI and tests; no changed-file overlap with #536 | 9/9 success | **Integrate candidate** after fresh-base UI/tests and exact-head checks |
| #539 | `4335db3cb28f56029235b2ab2d0d31e8ced68c19` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Lane-state evidence reconstruction; not a runtime implementation substitute | External beta validation failed; other reported checks pass | **Repair** failed external beta gate; hold evidence claim until fixed |
| #537 | `8f6cb08a19bc8511790d10e13fa77919cd060c34` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Independent search visibility boundary in `knowledge/search.py` | 6/6 reported checks success | **Integrate candidate** after current-base tests and authorization-scope review |
| #536 | `5490b0b52d623c9ca60896d8ce8ec96bdb7d7638` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | Lab trace/run-artifact join; #525 also touches Lab work-loop surface but not same changed paths | 9/9 success | **Combine/reconcile** with #525; preserve one canonical work-loop/read model |
| #535 | `8b6eadd77aa1751efd2bc3b69722a1af8e8e1c72` | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` | EAA/dispatch composition; depends on #502/#508/#500 chain | 14/15 success; Provider Routing Verification failed | **Hold and repair/rebase**; fail closed until provider-routing baseline and exact-SHA chain are proved |
| #534 | `fb9bee79378d22f7f27b873959b92a471d3ce133` | `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1` | Overlaps #527 at `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | 9/9 success | **Combine** with #527; resolve stale base and contract semantics together |
| #532 | `aec31cb143724953a4c6209df2cb96a45e004f4b` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Arkana thread UTC timestamp semantics | 9/9 success | **Combine/revalidate** with #531 thread-history batch |
| #531 | `d0a8902d88e8fb5941a8639a1c9106c7b712b2e9` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Arkana project-turn visibility; related thread-history surface to #532 | 8/8 success | **Combine/revalidate** with #532; check visibility and timestamps end-to-end |
| #529 | `95eb5b7b0134ab44fd8ccdf3b9257032fc7aaa77` | `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1` | Lens-strip keyboard/landmark changes overlap UI shell CSS with navigation batch | 9/9 success | **Combine** with #505/#507 only after inspecting actual shared navigation contract |
| #528 | `e162371df67b52769ce291fe71407875386ea438` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | NovaNet echoes completeness, UI and test | 9/9 success | **Integrate candidate** after current-base tests |
| #527 | `c8320003b423149402867c54fa78abe5754b02ce` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Overlaps #534 at `knowledgeContracts.ts` | 9/9 success | **Combine** with #534; preserve provenance and status contract in one UI contract |
| #526 | `cb868ce4ade47c7c74fdd4666b47739e7888b0f2` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Graph traversal edge de-duplication; distinct from graph analytics/provenance | 6/6 success | **Integrate candidate** after graph regression suite on current base |
| #525 | `daef33c4d0535c392bc4a54e228471a1c432cf08` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Lab work-loop/read model; composition must respect canonical Lab loop already merged through #533 | 9/9 success | **Hold / combine** with #536; close only if exact diff proves redundant |
| #523 | `309f7c8f9d89d8b2b1c1aba2d70678ad93caa888` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | 403 authorization refusal presentation; console UI contract | 9/9 success | **Integrate candidate** after current-base auth-state tests |
| #522 | `dcdff997d08cd2cf4cb98ef61e9422020acbf8f6` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | Home identity-aware entry action | 9/9 success | **Integrate candidate** after current-base route and identity tests |
| #521 | `0765edd50389550236716f24f8960e7867d61c28` | `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` | SolSpire control-plane UI; shared endpoint/type contract surface | 9/9 success | **Integrate candidate** after current-base contract and auth checks |
| #516 | `dc91354eae3dca6ef98308f9fbd7f9cf569d0ff3` | `dfbd2304db27746b22f0cda9b6961d1e37fda313` | Shell document-title behavior; shell shared with #514/#515 | 9/9 success | **Combine/revalidate** with #514/#515 UI batch |
| #515 | `757cc6772dd6c60925952ec1fd24e7db4f7a6bf5` | `dfbd2304db27746b22f0cda9b6961d1e37fda313` | Arkana response provenance; modifies Arkana page | 9/9 success | **Combine/revalidate** with #514/#516; avoid overwriting current page behavior |
| #514 | `e48cbf2620ad1d0f88bbaaf8f275d74d10319b5b` | `dfbd2304db27746b22f0cda9b6961d1e37fda313` | App-level error boundary; shell/page integration | 9/9 success; PR reported non-mergeable | **Repair/rebase** with #515/#516 and validate failure behavior |
| #508 | `071ecd8c5f3b9a0c76c80bcf7f156c50aec4a2cb` | `ef82cb9e2d05f3f48bf91fcb0abf0aeacd11fb52` | Stacked on #502; read-only GitHub evidence adapter | 5/6 success; Provider Routing Verification failed | **Hold**; rebase on accepted EAA base, verify exact-SHA reviewer/authority binding; fail closed |
| #507 | `3a19810ea4b795133f9eb80eddca2f06f20b37e7` | `49809f45274f2f81b24e01fefdfb3009e8717495` | Test-only legacy-route guard overlaps #505's route alias implementation | 4/4 reported checks success | **Combine** with #505; retain tests only if they assert the final router behavior |
| #505 | `8cb030c03886c6943cc0c7003ff8afc5342bb96d` | `49809f45274f2f81b24e01fefdfb3009e8717495` | Legacy inbound aliases in router; #507 guard tests | 9/9 success | **Combine** with #507; validate alias safety on current route tree |
| #503 | `37e89b4aa2dc743257acf0195e77fc055be95a96` | `49809f45274f2f81b24e01fefdfb3009e8717495` | EAA baseline workflow | CI Gate Trigger Coverage failed; 5 other reported checks success | **Repair** workflow trigger coverage before EAA composition proceeds |
| #502 | `ef82cb9e2d05f3f48bf91fcb0abf0aeacd11fb52` | `49809f45274f2f81b24e01fefdfb3009e8717495` | EAA protocol/schema/workflow; parent for #508 and #535 chain | 10/11 success; Provider Routing Verification failed | **Repair/rebase**; do not grant acceptance authority through boolean or unbound evidence |
| #500 | `7640bbad51bdafe00ed84d59bbc0178dd734f44c` | `49809f45274f2f81b24e01fefdfb3009e8717495` | GATE-L4 dispatch contract; EAA/dispatch chain | 10/11 success; Provider Routing Verification failed | **Hold and repair/rebase**; discovery/run-inspection only, no merge/deploy capability |
| #499 | `d04ba3b608691bb26a096fd2a2d025939360ff2d` | `49809f45274f2f81b24e01fefdfb3009e8717495` | Weaver status truthfulness and router schema | 8/9 success; Provider Routing Verification failed | **Repair/rebase**; preserve distinction between merged, accepted, and human-gated |
| #496 | `967f30d9016543ee895bdb7a5119c08fab2e9e5f` | `49809f45274f2f81b24e01fefdfb3009e8717495` | Docs/shared contracts plus secret-scan config; evidence may be stale | 4/4 success | **Hold for evidence refresh**; retain only claims grounded at current revision |
| #482 | `0cc7c9e766d80e4a1a6028cbd611bdd7be063a10` | `ee684fffe6f4f1670a7d9e8928e9c5fc323b4c2a` | Provider-routing workflow wiring and history-depth CI | 8/9 success; Provider Routing Verification failed | **Repair/rebase**; compare failure node fingerprint against current main before classifying as baseline debt |

## Cross-PR overlap map

1. **Knowledge routes:** #542 + #543 both edit `api/knowledge_routes.py`; combine and run the graph-owner-scope and timeline-boundary suites together.
2. **Knowledge graph contracts:** #527 + #534 both edit `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts`; combine after deciding the final status/provenance contract. #526 is a separate graph traversal repair and should be validated with them, not blindly merged.
3. **Arkana thread history:** #531 + #532 are one end-to-end area (visibility + UTC truth), even though their direct changed paths differ.
4. **Legacy navigation:** #505 + #507; #529 touches the shared lens strip and CSS, so include it in navigation integration testing but don't assume identical implementation scope.
5. **Lab/Weaver:** #525 + #536 share the Lab work-loop/read-model concern; #541 changes the Weaver approval ledger and is adjacent but has separate changed files.
6. **Arkana/shell recovery:** #514 + #515 + #516 must be integrated as a batch due to app/page/shell behavior.
7. **EAA/dispatch:** #502 is the EAA parent; #508 is stacked on it; #500 is dispatch; #503 is CI baseline wiring; #499 is a related status-semantics fix; #535 is the attempted composition. #482 is a provider-routing workflow repair. No component may be accepted while the provider boundary or exact-SHA authority binding is unproven.

## Release-batch gate

Before proposing one release batch:
- refresh/rebase each retained candidate on `04e1b83b89e51a994af68b529a1076665f9b3ae5` or its resulting validated composition;
- run all relevant tests and PR-triggered checks on exact candidate heads;
- compare any provider-routing failure by node identity/fingerprint on the same current base; no weakening or suppression;
- close as superseded only after the replacement contains the change and tests, with a comment recording that evidence;
- re-fetch `main` and each candidate head immediately before asking for release authorization;
- do not merge any release-batch PR without explicit authorization, because merge auto-deploys to Render.


## Candidate compositions created after the initial inventory

All are draft candidates on current main `04e1b83b89e51a994af68b529a1076665f9b3ae5`; none is merged or released.

| Candidate PR | Exact head | Sources | Current gate state | Decision |
|---|---|---|---|---|
| [#547](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/547) | `1a2dd149250b13a3d858fa853a2cbe64d73ba15c` | #531 + #532 | 16 checks; backend, frontend, test, console-contract, production-read-only-probe and other checks passed; `validate` was in progress at last read | **Hold for final check completion**, then review exact-head results |
| [#548](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/548) | `e219acd28adef1376d92429566e4226df443d606` | #537 + #526 | 10 checks; 9 passed, `lane-doc-currency` failed | **Repair** documentation-currency gate; code merge blocked until exact-head gate is green |
| [#549](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/549) | `a0aecb2631333e4b93072a456dacab4c36ae4745` | #542 + #543 | 11 checks; several were still in progress at last read | **Hold for exact-head CI**; specifically verify owner-scope SQL and limit floors |
| [#550](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/550) | `dc7619caa44fee91215fc6a5160a12853a9dba6d` | #514 + #515 + #516 | Newly opened; checks not yet fully observed | **Hold for exact-head CI**; manually integrated error boundary into current `App.tsx` to preserve identity-aware navigation |
| [#551](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/551) | `367037d12ada094f44acd4205b048049385c93bb` | #505 + #507 + #529 | Newly opened; checks not yet fully observed | **Hold for exact-head CI**; current `tests/test_console_shell_nav_contract.py` was preserved because stale patch context did not apply |

### Still not composed

- **#527 + #534** share `knowledgeContracts.ts`. Both patch orders failed to apply cleanly against current `main`; no combined candidate was published. **Hold for semantic reconciliation**, do not copy either stale file wholesale.
- **EAA/dispatch (#482, #499, #500, #502, #503, #508, #535)** remains uncomposed. #503 has `CI Gate Trigger Coverage` failure; #502/#500/#508/#535 have provider-routing failures on their reported heads. Current-base node-fingerprint comparison and exact-SHA authority review are required before a combined candidate can be considered.
- The initial 30-row table is the inventory of the original open queue at the time it was fetched. The five candidates above are new queue entries and are recorded separately so they do not silently inflate or obscure the original dispositions.


## Exact-head candidate status refresh — 2026-10-15T20:26Z

All candidate heads below are based on `04e1b83b89e51a994af68b529a1076665f9b3ae5`. Check counts are live GitHub check-runs observed at this refresh, not inferred from legacy combined status.

| PR | Exact head SHA | Check-runs | Current result | Disposition |
|---|---|---:|---|---|
| #546 disposition record | `baa53c0c1f866b7bd666b14fb18ba20caf3780fe` | 6 | 6 success | **Hold** as documentation candidate; no code/release effect |
| #547 Arkana thread visibility + UTC | `1a2dd149250b13a3d858fa853a2cbe64d73ba15c` | 16 | 16 success | **Eligible for review**; source #531/#532 remain open until disposition after release decision |
| #548 Knowledge search + traversal | `574605dce6f6791b05dd726a606ca2779e1f1ef6` | 10 | 10 success after refreshing `lane-state.json` and rebinding Lane 2 deferral to open #528 | **Eligible for review**; source #526/#537 remain open pending release |
| #549 Knowledge graph owner scope + timeline bounds | `a0aecb2631333e4b93072a456dacab4c36ae4745` | 11 | 11 success | **Eligible for review**; source #542/#543 remain open pending release |
| #550 console error boundary + Arkana provenance + document title | `dc7619caa44fee91215fc6a5160a12853a9dba6d` | 15 | 15 success | **Eligible for review**; current `App.tsx` identity-aware navigation preserved |
| #551 legacy aliases + accessible lens navigation | `6d592a1825a29c745f61ce61b5d909c78585fe01` | 15 | 15 success after removing `/gate`, `/living-gate`, `/home`, `/knowledge-os` from the recorded gap set now covered by aliases | **Eligible for review**; source #505/#507/#529 remain open pending release |
| #552 EAA baseline trigger coverage | `1ffcfb3824cc6a145bd8328e271b4397c1daca5d` | 9 | 9 success; baseline workflow pinned to historical SHA unchanged | **Eligible for review** as a bounded CI wiring repair; does not clear provider-routing failures |
| #553 EAA/dispatch/read-only evidence composition | `06cb8ad17429137d7f455e8f8cf3ab1d02e19be2` | 19 | 17 success; baseline + provider-routing still running at refresh | **Hold** until both complete; provider boundary remains fail-closed |
| #554 Knowledge status + graph provenance contracts | `b2dc00872ff2ade92cbba412dd51b5fe4e730d75` | 13 | 2 success; remaining exact-head checks running after a TypeScript syntax repair | **Hold** until all checks complete; the prior head failed because provenance interface documentation was inserted inside the preceding JSDoc, now relocated |
| #555 Weaver withdrawal + Lab run/artifact trace | `32251bc960f0877aeb01cec699df73a7053b8221` | 16 | 12 success; native workflow, console-contract, canonical Render image, and validate still running | **Hold** until all checks complete; #525 remains separately held |

## Release posture

No candidate in this table is merged. Green PR-triggered checks establish engineering evidence on the exact candidate head, not production behavior. The coherent release batch should be assembled only after the remaining running checks finish, #554 is green, and #553's provider-routing result is adjudicated against a same-current-base node fingerprint without weakening the gate. Since `main` auto-deploys to Render, no merge has been performed.


## Queue state transitions after the 20:26Z refresh

- **#528 closed unmerged as superseded.** Its current-main NovaNet implementation already contains the same bounded public echoes limit, public total label, and truncation notice; its test file blob is identical to current `main` (`c9a1f6dff972ecb8da70107053d277f8a90b91b6`). Comment posted on #528.
- **#503 closed unmerged as superseded by #552.** The trigger-coverage repair retains the exact-base baseline workflow and expands the path filter to cover `tests/test_autonomy.py` plus the EAA/dispatch/provider-routing inputs. #552's exact head had 9/9 checks pass. Comment posted on #503.
- #538 and #544 remain closed unmerged as superseded by #545.
- #525 remains open/held. Its old `LabWorkLoop.tsx` approach is not being restored over the canonical work-loop composition; no exact evidence yet proves the desired Weaver read model is already present.
- #527/#534's shared contract was composed as #554. Its first candidate head failed because the provenance interface was inserted inside the preceding JSDoc. That syntax placement was corrected; the latest head is `da7e0279457017200b7eb4ed9f25a0d48bbaf7d1`, with 14/15 checks successful and only `validate` still running at this refresh.
- #551's stale legacy-gap entries were removed only for the four paths now aliased by #505; the new exact head passed 15/15 checks.
- #553 now includes #482's full-history provider-routing checkout and guard. Latest head `b0e20e9e6524066c7522ab351d4cf0310a143c22`: 17/19 checks passed; `baseline` and `provider-routing` remained in progress. The previous provider-routing run reported 13 failed nodes, 3,332 passed, 21 skipped, and 1 collection error. This remains **not mergeable by policy** until the current exact-head provider-routing run completes and its failures are attributed without weakening the gate.
- #555 Weaver/Lab candidate passed 16/16 reported checks at `32251bc960f0877aeb01cec699df73a7053b8221`.

No code candidate has been merged. These transitions reduce duplicate queue entries but do not authorize production release.


## Exact-head status refresh — 2026-10-15T20:34Z

| PR | Exact head SHA | Check-runs | Result | Decision |
|---|---|---:|---|---|
| #553 EAA/dispatch + full-history provider gate | `b0e20e9e6524066c7522ab351d4cf0310a143c22` | 19 | 17 success; `provider-routing` and `baseline` still running | **Hold**; the full-history repair is included, but provider boundary is not accepted until the current exact-head gate finishes |
| #554 Knowledge status/provenance contracts | `da7e0279457017200b7eb4ed9f25a0d48bbaf7d1` | 15 | 15 success after correcting the JSDoc placement | **Eligible for review** |
| #555 Weaver withdrawal + Lab run/artifact trace | `32251bc960f0877aeb01cec699df73a7053b8221` | 16 | 16 success | **Eligible for review** |
| #556 Home + SolSpire + authorization-state recovery | `01e9647c8464044b41e14b72f1691125453054ca` | 13 | checks newly queued | **Hold** until exact-head checks finish |

#556 combines the previously separate #521/#522/#523 changes while preserving the current-main `endpoints.ts` and applying #521's patch to it. #528 is now closed as superseded because its code and test are already on current `main`; it is not part of the release batch.

## Release batch candidate set

Subject to completion of the listed gates, the coherent review batch is:
- #547 Arkana visibility + UTC thread history — 16/16 pass
- #548 Knowledge search visibility + graph traversal — 10/10 pass
- #549 Knowledge graph owner scope + bounded timeline — 11/11 pass
- #550 error boundary + Arkana provenance + document title — 15/15 pass
- #551 legacy aliases + accessible lens navigation — 15/15 pass
- #554 Knowledge status-read + graph provenance contracts — 15/15 pass
- #555 Weaver withdrawal + Lab trace — 16/16 pass
- #556 Home + SolSpire + authorization state — awaiting checks
- #552 EAA baseline trigger coverage — 9/9 pass, but its functionality is also incorporated into #553
- #553 EAA/dispatch chain — held until exact-head provider-routing and baseline checks complete and provider-routing failure attribution is acceptable

#525 remains outside the batch until its old work-loop implementation is reconciled with the canonical #533 composition. #539 remains held on the failed external beta validation. The original split source PRs stay open until the replacement candidate is accepted and a release is explicitly authorized; do not close them early merely because a draft candidate exists.


## Final gate refresh — 2026-10-15T20:37Z

- #556 current head `01e9647c8464044b41e14b72f1691125453054ca`: **15/15 checks passed**.
- #554 current head `da7e0279457017200b7eb4ed9f25a0d48bbaf7d1`: **15/15 checks passed**.
- #555 current head `32251bc960f0877aeb01cec699df73a7053b8221`: **16/16 checks passed**.
- #553 current head `62160d6ba0e6c7b22db7b4909c87c6cc0755b4ad`: the second full-history provider-routing pass is running after repairing the economic-seam/SG-02 trigger and history-depth inputs, and correcting the reporting exemption assertion to step-level semantics. Do not infer a pass from the earlier run.
- #539 external beta validation was rerun on the same source SHA `4335db3cb28f56029235b2ab2d0d31e8ced68c19`; the rerun is in progress. Until it completes, keep #539 held rather than classifying the prior failure as environmental.
- The current-base candidate set now includes #556 for Home/SolSpire/auth recovery. No source PRs were closed except #528 and #503 where supersession was established and commented. No code candidate has been merged or deployed.


## Additional source-queue reconciliation — 2026-10-15T20:44Z

- Source PRs #531, #532, #526, #537, #542, #543, #514, #515, #516, #507, #529, #527, #534, #536, #541, #521, #522, and #523 are now **closed unmerged as superseded** by the passing current-base candidates #547, #548, #549, #550, #551, #554, #555, and #556. Each closure has a comment naming the replacement PR and exact passing head. Their branches remain available.
- #505 remains **open/held** because its unique updates to `tests/test_console_shell_nav_contract.py` had not been included in #551. Those test changes have now been manually reconciled into #551 while preserving the current-main test helpers; #551's new head and checks are pending. If those checks pass, #505 can be closed as superseded by #551.
- #539's external beta validation passed on same-SHA rerun (attempt 2), but its evidence snapshot remains stale at base `7580bd8f` with historical open-PR counts 39/45. It stays **open/held for evidence refresh**, not closed as redundant.
- Live open queue at this refresh: **21 PRs**. It consists of the ten current-base candidates/docs entries #546–#556 (with #546 documentation-only), plus held source work #482, #496, #499, #500, #502, #505, #508, #525, #535, and #539. #503 and #528 are closed unmerged as superseded; #538/#544 remain closed unmerged as superseded by #545.
- #553's second provider-routing run exposed 11 failures, 3,361 passes, 16 skips, and one collection error; a third current-base repair now addresses the exact remaining history-guard path-filter failures. The new head `99763d3ff1d74360630d569a81e0ce2095f197d8` is running CI. Do not merge the EAA chain unless its provider-routing boundary is green on this exact head and remaining full-suite debt is explicitly adjudicated without weakening gates.


## Exact-head reconciliation refresh — 2026-10-16

This section supersedes earlier status claims wherever the exact head differs. Current `main` remains `04e1b83b89e51a994af68b529a1076665f9b3ae5`; no release merge was performed in this pass.

### Current-base candidate status

| PR | Exact head SHA | Base SHA | Latest observed checks | Disposition |
|---|---|---|---|---|
| #547 Arkana thread visibility + UTC history | `1a2dd149250b13a3d858fa853a2cbe64d73ba15c` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 16/16 completed successfully | Review-eligible; production acceptance not claimed |
| #548 Knowledge search visibility + graph traversal | `7c085b45ab3c55c50ffc69ce40d07ccc86e39a01` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | New checks queued/in progress after lane-state repair | Hold until exact-head CI passes; #528 dependency has been removed from the snapshot and lane 2 is now represented as idle |
| #549 Knowledge graph owner scope + bounded timeline | `a0aecb2631333e4b93072a456dacab4c36ae4745` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 11/11 completed successfully | Review-eligible |
| #550 Console error boundary + Arkana provenance + title recovery | `dc7619caa44fee91215fc6a5160a12853a9dba6d` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 15/15 completed successfully | Review-eligible |
| #551 Legacy aliases + accessible lens navigation | `330907c05a629155e38fdd2584c505d3340ec73c` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 15/15 completed successfully | Review-eligible; route/test coverage rechecked against #505 |
| #554 Knowledge status + graph provenance contracts | `da7e0279457017200b7eb4ed9f25a0d48bbaf7d1` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 15/15 completed successfully | Review-eligible |
| #555 Weaver withdrawal + Lab run/artifact trace | `32251bc960f0877aeb01cec699df73a7053b8221` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 16/16 completed successfully | Review-eligible |
| #556 Home + SolSpire + authorization state | `01e9647c8464044b41e14b72f1691125453054ca` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | 15/15 completed successfully | Review-eligible; authorization-state contract checks passed, no runtime acceptance claimed |
| #553 EAA/dispatch + read-only evidence chain | `c034fe4cb10bcfa5763ed4e6a77cb86109a3b8ce` | `04e1b83b89e51a994af68b529a1076665f9b3ae5` | New exact-head run in progress | **Hold**; provider-routing remains fail-closed until exact-head run and remaining product-contract failures are adjudicated |

### Repairs and queue transitions

- #548: removed the stale lane-2 deferral to closed #528. The snapshot now records lane 2 as `idle` with no open lane PR; the guard and tests explicitly support that state instead of inventing a live owner. This is a candidate-branch repair; its fresh checks have not yet completed.
- #553: added `CURRENT_STATE.md` to the relevant path filters in `.github/workflows/economic-seam-engine.yml`, `.github/workflows/provider-routing.yml`, and `.github/workflows/sg-02-fe-2-v.yml`. Repair commit/head: `c034fe4cb10bcfa5763ed4e6a77cb86109a3b8ce`. The prior exact-head run on `99763d3ff1d74360630d569a81e0ce2095f197d8` failed with 11 test failures and one collection error. Besides the now-addressed three path-filter omissions, it exposed independent product-contract failures in Lab auth/mutation-route inventory, identity-spine copy, Arkana shared-session identity, SolSpire governance, and execution-runtime mutation policy. Those failures are not waived; the new exact-head run must be inspected before any eligibility decision.
- #551: exact-head changed-file and test-name comparison confirms every test function from #505 is present in #551's `tests/test_console_shell_nav_contract.py`, with four additional alias-namespace and route-round-trip negative controls. The current candidate's router contains the legacy alias implementation. #505 was commented and closed unmerged as superseded by #551; no production release was authorized.
- #556: exact-head check runs are all successful, including console contract and authorization-state checks. This is source-level CI evidence only; no live authorization/runtime acceptance is claimed.
- #528 and #503 remain closed unmerged as superseded. #538 and #544 are closed unmerged as superseded by merged #545. #539 remains historical evidence only until its lane snapshot is refreshed against the current queue.
- #525 remains held pending reconciliation with canonical Engineering Lab composition. #482, #496, #499, #500, #502, #508, #535 and any other still-open source PRs must not be closed merely because a composed candidate exists; require exact changed-file/content coverage plus candidate checks first.

### Release decision

No code candidate has been merged in this refresh. The review batch is #547, #549, #550, #551, #554, #555, and #556, with #548 pending fresh CI and #553 explicitly excluded pending provider-boundary adjudication. This is a **review-eligible batch, not an implicit release approval**. Merge to `main` remains a production release and requires explicit authorization.
