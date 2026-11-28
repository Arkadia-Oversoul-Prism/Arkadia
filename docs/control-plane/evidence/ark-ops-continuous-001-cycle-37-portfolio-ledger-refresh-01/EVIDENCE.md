# ARK-OPS-CONTINUOUS-001 — cycle 37: portfolio ledger refreshed, and a fair selection that is not the repo we worked in

**Directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
**Pulse (UTC):** 2026-11-28T09:06 – 09:20
**Authority:** human-governed, evidence-bounded, fail-closed. `MERGE_AUTHORITY = NONE`.
**Outcome:** one bounded unit — the §3 ledger refreshed from live state — plus a newly
measured, unowned FSN defect recorded for the next pulse. No merge, no deployment, no
acceptance.

## 1. Fresh-sandbox reconstruction

Identity and access were re-verified rather than assumed. `gh auth status` reported
`You are not logged into any GitHub hosts` on the first call; the ambient `GH_TOKEN` was
unset. `export GH_TOKEN="$GITHUB_TOKEN"` (the 40-char `ghu_` OAuth token) authenticated as
`Arkadia-Oversoul-Prism`, and that identity is what every read below used.

| repository | default branch | head | head committed | pushed_at | open PRs | open issues |
|---|---|---|---|---|---|---|
| `Arkadia-Oversoul-Prism/sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e34685b06e2e1698cf9eb896b9720` | 2026-11-26T17:52:36Z | 2026-11-28T05:21:05Z | 4 | 1 |
| `Arkadia-Oversoul-Prism/family-safety-network` | `main` | `18c729735fd428622ea70b76571aa38e518a9774` | 2026-11-26T08:22:33Z | 2026-11-28T07:11:44Z | 12 | 7 |
| `Arkadia-Oversoul-Prism/Arkadia` | `main` | `8f746f9eab6df51733f6d43c8bab26af63eb6471` | 2026-11-27T00:13:03Z | 2026-11-28T07:12:49Z | 64 | 10 |

All three repositories are reachable, none archived, all with `admin/maintain/push`
permissions. No repository was omitted.

Arkadia's 64 PRs are **all drafts**; sonata's 4 and FSN's 12 likewise. Under GOV-04
(ACTIVE, `fd0a4fdc`) a draft is not merge-eligible — "drafts must be explicitly made ready
by their owner; no silent draft conversion" — so the delegated merge surface offered
nothing this pulse, and no merge was attempted.

## 2. The selection (re-derived, not remembered)

The contract forbids a remembered rotation sequence, so the selection was produced by the
ledger's own selector against live GitHub, not by arithmetic in prose:

```
$ PYTHONPATH=scripts python scripts/portfolio_state_refresh.py
sonata: VERIFIED branch=feature/sonata-tts-app head=7c4e6a64e39e pulls=4 issues=1 progress=2026-11-28T05:21:05Z
family-safety-network: VERIFIED branch=main head=18c729735fd4 pulls=12 issues=7 progress=2026-11-28T07:11:44Z
Arkadia: VERIFIED branch=main head=8f746f9eab6d pulls=64 issues=10 progress=2026-11-28T07:12:49Z
next: Arkadia-Oversoul-Prism/sonata -- oldest verified last_progress_at among unblocked
  repositories (2026-11-28T05:21:05Z); tie-break order Sonata -> FSN -> Arkadia
```

**The fair selection is Sonata.** That is recorded rather than quietly substituted: the
pulse's bounded implementation unit landed in Arkadia, and the divergence is stated here
instead of being resolved in favour of wherever work was convenient.

Why Sonata was not advanced, and why that is not a licence to invent a slice:

- Every actionable Sonata slice is **owned by an open draft** — S1 `#9` (`b9bbf845`),
  S4 `#10` (`e1f952a0`), engine retry `#11` (`f85e779b`), S3 document import `#12`
  (`206344da`). §8 forbids a parallel PR for a slice an open draft owns.
- The next **unowned** slice, S2 (a natural offline neural voice), needs a bundled
  licensed model file plus a physical-device measurement. Neither exists in this sandbox,
  and neither can be fabricated.
- This sandbox has **no JVM and no Android SDK**: `java`, `javac` and `kotlinc` are absent,
  `ANDROID_HOME` and `ANDROID_SDK_ROOT` are empty. Sonata's verification path is its CI,
  which `ci-evidence.log` at `7c4e6a64` records as 405 JUnit tests passing (236 app core
  + 169 narration core). A Kotlin change pushed from here would be **unverified at push**,
  which the contract's §9 forbids.

So Sonata is `COMPLETE_FOR_NOW` for **new** slices at this revision — not blocked in
principle, and deliberately not marked `blocked: true` in the cursor, because a permanent
block flag would starve Sonata of a future pulse that does carry a JDK.

## 3. The unit performed: the §3 ledger, refreshed from live state

`portfolio-state.json` is a **derived** artefact and had been measured at
`2026-11-28T07:12:30Z`. It was re-derived with the only thing allowed to write it:

```
$ PYTHONPATH=scripts python scripts/portfolio_state_refresh.py --write
wrote docs/control-plane/openhands/hourly-weaver/portfolio-state.json
```

The diff is 4 insertions / 4 deletions in one file: `derived_at` ->
`2026-11-28T09:09:41Z`, and Arkadia's `pushed_at`, `latest_open_pull.updated_at` and
`last_progress_at` advanced to `2026-11-28T07:12:49Z` / `07:12:57Z` / `07:12:49Z`. Sonata
and FSN rows are byte-identical, which is the expected shape: the only push between the
two measurements was this workstream's own.

`portfolio-cursor.json` (authored) records this pulse's judgements: Sonata's selection and
`COMPLETE_FOR_NOW` classification, the verification-environment exposure that keeps Sonata
out of reach here, FSN's newly measured defect (§4), and Arkadia's state.

## 4. A newly measured, unowned FSN defect

The cursor already carries a lesson that "every finding is owned" is **not** a safe
inference from an open-PR list. That lesson was applied by auditing rather than assuming,
and it found another unowned slice. Measured at FSN `main` `18c72973` (clone at
`/tmp/fsn`, `backend/`):

`DELETE /families/{family_id}/members/{member_id}/data` -> `routes.py::erase_member` ->
`retention.py::erase_member_data(db, member_id)` deletes:

- `EmergencyEvent` where `initiated_by_member_id == member_id`
- `LocationObservation` where `subject_member_id == member_id`
- `SharingSession` where `subject_member_id == member_id`
- `Device` where `member_id == member_id`

It does **not** touch `SharingSession.granted_to_member_id`, and it does **not** remove the
`FamilyMembership` row. Two consequences:

1. A session another member granted *to* the erased member survives erasure, and
   `authz.session_covers_viewer()` still accepts it (`granted_to_member_id == viewer.id`),
   so the erased member keeps live read access into another member's location.
2. The membership row survives, so `list_members` still lists the erased member.

The **account** path is not affected the same way: `erase_account_data` deletes the
memberships, and `granted_to_member_id` is `ON DELETE CASCADE`, so those grants cascade
away there. The gap is specific to the member-level path.

Coverage is absent, which is what makes this unowned rather than merely unrepaired:
`grep -rn "granted_to" tests/ --include=*.py` returns exactly one hit
(`tests/test_authorization.py:161`, a grant in an authorization test), and no erasure test
mentions it.

No open issue or draft carries this: `#26/#27` own the **account** path's identity
revocation, `#21/#20` the device-location read audit, `#16` the unthrottled routes,
`#12` audit immutability, `#15` the authz existence oracle, `#14/#13` the rate-limit bound,
`#17` the purge runner, `#19` the manifest boundary, `#23/#22` the TLS guard, `#25/#24` the
release checklist, `#18` F0 integration.

It was **not** implemented this pulse. The erasure tests are PostGIS-gated — 45 of FSN's 61
backend tests skip here with `connection to server at "localhost", port 5432 failed:
Connection refused` — so the repair could not be verified within the cycle ceiling. A
one-clause change plus a DB-backed test is the next pulse's unit, recorded in the cursor.

## 5. Tests and checks actually run

| check | result |
|---|---|
| `scripts/portfolio_state_refresh.py` (dry run, live GitHub) | 3/3 rows `VERIFIED`, selection printed |
| `scripts/portfolio_state_refresh.py --write` | wrote the derived state; 4/4 line diff in one file |
| FSN backend baseline, `python -m pytest -q` at `18c72973` | **16 passed, 45 skipped** (all skips are PostGIS-unavailable) |
| FSN audit greps | `granted_to` absent from every erasure test |

Not run, and not claimed: any Kotlin/Gradle compile or test (no JVM/SDK); any PostGIS-backed
FSN test (no database); any browser or runtime observation of a deployment; any CI run for
this commit at authoring time.

## 6. Boundaries observed

No merge. No push to `main`. No force-push. No draft converted to ready. No deployment or
production claim. No new PR — this unit updates the existing draft `#744`, its correct
owner. No branch deleted. Nothing was written to Sonata or FSN source.

## 7. Deterministic next action

- **Current state:** Arkadia `main` `8f746f9e`; PR `#744` (draft) carries the ledger,
  refreshed at `2026-11-28T09:09:41Z`. Sonata `7c4e6a64` (4 drafts). FSN `18c72973`
  (12 drafts, 7 issues).
- **Evidence:** §1–§5 above; `portfolio-state.json`; `portfolio-cursor.json`.
- **Blockers:** Sonata needs a JDK + Android SDK (or accepts CI-only verification) and its
  slices are owned; FSN's next slice needs a reachable PostGIS; all merges need a human and,
  for drafts, the owner's ready-mark.
- **Authorized next action:** resume at the selector — `python scripts/portfolio_state_refresh.py`
  — and if Sonata is still selected, take **only** an unowned slice with a real verification
  path; otherwise implement the FSN member-erasure clause (§4) in a pulse that has PostGIS.
- **Forbidden:** merging, marking a draft ready, deploying, duplicating a slice an open
  draft owns, or claiming the FSN defect is repaired.
- **Completion condition:** the selected slice is implemented **and** verified by a test that
  fails before the change and passes after it, with the node identity recorded.
