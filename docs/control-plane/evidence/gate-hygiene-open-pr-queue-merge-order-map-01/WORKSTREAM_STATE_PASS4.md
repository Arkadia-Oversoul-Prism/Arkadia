# WORKSTREAM STATE — gate-hygiene open-PR queue map (Pass 4)

Workstream: `gate-hygiene/open-pr-queue-merge-order-map-01`
Active PR: **#219** (`gate-hygiene/open-pr-queue-merge-order-map-02`)
Base main: `162f574b05dd839540d803aadda7608342618a84`
Pass 4 head: this branch. Authority: no merge / no push to `main` / no force-push.

## Current state

- Live queue: **5 open PRs, #215–#219**, all on `main 162f574`, all MERGEABLE / UNSTABLE.
  Required gate (`Full-history secret scan`) **success** on all five.
- Composability **re-proven from `main`** in this clone: `#215→#216→#217→#218→#219` is
  git-clean at every step; composed HEAD `75a01d0e83377ea642fe8a5f83c9faacaddb9abd`;
  order-insensitive (alternate tree `196b713f…`, empty diff).
- Node-set delta (this clone): baseline 105 → composed 103; **fixed 2, newly-failing 0**.
  Same delta with `requests` installed (101 → 99). CP10 judge PASS on composed + every PR.
- `api/main.py` untouched; budget 2582 / 2600; `py_compile` OK.

## Correction recorded this pass

Pass 3 §2's `refs-present` column does **not** reproduce in this clone: 5 PR refs (not 216),
`7d79f38` unresolvable, baseline **60F/836P/45E** (not 20F/1308P/1E). Its absolute counts
are marked unreproduced; only the composed **delta** (baseline minus two adjudication nodes,
plus zero) is retained.

## Next bounded task (pinned)

**Adjudication assertion defects** in `tests/test_agents_md_encoding_adjudication.py` — make
`test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` skip when `GATE2_PARENT_REV`
is absent (currently `AttributeError`), and pin
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` to a fixed revision
instead of the moving `origin/main`. Test-only; **separate PR** — do not fold into this one.

## Resume condition

Next heartbeat reconstructs from `main`, the open PRs, and this file. Do not merge; a human
merges. Do not fold the pinned task into the queue-map PR.
