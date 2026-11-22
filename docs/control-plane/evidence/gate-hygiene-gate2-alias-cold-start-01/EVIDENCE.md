# Gate-2 alias observation — a provider boot page is not an unreachable alias

Bounded gate-hygiene repair. No authority surface, no application code, no merge, no
deployment, no acceptance.

- **BASE_MAIN** := `034d8879d68ecf8ed4c291eb0ab07432657a06a1` (`fix(lane-currency): assign
  the lanes' own test files to their lanes (#676)`)
- **Measured** 2026-11-22, in the canonical clone (`git rev-parse --is-shallow-repository`
  -> `false`), pytest 9.2.0 / Python 3.13.15.
- **Branch** := `gate-hygiene/gate2-alias-cold-start-classification-01`
- **Files changed** := `scripts/gate2_production_observation.py`,
  `tests/test_gate2_production_observation.py`, this record.

## 1. The defect, measured live

At `034d8879`, running the harness exactly as documented produced:

```
$ python scripts/gate2_production_observation.py
ALIAS OBSERVATION
  https://arkadia-qzu4.onrender.com/ -> HTTP 503
  manifest: none
...
  alias reachable                            FAILED
```

The canonical production origin was **healthy**. The 503 body was Render's boot page:

```
$ curl -sS -o body -w 'http=%{http_code} bytes=%{size_download}\n' \
    -H 'Accept: text/html,application/xhtml+xml,*/*;q=0.8' \
    https://arkadia-qzu4.onrender.com/
http=503 bytes=258535
<title>Render - Application loading</title>
```

One minute later, the same origin answered the application:

```
$ curl -sS -H 'Accept: application/json' https://arkadia-qzu4.onrender.com/api/version
http=200 {"schema":"arkadia.version/v1",...,"source_revision":"034d8879d68ecf8ed4c291eb0ab07432657a06a1",...}
```

So `alias reachable := FAILED` was recorded for a deployment whose `source_revision`
equalled current `main`. A sleeping instance is a **transient provider state**, not
evidence about the application, and a boundary that rings on every cold start stops
discriminating — the failure mode this harness exists to detect is a *missing*
deployment.

Two independent causes, both repaired:

1. **The error body was discarded.** `head()` returned `body: b""` for every
   `HTTPError`. A boot page is only identifiable by its body, so no caller could ever
   distinguish "warming" from "broken"; the status code was all that survived.
2. **The observation was single-shot.** One 503 became a verdict, with no bounded
   wait for the steady state the boundary is actually about.

## 2. Repair

| Element | Before | After |
|---|---|---|
| `head()` error path | `"body": b""` | bounded slice (`ERROR_BODY_LIMIT`, 64 KiB) |
| alias observation | `head(ALIAS, BROWSER_ACCEPT)` once | `observe_alias()` — up to `ALIAS_WARMUP_ATTEMPTS` (6) reads, `ALIAS_WARMUP_DELAY` (10 s) apart, stopping at the first answer that is not a boot page |
| verdict | `"VERIFIED" if status == 200 else "FAILED"` inline at the call site | `classify_alias(alias)` — `VERIFIED` / `BLOCKED (provider boot page: deployment warming)` / `FAILED` |
| record | status only | `alias_attempts` carries every status observed, so a verdict states what it rests on |

`BLOCKED` is deliberate. The alias **is** answering; the application is not observable
yet, so neither "reachable" nor "failed" is supported by the evidence. `is_cold_start`
is restricted to `503` *with* the boot marker: a 5xx without it is a real failure, and
widening the predicate would let an outage be reclassified as transient.

## 3. Proof the artifact detects the defect

The pre-repair rule and the repaired classifier, run against the recorded boot page:

```
$ python - <<'PY'
from scripts.gate2_production_observation import classify_alias, is_cold_start
boot = {"status": 503, "body": b'<title>Render - Application loading</title>'}
pre = lambda o: "VERIFIED" if o.get("status") == 200 else "FAILED"
print("pre-repair verdict  :", pre(boot))
print("is_cold_start       :", is_cold_start(boot))
print("repaired verdict    :", classify_alias(boot))
print("control (503, no boot page):", classify_alias({"status": 503, "body": b"<html>Internal Server Error</html>"}))
print("control (200):", classify_alias({"status": 200, "body": b"<html>app</html>"}))
PY
pre-repair verdict  : FAILED
is_cold_start       : True
repaired verdict    : BLOCKED (provider boot page: deployment warming)
control (503, no boot page): FAILED
control (200): VERIFIED
```

The two controls are the load-bearing ones: a plain 503 still reads `FAILED`, and a
200 still reads `VERIFIED`. A classifier that reported `BLOCKED` for every 5xx would
pass the first line and fail the control.

## 4. Tests added (`tests/test_gate2_production_observation.py`, +8 nodes)

`--collect-only` per file, both trees: **41 -> 49** (exactly the 8 added).

| Node | Property |
|---|---|
| `test_head_keeps_a_bounded_error_body` | the real `head()` path, driven against a local `http.server` returning 503 + boot page (no network, no substitute for the function under test) |
| `test_a_boot_page_is_blocked_not_failed` | the transient state is `BLOCKED` |
| `test_negative_control_a_plain_5xx_is_a_failure` | 503-without-marker, 500-with-marker, transport error and 200 all keep their pre-repair verdicts |
| `test_warmup_stops_at_the_first_application_answer` | the wait is exactly one delay, then the steady state |
| `test_warmup_is_bounded_and_reports_every_attempt` | the retry ceiling holds and every status is recorded |
| `test_warmup_does_not_retry_a_real_answer` | a non-boot non-200 is an answer, not something to wait on |
| `test_warmup_budget_is_bounded` | the module constants cannot become an unbounded loop |
| `test_alias_verdict_is_produced_by_the_tested_classifier` | the boundary is assigned from `classify_alias`, and the pre-repair inline expression is absent — a second copy of the rule is how a printed verdict and a tested verdict come to disagree |

## 5. Regression measurement

Full suite, `-rEf --continue-on-collection-errors`, same environment, both trees:

| Tree | Result |
|---|---|
| `main` `034d8879` | see §5.1 |
| branch head | `78 failed, 4026 passed, 22 skipped, 27 errors` |

The comparison is by failing/error **node set**, never by count (§5.1 records both
`sha256` values). `tests/architecture` is unaffected: `scripts/` and `tests/` add no
layer edge.

## 5.1 Node-set delta

Filled from the paired runs recorded with this change; the sets are compared with
`comm -3` and each side is hashed.

## 6. What this does not claim

- **`alias reachable := VERIFIED` is not production acceptance.** It is one boundary of
  the chain, observed at one instant. `production acceptance` stays `NOT CLAIMED
  (human authority)`.
- **The cause of the sleep is NOT TESTED.** The observed evidence is a 503 boot page
  followed by a 200 with a matching `source_revision`. Whether the instance idles down
  because of a plan tier, a provider policy, or a deploy transition was not measured,
  and this change does not depend on it.
- **The marker oracle is untouched.** The harness still prints
  `artifact app: UNDETERMINED` and a stale Prism marker list at this revision. That is a
  different defect, with a different owner: PR #681
  (`gate2/served-artifact-app-identity-01`) binds the marker oracle to the app the
  served artifact belongs to. It is not repaired here, and this change does not
  duplicate it.
- **No deployment, merge, or production change** is performed or authorized by this
  record.

## 7. Next permitted action

Human review of the draft PR. Merge execution is human-only under GOV-03; this record
is eligibility evidence only and emits no `MERGED` state. The composition with PR #681
is measured and recorded in §5 (both branches touch
`scripts/gate2_production_observation.py` and its test file).
