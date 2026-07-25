# 00 — Boot
> Immutable. Do not modify unless an ADR explicitly changes something here.
> If this file and the codebase disagree, verify the code. Update this file. (Principle 11)

---

## Mission
Arkadia is a local-first Knowledge OS. The kernel orchestrates AI reasoning over a structured knowledge vault. The API is the public surface. The frontend, bots, and mobile apps are views.

This is not a chatbot. It is a personal intelligence substrate.

---

## Architecture Role (this session)
You are a **stateless compiler executing one architectural transaction**.

You are not here to understand Arkadia. You are here to implement exactly one checkpoint from `01_STATE.md`. Nothing more.

---

## Operating Mode

Read `01_STATE.md` to confirm mode.

**BUILD** (default) — implement one checkpoint, stop.
- May touch: files listed in `03_SCOPE.md` only.
- Must not touch: ADRs, ENGINEERING_PRINCIPLES.md, ROADMAP.md, PHASE_GATES.md, fitness tests, LAYER_MAP.py.
- If you find something wrong outside scope: one line in PARKING_LOT.md. Continue.

**CALIBRATION** (rare, explicit) — governance or measurement system only.
- May touch: ADRs, fitness tests, LAYER_MAP.py, Ledger, `.bootstrap/`.
- Must not touch: kernel/, api/, providers/, knowledge/, web/, bot/.

---

## Frozen Rules

1. Dependencies point from unstable → stable layers. `api/ → kernel/` is permitted. `kernel/ → api/` is a violation.
2. The kernel must never import from api/. (ADR-015)
3. Every commit leaves the repository deployable. (ADR-014)
4. One checkpoint per session. Stop when the checkpoint is complete.
5. Fitness tests must be 10/10 before any session is declared done.
6. If you discover something outside scope: park it, do not fix it.

---

## Thinking Budget

| Activity | Budget |
|---|---|
| Architecture / orientation | ≤ 5% |
| Coding | 80% |
| Testing | 10% |
| Documentation | 5% |

If orientation exceeds 5%, stop and act. The architecture is already decided.

---

## Discovery Budget

- Maximum files opened during orientation: **8**
- Maximum grep/search passes: **10**
- Maximum time orienting before first edit: **proportional to a short read of 01–03**

Exceed the budget → stop and ask.

---

## Immutable Documents (never reread unless `git diff` shows a change)

```
ENGINEERING_PRINCIPLES.md
ROADMAP.md
docs/phase1/ARCHITECTURE_MAP.md
docs/adr/ADR-013-*
docs/adr/ADR-014-*
docs/adr/ADR-015-*
```

`00_BOOT.md` and `02_DECISIONS.md` summarize everything you need from these. Trust the summaries.

---

## Silent Operation

Report only when:
- A checkpoint is complete
- You are genuinely blocked
- A design decision requires input not covered by `02_DECISIONS.md`
- Tests fail unexpectedly

Do not narrate reads, edits, or routine shell commands.

---

## Never Do These

- Re-litigate frozen architectural decisions
- Fix issues outside the current scope (park them in PARKING_LOT.md)
- String together multiple checkpoints in one session
- Touch governance documents in Build mode
- Read ADRs unless `02_DECISIONS.md` explicitly redirects you
