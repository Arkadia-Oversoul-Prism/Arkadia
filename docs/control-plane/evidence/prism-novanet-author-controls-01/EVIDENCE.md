# NovaNet public field — author-only edit / delete controls

Workstream 2 (NovaNet & Project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, shared contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: reconcile an archived Prism **product capability** the console
field lacks — the author-only Edit / Delete controls over a public transmission.
The console field (`data-testid="novanet-public-field"`, `/api/transmissions`)
was read-only while the archived Prism field offered these controls. The backend
contract is live and verified, so this is a reconciliation, not an invention.

Authority: human retains merge, production deployment, and acceptance. Nothing
here claims any of the three.

Successor slice to `prism-opportunity-notes-render-01` (same branch/PR #492,
draft). It adds one feature-local component and one page mount; it adds **no**
route, **no** endpoint-registry entry, and **no** authority.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, base `main`).
- `origin/main` at the start of this pass:
  `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`.
- Branch head before this slice: `44b854e2` (`prism-opportunity-notes-render-01`).
- PR #492 state (read-only, `GET /pulls/492`): `open`, `merged: false`,
  head `44b854e2`, base `49809f45`.
- Environment: node `v24.21.0`, pnpm `10.26.1`.

## 1. The precondition — the mutation contract is served (measured)

Before wiring a control, the handler was read (`api/transmissions.py`):

- `@router.patch("/api/transmissions/{post_id}")` -> `edit_transmission`
  returns `403 {"detail": "only the author can edit this post"}` for a non-owner
  and `401` for an anonymous caller; the owner is resolved from
  `_get_current_user` / the stored `owner_uid`, never from the request body.
- `@router.delete("/api/transmissions/{post_id}")` -> `delete_transmission`
  enforces the same boundary (`"only the author can delete this post"`).

So the archive's client-side `myUid === post.owner_uid` gate mirrors a boundary
the backend already enforces. The UI offers the control only where the backend
would accept it, and never decides ownership itself.

## 2. What changed (bounded)

- **New** `web/arkadia_console/src/components/novaNet/AuthorControls.tsx` —
  author-only Edit / Delete for one transmission. Renders **nothing** when
  `isOwn` is false (`if (!isOwn) return null`), so a control that could only
  403 is never shown (directive §6). The mutation path is composed from the one
  registry — `` `${endpoints.transmissions}/${encodeURIComponent(postId)}` `` —
  never an inline literal (§3.1), and the id is percent-encoded so a value
  containing `/`, `?` or `#` cannot address a different route.
- **Edited** `web/arkadia_console/src/pages/NovaNetPage.tsx` — mounts
  `AuthorControls` per transmission, gated on
  `Boolean(myUid && t.owner_uid && myUid === t.owner_uid)` where `myUid` is the
  verified Firebase uid from the auth context; a successful mutation calls
  `field.reload` so the field re-reads what it changed.
- No shared file touched: `lib/endpoints.ts`, `lib/types.ts`, router, surfaces,
  `App.tsx` are unchanged (the registry member `endpoints.transmissions` is
  referenced, not restated).

## 3. Proof

- `corepack pnpm --dir web/arkadia_console build` (`tsc --noEmit && vite build`)
  -> clean (82 modules, built).
- `python -m pytest tests/test_prism_novanet_author_controls.py -q -rEf`
  -> **9 passed**.
- `python -m pytest tests/architecture -q -rEf` -> **11 passed**.
- Targeted regression (`test_console_endpoint_registry_contract.py`,
  `test_console_shell_nav_contract.py`, `test_prism_novanet_author_controls.py`,
  `test_prism_console_ci_wiring.py`) -> **87 passed**.
- `printf '<new test>\n' | python scripts/cp10_mutation_boundary_policy.py --judge`
  -> `Mutation boundary PASS`, exit 0.
- The console-contract gate (`prism-console-contract.yml`) does not name its
  guards explicitly — it derives its domain from `scripts/console_contract_domain.py`
  at test time, so the new guard enters the executed set by construction
  (domain 21 -> 22). No gate wiring edit is required or made.

The new guard carries a **negative control per behavioural claim** (ungated
control, control offered to a non-owner, inlined mutation path), applied by the
same detector that judges the live tree, so rewriting the component cannot
disarm it.

## 4. Unknowns / not claimed

- No runtime/browser observation of the control against the deployed origin: the
  proof here is source-level contract + build, matching the convention for
  console feature guards. Deployment/acceptance are **NOT CLAIMED**.
- The Edit control's inline textarea UX follows the archive's pattern; its exact
  copy is not asserted against the archived source (the archive is evidence, not
  a byte target).

## 5. Next bounded task on this lane

Reconcile the next archived NovaNet public-field capability **whose contract
measures cleanly against a verified handler** (e.g. reactions / repost, only if
a real handler is verified). Do not invent a capture path for a capability with
no verified write route.
