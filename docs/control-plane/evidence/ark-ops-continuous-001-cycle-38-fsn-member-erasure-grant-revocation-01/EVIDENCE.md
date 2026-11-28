# ARK-OPS-CONTINUOUS-001 — cycle 38: FSN's member erasure now ends the erased member's grants

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471` (Arkadia)
**Branch:** `gate-hygiene/portfolio-state-ledger-01`
**Pulse:** 2026-11-28T11:0xZ
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to any
canonical branch, no deployment, no acceptance, no draft conversion. The ledger's own PR #744 was
extended rather than duplicated.

This is an **implementation** record, so it takes the bare `…-cycle-NN` path. The work itself
landed in the selected repository (`family-safety-network`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json                                       (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json                                      (authored judgement)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-38-fsn-member-erasure-grant-revocation-01/EVIDENCE.md (new)
```

The cycle index (`…/ark-ops-continuous-001/LEDGER.md`) lives on `main` (merged by #705 at
`8f746f9e`) and this branch is behind it. Adding the cycle-38 row belongs to whoever next
reconciles the index; a second copy here would recreate the split-ledger problem the index exists
to fix.

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-28T11:06Z, not from memory. All three repositories were reachable with
the session token (`gh api repos/Arkadia-Oversoul-Prism/{Arkadia,sonata,family-safety-network}` ->
200; `sonata` default branch `feature/sonata-tts-app`, FSN `private: true`). Nothing was omitted.

| Repository | Default branch | Head | Open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 4 | 2026-11-28T10:29:33Z |
| `family-safety-network` | `main` | `18c729735fd4` | 12 | 2026-11-28T07:11:44Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 2026-11-28T09:10:55Z |

FSN was oldest, so the fairness rule selected it; the tie-break order was never reached. Selection
was derived by `scripts/portfolio_state_refresh.py` against live state, not by hand and not from the
committed ledger — the committed snapshot was taken at 09:09:41Z and had already been superseded by
the cycle-37 Sonata push.

## 2. Selected task — an issue measured but unowned

The FSN cursor's `next_legal_task` named **issue #28**, created by the previous pulse after measuring
that every other finding was carried by a draft. #28 had no owner: `#26/#27` own the account-path
identity revocation, `#12` audit immutability, `#16` unthrottled routes, `#21/#20` the location read
audit. So this pulse continued a real, measured, unowned slice rather than opening a parallel one.

## 3. The defect, and the verification that had been recorded as blocked

`retention.py::erase_member_data` deleted the member's own observations, emergency events, devices
and *subject-side* sessions. It never filtered on `SharingSession.granted_to_member_id`, and never
touched the `FamilyMembership` row. An erased member therefore:

1. kept a live `scope='member'` read grant into another member's location, and
2. stayed listed by `GET /families/{id}/members`.

The prior pulse recorded this as **verified absent coverage but not repairable**, because the erasure
tests are PostGIS-gated and reported `45 of 61 skip`. That blocker was an **unprovisioned
environment**, not an inaccessible dependency:

```
sudo dockerd &
sudo docker run -d --name fsn-db -e POSTGRES_USER=fsn -e POSTGRES_PASSWORD=fsn \
     -e POSTGRES_DB=fsn -p 5432:5432 postgis/postgis:15-3.3
cd backend && alembic upgrade head
```

-> `PostGIS 3.3`, and `pytest tests/ -q` on **unmodified** `main` `18c72973` gives **61 passed** —
the same baseline CI records. The gate is reachable; the earlier `45 skipped` was a statement about
the sandbox. This supersedes that cursor entry.

## 4. The repair

```text
erase_member_data
  + revoke every SharingSession where granted_to_member_id == member_id and revoked_at IS NULL
  + mark FamilyMembership.removed_at
  + report grants_revoked / membership_removed
erase_account_data
  + aggregate grants_revoked into the totals it already returns
```

Both are **updates, not deletes**, and that is forced by the schema rather than chosen for
convenience: `location_observations.sharing_session_id` is `ON DELETE RESTRICT`, and the *subject's*
observation rows legitimately reference the grant. Deleting the grant would fail or destroy another
member's data; deleting the membership cascades into the same grant and fails identically.

Revocation ends access through `authz.authorize_view`, which applies `revoked_at IS NULL` in its
query and `session_is_active` per row. The `removed_at` tombstone keeps the erased member out of
`list_members`, `active_membership` and the share-target lookup — all three already filter it.

**Correction to the issue's reasoning, recorded rather than silently followed.**
`authz.session_covers_viewer` does *not* consult `revoked_at`, and that is by design: it is a scope
predicate, composed by `authorize_view` with `session_is_active`. It was never the load-bearing
check, so the tests assert on `authorize_view` and on `session_is_active`, not on
`session_covers_viewer`.

## 5. Evidence

Base `main` `18c729735fd428622ea70b76571aa38e518a9774` -> head `39e9cac9d8593c808dbe8b6efed245e327d73b75`
(`fsn/f2-member-erasure-grant-revocation-01`, draft PR #29, issue #28).

| Measurement | Result |
|---|---|
| `pytest tests/ -q` on unmodified `main` | **61 passed** |
| `pytest tests/ -q` with the repair | **65 passed** (+4) |
| Negative control: revert only `app/retention.py` | **3 failed, 62 passed** |
| `FSN CI` on `push` (`39e9cac`) | **completed / success** (backend, secret scan, Android) |

The three negative-control failures are exactly the defect assertions:

```text
FAILED tests/test_hardening.py::test_erase_member_data_revokes_grants_to_the_erased_member
FAILED tests/test_hardening.py::test_erase_member_data_removes_the_erased_membership_from_the_family
FAILED tests/test_hardening.py::test_erase_member_endpoint_succeeds_while_a_grant_to_the_member_exists
E  KeyError: 'grants_revoked'
E  AssertionError: assert <app.models.FamilyMembership object ...> is None
```

The fourth test passes on **both** trees. It is a **design guard** (it reddens if a future repair
deletes the grant instead of revoking it), not a defect detector, and is labelled as such so it is
not read as evidence of the original defect.

## 6. A second defect, measured, deliberately not folded in

`erase_account_data` raises `ForeignKeyViolation` — a 500 — on the same root cause when the erased
account holds a member-level grant whose subject has an observation:

```text
ACCOUNT ERASE RAISED: IntegrityError (psycopg2.errors.ForeignKeyViolation)
update or delete on table "sharing_sessions" violates foreign key constraint
"location_observations_sharing_session_id_fkey" on table "location_observations"
```

**Pre-existing, proven**: identical failure with `app/retention.py` reverted to `main`. It is
recorded as **issue #30** rather than repaired here, because every available fix changes the schema
or the retention semantics (null the grantee, make `obs.sharing_session_id` `ON DELETE SET NULL`, or
revoke-and-retain). That is `HUMAN_DECISION_REQUIRED`. Folding a migration into a one-clause repair
would have been scope expansion, and picking one of the three silently would have been a governance
decision made by an agent.

## 7. Fairness clock — a recorded distortion

The refresh push records progress in Arkadia, and a push moves that repository's
`last_progress_at`. After this pulse FSN is the most recent (its own push at 11:11:57Z) and Arkadia
reads oldest at 09:10:55Z — before this ledger push. So:

* the next fair selection is **Arkadia**, on the heads measured here;
* the ledger-refresh push itself will advance Arkadia, and must not be mistaken for engineering
  progress in Arkadia.

This is why the selection is stated with the per-repository heads it was derived from, not from the
refreshed file alone.

## 8. What remains unknown

* Android and physical-device acceptance (F3): untouched, still BLOCKED on hardware.
* `alembic check` under CI: no ORM model changed, so it is unaffected — asserted from the diff, and
  confirmed by CI success, not measured separately here.
* Whether the `removed_at` tombstone is the right long-term erasure semantic: it retains a
  `user_id`/`family_id` link. There is currently no add-member or rejoin route
  (`grep` over `app/routes.py` returns only list / location / erase), so the occupancy of
  `uq_membership_family_user` is unreachable today. It becomes a real question with a join route.
