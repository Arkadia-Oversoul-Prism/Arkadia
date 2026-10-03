# GATE-10 — Console capture `safe_id` repair (evidence)

**Class:** defect repair, device-verified runtime path.
**Base main:** `357fbd83001924e909979fbaebdedbd991a2aadb` (2026-10-03).
**Branch:** `gate10/console-capture-safe-id-repair-01`.
**Authority:** none required to implement, test, branch, open PR. Merge is sovereign-only.

## 1. Defect (measured, not inferred)

`solspire/console_authority_router.py::sync_capture` (the `POST /solspire/authority/captures`
handler) referenced the name `safe_id` in four places while never defining it. The sanitizer
line that defines it was dropped while its uses were kept, so **every** call to the captures
endpoint raised at runtime:

```
NameError: name 'safe_id' is not defined
```

This is the endpoint the native Console client (`ConsoleRepository.kt`) calls to reconcile
each capture. The failure is runtime-only — `python -m py_compile` passes, because the
reference is a name lookup, not a syntax error. Reproduced by executing the handler directly
(`/tmp/prove_capture.py`, dev-mode auth) before the repair, and re-run after.

### Origin (git forensics)

```
$ git log -L 247,247:solspire/console_authority_router.py --oneline --no-patch | head
29add3cf4d  feat(console): native capture reconciliation endpoints   # defines safe_id
134b28ee0d  fix(console): canonical field reconciliation             # drops the definition, keeps 4 uses
```

`29add3cf4d` introduced
`safe_id = "".join(ch for ch in body.capture_id if ch.isalnum() or ch in "-_")[:80]`.
`134b28ee0d` removed that line without removing its four uses.

## 2. Repair

Restore the sanitizer, add an explicit empty-input guard, and hoist the duplicated
conditional artifact-ref expression into one local. Behavior restored:

- `capture_id` sanitised (alnum + `-`/`_`, truncated to 80) before use and before return.
- Empty sanitised id → `400` (was implicitly `200` on the pre-regression revision).
- Metadata-only capture (no bytes) records `device-local-capture:<uid>:<id>`; a capture with
  bytes records `console-capture:<uid>:<id>`. This preserves the existing security posture —
  the earlier revision collapsed both branches to the same server-server-ref string, which
  asserted server-side content for a device-local record.

Files changed:

- `solspire/console_authority_router.py` — repair only.
- `tests/test_console_authority_chain.py` — +2 regression tests.

## 3. Verification

| check | result |
|---|---|
| `python -m py_compile solspire/console_authority_router.py api/main.py` | PASS |
| `tests/test_console_authority_chain.py` | 5 passed (was 3 passed) |
| handler executed directly (`/tmp/prove_capture.py`) | RAISED NameError before; returns `ok:True, capture_id:"cap-001", artifact_ref:"device-local-capture:…"` after |
| `tests/architecture` | 11 passed |
| `tests/test_m02a_ci_gate_integrity.py` | 55 passed |
| full suite `pytest tests/ -q --continue-on-collection-errors` | 27F / 1365P / 20S / 1E — node set **28**, identical to base |

### Baseline / regression boundary

Base main measured `27F / 1363P / 20S / 1E`, failing-node set **28**. After the repair the
failing-node **set is unchanged at 28**; passed count rose from 1363 to 1365, exactly the two
added tests. No node-set delta — the contract's node-set method of attribution.

### Pre-existing failures explicitly NOT in scope

- `tests/test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification`
- `tests/test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk`
- `tests/test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record`
- `tests/test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records`

The third is a **guard false positive** (not a defect): it flags any route decorator whose
path merely *contains* the substring `review` — here `POST /solspire/projects/{id}/patches/preview`.
The first two encode an authority principle (no HTTP route may create evidence or expose
verification) that the mounted `console_authority_router` now contradicts. Whether a
device-verified Console path is a permitted exception is an **authority-model** question, so it
is deferred to the sovereign (§Authority below). None of these four is attributable to this
change: all four fail identically on base main.

## 4. Authority boundary

- No merge, no push to `main`, no force-push, no self-authorization.
- No change to identity, authority model, or governance surfaces.
- The four deferred boundary nodes touch **authority semantics** (May an HTTP route create
  evidence? May the mounted console surface expose verification?). Classifying or resolving
  them changes the authority model and is reserved to the human sovereign.

## 5. Next bounded task (proposed, not executed)

`tests/test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record`
is a self-contained test-side false positive: tighten its route detector to match the resource
verb (`/review`) rather than the substring `review`, and add a negative control. Do not restore
literal pins against JSON responses (per AGENTS.md test-side-literal-pin lesson). This is a
separate, non-consequential bounded PR.
