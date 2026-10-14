# Workstream 4 -- Arkana thread history · project-turn visibility evidence

**Branch:** `feat/prism-w4-arkana-project-turn-visibility`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §7.1 (Workstream 4: "Arkana thread
history against the verified `/api/commune/threads` handler, preserving truthful state")
**Instruction:** `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`
**Starting `main`:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. The measured defect

`GET /api/commune/threads/{thread_uuid}/messages` answered `{"messages": []}` for a thread whose
Knowledge OS database held recorded conversation turns. The empty state was therefore
**indistinguishable from a failed or lost read** — the exact distinction the thread-history slice
was built to preserve (`docs/control-plane/evidence/prism-w4-arkana-thread-history-01/EVIDENCE.md`
§1: "an empty collection is a `200`. The UI therefore cannot infer 'no data' from a failure").

### Root cause: two producers, one marker vocabulary

Two canonical producers write `note_type='conversation'` notes into a Knowledge OS thread, each in
its **own** content shape:

| Producer | Write shape | Turns per note |
|---|---|---|
| `knowledge/pipeline.py::ingest_conversation` (Oracle spine) | `## Prompt\n\n{p}\n\n## Response\n\n{r}` | **2** |
| `solspire/conversation_bridge.py::append_conversation_turn` (project conversations) | `Project: …\nConversation: …\nRole: {role}\n\n{content}` | **1** |

The handler understood **only** the first. Its parser required the literal `## Prompt\n\n` and
`continue`d past every note that lacked it, so the project producer's notes were read out of the
database and then silently discarded. Measured pre-repair (guard run against the unmodified
handler):

```
FAILED tests/test_arkana_thread_history_contract.py::test_project_conversation_turns_are_visible
FAILED tests/test_arkana_thread_history_contract.py::test_both_producers_compose_in_one_thread
FAILED tests/test_arkana_thread_history_contract.py::test_unknown_role_heading_is_a_user_turn_not_a_fabricated_answer
FAILED tests/test_arkana_thread_history_contract.py::test_negative_control_the_turn_reader_flags_the_unparsed_shape
4 failed, 14 passed
```

### Why this is not a "the producer should change" repair

`solspire/conversation_bridge.py:74-83` documents the project note shape as deliberate — the
conversation UUID is embedded in the note body *because* Knowledge OS duplicate detection is
content-scoped, and the bridge must not "change the canonical pipeline or introduce a second dedupe
authority". Both shapes are canonical; the reader is the surface that must understand both.
`api/commune_threads.py` is also **unclaimed by every open PR** (34 open PRs, file-overlap scan
below), so this is a genuinely unowned gap rather than duplicated work.

---

## 2. The bounded repair

`api/commune_threads.py` — one module, one helper, read-only:

* `_turn_messages(content) -> list[(role, content)]` reads a note in **either** canonical shape and
  returns the turns it records.
  * Oracle shape (`## Prompt` + `## Response`) -> `[("user", q), ("arkana", a)]`.
  * Project shape (`Role: <role>` heading) -> one turn; `arkana`/`assistant`/`model` are answers,
    any other role is a user turn.
  * A note in **neither** shape is skipped. An unknown body is never guessed into a message.
  * A half-written Oracle pair (prompt, no response) still yields **nothing** — the pre-existing
    no-fabrication guarantee is preserved.
* The `/messages` route now calls the helper per row and appends every turn, keeping
  `SELECT … ORDER BY created_at ASC, id ASC` and the `thread_id`/`note_type`/`user_id` filter
  unchanged. **No route, method, status code, envelope, message key, or role vocabulary changed** —
  the verified contract in §1 of the prior evidence holds byte-for-byte, so the merged frontend
  slice (`arkanaThreadsContract.ts`, `ArkanaThreadHistory.tsx`) needs no change.

`api/main.py` is untouched (2505 lines, budget 2600).

---

## 3. Evidence

| Check | Command | Result |
|---|---|---|
| Targeted oracle + frontend + cal05 | `python -m pytest tests/test_arkana_thread_history_contract.py tests/test_prism_w4_arkana_thread_history.py tests/test_cal05_first_class_threads.py -q -rEf` | **39 passed** (was 35 passed; +4 new guards) |
| Negative control (fix reverted) | same, handler restored from `git checkout --` | **4 failed, 14 passed** — every new guard reddens; the pre-repair defect is what they detect |
| Boot syntax | `python -m py_compile api/main.py api/commune_threads.py` | OK |
| Architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| Mutation boundary | `printf 'api/commune_threads.py\ntests/test_arkana_thread_history_contract.py\n' \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| Open-PR overlap | file scan of all 34 open PRs for `commune_threads` / `arkana_thread_history` / `cal05` | **0 matches** — unowned |

The new guards are written against the **real handler** (composed router + real identity seam), not
a mock, and one of them (`test_negative_control_the_turn_reader_flags_the_unparsed_shape`) pins the
reader in **both** directions — a turn for each shape it claims to understand and nothing for each
shape it must reject — so it cannot pass against a reader that returns a turn for any note.

No full-suite run was taken this pulse (budget rule: at most one, and this slice's proof is the
targeted oracle + the negative control). No baseline node set is claimed as changed.

---

## 4. Remaining uncertainty / not claimed

* **Production parity is NOT CLAIMED.** The repair is a repository-source change; it has not been
  observed on the canonical runtime (`https://arkadia-qzu4.onrender.com`, ADR-016) and no deployment
  is authorized by this workstream.
* The role vocabulary accepted for the project producer (`arkana`/`assistant`/`model`) is derived
  from the producers' own defaults (`solspire/console_router.py::AppendMessageRequest.role` defaults
  to `user`; the archive UI posts `role: 'user'`). An answer turn written under a *new* role name
  would read as a user turn — recorded, not guessed at, because the alternative (treating every
  unknown role as `arkana`) fabricates answers.
* `create_arkana_thread` still returns `500` on a body-less `POST` (`tests/test_arkana_thread_history_contract.py::test_recorded_defect_bodyless_create_is_a_server_error`).
  It is adjacent, mutation-side, and deliberately **not** repaired here — the pin is preserved
  unchanged and should be re-pointed to `400` by whoever owns that repair.

## 5. Authority

Merge, deployment, and acceptance remain the human sovereign's. This PR is draft.

---

## 6. Pulse record — next-action block

**Pulse:** PRISM-W4 · Lane 4 (Arkana / Weaver / Engineering Lab) · pass 1, 2026-10-14.
**Starting `main`:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`.
**Branch head:** `226aef2022f047cd4fe1cd3a88683478e451e2d2` (PR #531, draft).
**Live state:** `OPEN` / `isDraft: true` / `mergeable: MERGEABLE` / `mergeStateStatus: CLEAN`.
**CI:** 11/11 check-runs `completed/success` on the head (secret scan, boot-syntax, console-contract,
test, provider-forensics, security-metadata, production-read-only-probe,
native-arkadia-golden-workflow, bundle-beta-evidence, beta-beta-01-english, beta-beta-02-hausa).

| | |
|---|---|
| **Current state** | Bounded backend repair complete, tested, pushed; PR open and draft. |
| **Evidence** | This document; negative control 4F/14P with the fix reverted; targeted suite 39 passed; architecture 11 passed; CP10 judge PASS. |
| **Blockers** | None for this slice. Production observation of the repair is **BLOCKED** on authorization (no deploy permitted to this workstream). |
| **Authorized action (next pulse)** | Advance the oldest unadvanced lane. If Lane 4 is next again, the bounded candidate is the preserved `test_recorded_defect_bodyless_create_is_a_server_error` pin — re-point it to `400` and repair `create_arkana_thread` to tolerate a missing/empty body. That is mutation-side and must be its own bounded PR. |
| **Forbidden** | Merge, deploy, force-push, mark ready, weaken the preserved pin, or edit any lane-1 shared file (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`, `types.ts`, `SurfaceLenses.tsx`). |
| **Completion condition** | Sovereign reviews and merges; a post-merge deployment is observed serving the repaired handler; only then may production parity be claimed. |

**Note on `AGENTS.md`:** two open PRs (#504, #482) currently touch `AGENTS.md`, so the lesson from
this pulse is persisted here rather than appended to that contested shared file. The transferable
lesson: *one thread, two canonical note shapes — when a reader understands only one producer's
shape, the other producer's rows are silently dropped and the API reports an empty success, which is
indistinguishable from a lost read. Pin the reader against every producer's shape, in both
directions, or the empty state lies.*
