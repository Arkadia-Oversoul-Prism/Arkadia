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
