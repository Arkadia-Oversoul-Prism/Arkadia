# 02 — Decision Cache
> Frozen. Do not re-litigate. If a decision must change, file an ADR first.

---

## Persistence

**Why SQLite, not Redis or Postgres?**
Zero infrastructure. WAL mode is crash-safe. Fits single-node deployment horizon. Revisit: Phase 5 horizontal scaling.

**Why `data/runtime.db` separate from `knowledge/arkadia.db`?**
Runtime state (jobs, goals) and knowledge state have different backup, retention, and migration schedules. One corrupted DB must not take down the other.

**Why replace the in-memory queue?**
In-flight jobs are silently lost on process crash. JSON snapshot is best-effort. WAL is crash-safe. (ADR-014, Decision 1)

**Why keep JSON backup files after migration?**
Rollback path — a `git revert` of the migration commit must restore JSON behavior. Preserved read-only through B1.3.

---

## Architecture

**Why is kernel/ forbidden from importing api/?**
Stable layers cannot depend on unstable ones. kernel/ → api/ prevents isolated testing and creates circular import risk. (ADR-015)

**Why are providers leaf adapters?**
Provider implementations change constantly. kernel/ must swap providers without structural changes. Keys injected, not imported. (ADR-015, ADR-014 Decision 4)

**Why is api/main.py decomposition deferred?**
It is ~2506 lines and requires canonical domain types that don't exist until Phase 2. Budget: 2600 lines — do not grow it. (ADR-014)

**Why is the Plugin Registry (Workstream E) after runtime durability (Workstream B)?**
A durable runtime must exist before a plugin system can safely use it. B → E order is mandatory.

**Why is Observability (Workstream D) after E?**
Instruments an existing stable system. Instrumentation before stability is noise.

**Why is Layer Violation remediation (Workstream A) last?**
Workstream E removes the `ALLOWED_TYPES` frozenset, which is adjacent to several layer violations. Clean E before cleaning A.

---

## Tooling

**Why architecture fitness tests instead of code review?**
A rule in a document depends on every reader. A rule in a fitness test is enforced by CI. (Principle 7)

**Why REGISTERED_ARCHITECTURAL_DEBT, not ALLOWED_VIOLATIONS?**
"Allowed" implies permission. These are scheduled liabilities with exit criteria.

---

## Sequencing

**Why Phase 1 before Phase 2?**
Cannot canonicalize a domain whose runtime is undurable. (ROADMAP.md)

**Why no Event Bus, Redis, Kafka, microservices in Phase 1?**
Infrastructure does not fix architecture. Solve boundaries first, then scale. (Principle 3, ADR-014 explicit exclusion)
