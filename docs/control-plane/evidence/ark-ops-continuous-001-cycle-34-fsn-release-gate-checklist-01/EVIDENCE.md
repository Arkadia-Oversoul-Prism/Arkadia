# ARK-OPS-CONTINUOUS-001 — cycle 34: FSN gets a release gate it can be decided from

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471` (Arkadia)
**Branch:** `gate-hygiene/portfolio-state-ledger-01`
**Pulse:** 2026-11-28T04:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to any
canonical branch, no deployment, no acceptance, no draft conversion. The ledger's own PR #744
was extended rather than duplicated.

This is a reconciliation/implementation record, so it takes the bare `…-cycle-NN` path. The work
itself landed in the selected repository (`family-safety-network`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json                                          (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json                                         (authored judgement)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-34-fsn-release-gate-checklist-01/EVIDENCE.md   (new)
```

The cycle index (`…/ark-ops-continuous-001/LEDGER.md`) is **not** updated here, for the reason
cycle 32 recorded: it lives on `main` (merged by #705 at `8f746f9e`) and this branch is based on
`cb284195`, behind it. A second copy on this branch would recreate the split-ledger problem the
index exists to fix.

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-28T04:07Z, not from memory. All three repositories were readable with
the session token; none was omitted.

| Repository | Default branch | Head | Open PRs | Open issues | `last_progress_at` |
|---|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 4 | 1 | 2026-11-28T03:16:48Z |
| `family-safety-network` | `main` | `18c729735fd4` | 10 | 5 | 2026-11-28T02:13:12Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 10 | 2026-11-28T03:18:07Z |

FSN was oldest, so the fairness rule selected it; the tie-break order was never reached. The
selection was re-derived from live state rather than inherited from the previous pulse.

## 2. The gap

The directive names a release checklist under F4. At `18c72973` the repository had none:
`grep -rlin 'release checklist' . --exclude-dir=.git` returned no match.

Worse than absent, the threat model's own rows are stale against the source they describe:

| Row | Document says | Source at `18c72973` shows |
|---|---|---|
| F3 (line 92) | "No TLS enforcement in application code" | `main.py:26-38` rejects plaintext in production with `400 https_required`; `config.py:150-153` refuses to boot in production unless `FSN_REQUIRE_HTTPS` is true |
| F4 (line 93), §5.5 (line 81) | "no retention or deletion policy is implemented", "no right-to-erasure path" | `retention.py:42,61,89` implements purge, member erasure and account erasure; exposed at `POST /v1/maintenance/purge`, `DELETE /v1/families/{id}/members/{id}/data`, `DELETE /v1/account`; indexed by `0002_retention_indexes` |

A release decision cannot be taken from a document that under-reports the controls that exist,
because a reader cannot separate a real gap from a stale claim.

## 3. The change

`family-safety-network`, branch `fsn/f4-release-gate-checklist-01`, PR **#25**, issue **#24**.

| File | Δ |
|---|---|
| `documentation/testing/RELEASE-CHECKLIST.md` | +76 |
| `backend/tests/test_release_checklist.py` | +169 |
| `documentation/README.md` | +5 |

Every checklist row names the file and symbol that carries the control, or records that a search
found none. Declared status vocabulary: `MET`, `PARTIAL`, `NOT_MET`, `BLOCKED`,
`HUMAN_DECISION_REQUIRED`. Measured outcome: F1 `HUMAN_DECISION_REQUIRED`, F2 `PARTIAL`,
F3 `MET` (documented row stale), F4 `PARTIAL` (documented row stale), F5/F7/F8 `NOT_MET`,
F6 `PARTIAL`. Verdict: **NOT APPROVED**.

The guard parses the findings table out of THREAT-MODEL §6 and the checklist's own rows, and fails
when a finding has no row, a row invents a finding, an id repeats, a status leaves the vocabulary,
or the decision does not say `NOT APPROVED` while a gate is open. Six tests, of which four are
negative controls, one is a positive control (every gate `MET` must produce no finding), and one
asserts the parser itself is non-empty — because a parser that returns nothing would make the set
comparison pass vacuously.

`THREAT-MODEL.md` was deliberately **not** edited. Three open drafts edit it (#15, #16, #21) and
#16 and #21 carry F3/F4 and §5.5 as diff context, so a further concurrent edit conflicts. Correcting those rows is sequenced
behind them and recorded in issue #24.

## 4. Verification

| Check | Result |
|---|---|
| `pytest tests/test_release_checklist.py` (local) | **8 passed** |
| Live negative control: F7 row deleted from the real file | **2 failed, 6 passed**, `F7 is declared by the threat model but absent` |
| Restore and re-run | **8 passed**; sha256 `f49f84021a9be59bdf27ef05d9b58a365351fd0641ae23b97755982c6170a75e` identical before and after |
| `FSN CI` run `46106471130` (pull_request) | secret scan **success**; backend **success**; Android build **success** |
| Backend suite on the branch | **69 passed, 1 warning** |
| Backend suite on `main` (run `45782631330`) | **61 passed, 1 warning** |
| PR #25 head `c5ef595` | `MERGEABLE` / `CLEAN`, draft, 3 files, +250/−0 |

The `+8` is attributable, not inferred: it is exactly the eight nodes of the new test file, and
the run log names each of them passing. Line counts are measured with `git diff --numstat`, not
estimated from the PR summary.

**Not run, and why:** the PostgreSQL + PostGIS suite locally — this sandbox has no PostgreSQL
binaries and no running Docker daemon. CI is the authority for it and ran it green. Physical-device
acceptance was not attempted: no hardware, recorded as `BLOCKED` rather than claimed.

## 5. The fairness clock moved, and that is the rule working

Pushing to FSN set its `last_progress_at` to `2026-11-28T04:12:32Z`, so the re-derived selection is
now `sonata` at `2026-11-28T03:16:48Z`. The repository that was just worked advances; the next
pulse is pointed at the one that has waited longest. `scripts/portfolio_state.py --check` passes
with that selection, and the recorded selection was re-derived rather than typed.

## 6. Next legal task

Await human review of the eleven FSN drafts. Then correct THREAT-MODEL F3 (line 92) once #16 lands,
and F4 (line 93) with §5.5 (line 81) once #21 lands. Physical-device acceptance stays `BLOCKED` on
hardware; the F1 identity provider and the guardian-consent semantics stay human decisions. The
next pulse's selected repository is Sonata.
