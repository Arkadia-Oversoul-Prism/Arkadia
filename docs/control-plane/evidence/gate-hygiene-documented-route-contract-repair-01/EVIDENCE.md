# EVIDENCE — `gate-hygiene` / documented route contract repair (DR-01)

Branch `gate-hygiene/documented-route-contract-repair-01`. Docs + test only; no runtime
surface changed.

## 1. Defect

`DEPLOYMENT_GUIDE.md` advertised an endpoint table containing paths that `api.main:app`
— the app `entrypoint.sh` runs — does not serve. Every one of them answers `404` in
production, so the operator document contradicted the deployed contract.

Measured, not asserted: the table's rows were diffed against `app.openapi()["paths"]`.
`/health`, `/status`, `/oracle`, `/threads`, `/arkadia/corpus` and `/arkadia/refresh` were
documented and unserved. `/api/heartbeat` — the path `railway.json` probes — is served and
was absent from the table.

## 2. Change

- `DEPLOYMENT_GUIDE.md` — endpoint table replaced with the served surface derived from the
  live OpenAPI schema; `GET /api/heartbeat` recorded as the canonical liveness probe.
- `tests/test_documented_route_contract.py` (new) — pins the table to the served schema so
  the two cannot drift apart again.

## 3. Merge-order defect found and fixed (`4f8791e`)

`ce85110` placed `/health` in `RETIRED_LEGACY_ROUTES`, which asserted the path stays
**absent** from `api.main:app`. PR #154 (open, `MERGEABLE/CLEAN`) restores `GET /health`
as a projection of `/api/heartbeat`. That assertion would therefore have turned `main` red
the moment #154 landed — the guard would have failed on the PR that fixes the route.

`/health` is not a retired legacy path. The genuinely dead paths are the five that no open
PR adds. `/health` is a two-state path and now has its own test requiring the guide to
agree with whichever state holds.

## 4. Merge-order simulation — guard executed in place

The guard was copied into a detached worktree per state so `REPO_ROOT` resolved to a real
repository (a `/tmp` run resolves outside the repo and raises `FileNotFoundError` — a
harness artifact, not a guard defect; recorded so it is not re-mis-diagnosed).

| state | expectation | observed |
|---|---|---|
| **A** branch as-is (health absent, guide warns) | pass | **0 — pass** |
| **B** #154 merged, guide not updated | fail | **1 — fail (correct)** |
| **C** #154 merged, guide updated | pass | **0 — pass** |
| **D** health absent, guide advertises it | fail | **1 — fail (correct)** |

A and C are the reachable states and both pass. B and D are the two ways the guide and the
app can disagree and both fail. The guard no longer depends on merge order.

## 5. Regression fingerprint

| | failed | passed | skipped | errors |
|---|---|---|---|---|
| `main` @ `002b189` | 20 | 1039 | 13 | 2 |
| branch @ `4f8791e` | **20** | **1048** | **13** | **2** |

Failure set is identical, name for name (22 failure lines: 20 `F` + 2 `E`). The delta is
`+9 passed`, which is exactly the nine tests in the new file. No baseline debt was fixed
and no new failure introduced. Collection errors remain `tests/test_autonomy.py` and
`tests/test_render_codex.py` — pre-existing, documented.

`tests/architecture` **11/11**. `python -m py_compile api/main.py` clean; `api/main.py`
untouched at **2519 / 2600** lines. CP10 mutation boundary `--judge` exit **0** on both
commits.

## 6. Adjudication of PR #155 (AGENTS.md encoding queue) — independently reproduced

PR #155 adjudicates the five-PR `AGENTS.md` encoding-repair queue. Its verdict is
load-bearing for the sovereign's merge order, so it was re-derived here by an independent
method rather than accepted on reading.

**M1 — codepoint alphabet.** The corruption is total over the document's non-ASCII content,
so a correct repair must recover an alphabet contained in the established set. Enumerated
per candidate with `unicodedata`:

| candidate | bytes | distinct non-ASCII | outside established | Cyrillic | box-drawing | U+21D2 |
|---|---|---|---|---|---|---|
| `main` `002b189` | 27301 | 19 | 12 | 10 | 2 | no |
| **#150** | 29528 | **12** | **0** | **0** | **0** | no |
| #147 | 36650 | 23 | 14 | 10 | 2 | **yes** |
| #143 | 35811 | 28 | 26 | 0 | 2 | no |
| #152 | 27301 | 19 | 12 | 10 | 2 | no |

Only #150's recovered text stays inside the established twelve-codepoint alphabet.

**M2 — codec.** All 62 multi-character non-ASCII runs in `main` invert cleanly through
`cp866`: `s.encode("cp866").decode("utf-8")` succeeds and lands inside the established
alphabet for **62/62**, with **0** exceptions. The codec is confirmed, not assumed.

**M3 — structure.** `repair(main)` is a **prefix** of #150's file: the two agree for the
first 26894 characters, after which #150 appends an authored EOF section
(`## AGENTS.md encoding corruption — the codec is cp866…`). This reproduces #155's
"byte-prefix + authored EOF section" claim exactly.

**M4 — the guard, executed in place** across five worktrees (its own tree plus the guard
file copied into each candidate):

```
origin/main  -> 2 passed
pr150        -> 2 passed
pr152        -> 2 passed
pr147        -> 1 failed, 1 passed
pr143        -> 1 failed, 1 passed
```

This reproduces #155's table exactly: the guard passes on `main`, passes on the correct
repair, and rejects both wrong candidates — green before *and* after #150 merges. Its
merge-order independence claim holds.

**Verdict: #155's disposition is corroborated by an independent method.** #150 is the
correct repair; #147 and #143 are wrong; #152's guard is merge-safe in any order.

### Two correctable errors in #155's prose (disposition unaffected)

Recorded so the merge order does not rest on false reasoning:

1. **#147 does not "restore `main`'s corrupted region verbatim."** #147's `AGENTS.md` is
   *not* byte-identical to `main`'s — it is 9349 bytes larger with 147 non-ASCII runs
   against `main`'s 110. It does carry `main`'s corrupted runs (all present), and it does
   *not* repair them, so the conclusion "not a repair / CONTRADICTED" stands. The stated
   mechanism is wrong; the verdict is right.
2. **#143 does not introduce an "invented `U+21D2`."** The single `U+21D2` is in **#147**,
   not #143. #143 is the double-encoded file whose alphabet is a different, larger set
   (Latin-1/Windows-1252/Latin Extended-A look-alikes). #143 still fails M1 by 26
   codepoints, so its rejection stands.

Neither correction moves the merge order: #150 first, #147 closed as CONTRADICTED, #152
after, #143 not merged, #151 at sovereign preference.

## 7. Boundary

Evidence-only + test. No merge, no push to `main`, no force-push, no production-parity
claim, no authorization. Reads the repository and its git objects; no deployment was
inspected. Human merge remains the only path to canonical.

---
*This evidence artifact was produced by an AI agent (OpenHands) on behalf of the human sovereign.*
