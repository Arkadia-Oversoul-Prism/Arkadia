# ARK-VSR-2026-10-22 — production deployment verification

**Released by human authorization** (explicit confirmation to publish, merge, and verify).
This record documents what was released and what was actually observed in production.

## Release chain

| Step | Value |
|---|---|
| Base before merge | `3cd81f76d0149a8a821a5152813ac50a68144b0e` (= `origin/main`, verified current) |
| Candidate | `c0d888aae52f79272915ddffd26d1af43bf8a552`, tree `b44acdf1b64b72bc35b65ad3a5c861731ee3e153` |
| PR | #558 (6 commits, 7 files) |
| CI on head | **15/15 check-runs `success`** (incl. `console-contract`, `frontend`, `test`, `boot-syntax`, `Full-history secret scan`) |
| CP10 mutation boundary | PASS on all 7 changed paths |
| Merge | **merge commit** `68403b9ea8e2ba16ade0d1b08418453a79b9dcb7` (repo convention; `main` is merge-commit history) |
| `main` after merge | `68403b9e` |
| Production `source_revision` | `68403b9e…` — **observed**, `revision_conflict: false` |

Deployment identity is established by the runtime's own read-only probe
(`GET /api/version`), which reported the pre-merge revision `3cd81f76` and then `68403b9e`
after the deploy completed. That is a source↔runtime consistency observation, not a
claim that the deployment is otherwise healthy.

## Served-artifact verification

| Check | Result |
|---|---|
| Served bundle asset | `assets/index-H_k_9bm6.js`, HTTP 200, 144,875 B |
| sha256 vs. a local build of the candidate | **byte-identical** (`3ab0e8505cb1863f749392f92c08fe2ef2e2dbee3f6d4851…`) |
| sha256 vs. a local build of unfixed `main` | **differs** (`951727889039b0c8b60138e92e011dd6820d38cc3de4baf6…`) |
| Marker `Primary navigation (mobile)` | 1 |
| Marker `ResizeObserver` | 1 |
| Marker `min-w-0 break-words` | 1 |
| Control `scrollIntoView` (must be absent) | **0** |

The served artifact is the candidate's build, not the pre-repair build. Note that the local
build compared was taken at tree `bd52aa7d` while the merged tree is `b44acdf1`; those trees
differ only in two docs and one test file (`git diff --name-only` → 3 paths, **0** under
`web/arkadia_console/`), so identical build output is expected rather than coincidental.

## Live production UI — Chromium, 390x844

Measured against `https://arkadia-qzu4.onrender.com` after the deploy. Raw capture:
`measurements/OUTPUT-PRODUCTION-VERIFIED.json`.

| Route (deep-link load) | Active item visible | `scrollLeft` | `<h1>` |
|---|---|---|---|
| `/` | **yes** | 0 | ARKADIA |
| `/about` | **yes** | 409 | About Arkadia |
| `/weaver` | **yes** | 339 | Protected surface |
| `/knowledge` | **yes** | 261 | Protected surface |
| `/enterprise` | **yes** | 158 | Protected surface |
| `/engineering-lab` | **yes** | 63 | Protected surface |

| Viewport resize | Active item visible | `scrollLeft` |
|---|---|---|
| 700→400 | **yes** | 399 |
| 600→360 | **yes** | 439 |
| 390→320 | **yes** | 479 |
| 767→300 | **yes** | 499 |

History navigation: click About (`scrollLeft 409`) → `go_back()` to Home → `scrollLeft 0`,
Home visible. **6/6 routes, 4/4 resizes, 0 JS page errors.**

These are the same numbers the local A/B produced for the candidate, now observed on the
canonical origin rather than a local preview — so the earlier "no deployment-identity
observation" limitation in `REVIEW-DECISION.md` is now closed for this revision.

## Still not established

- **Chromium only.** No Firefox, WebKit, or physical device.
- **No screen-reader or reduced-motion verification.**
- **VSR-002 was not re-measured in production.** The served bundle carries the repaired
  `min-w-0 break-words`, but no live page currently renders a token long enough to overflow,
  so the fix is verified by artifact + local A/B, not by a production overflow measurement.
- **Four routes render `Protected surface`** at the `<h1>`, i.e. they are auth-gated for an
  anonymous visitor. The nav-reveal measurement is still valid there (the strip renders), but
  the *content* of those surfaces was not exercised.
- **The 8 pre-existing full-suite failures and 1 collection error are unchanged** and were
  not repaired.
