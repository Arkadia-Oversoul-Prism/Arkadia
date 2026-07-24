# Arkadia Engineering Principles

> How we build software in Arkadia.

These principles sit beneath the technical governance. ADRs record decisions. Architecture fitness tests enforce laws. These principles explain why those laws exist and how we think when the tests cannot answer the question for us.

---

## 1. Preserve Deployability

Every commit should leave the repository runnable.

A broken build is a broken contract with every contributor who picks up the codebase next. If a change cannot be completed in one session, leave the system in a state that is explicitly partial — with a feature flag, a TODO that fails loudly, or a documented checkpoint — never in a state that silently fails at runtime.

---

## 2. Reduce Entropy

Every change should reduce coupling, duplication, or ambiguity.

Adding functionality while increasing coupling is not progress. A commit that adds a feature but introduces an undocumented assumption, an implicit dependency, or an opaque side effect has negative architectural value even if the tests pass. Ask before merging: is the system easier to understand than it was?

---

## 3. Stabilize Before Scaling

Solve boundaries before introducing infrastructure.

A well-bounded system with SQLite will outlast a poorly-bounded system with Kafka. Infrastructure does not fix architecture. When a layer is unclear, the instinct is often to add tooling. The right instinct is to clarify the boundary first, then ask whether infrastructure is still needed.

---

## 4. Protect the Kernel

The kernel orchestrates; it does not accumulate business logic.

The kernel is the most sensitive layer in Arkadia. Every import it takes from higher layers is a coupling that propagates to everything the kernel touches. If business logic accretes in the kernel, it becomes the system — and everything else becomes decoration. Keep it narrow. Keep it stable. Keep it pointing inward.

---

## 5. Canonicalize the Domain

Every concept has one authoritative definition.

If "job" means different things in `kernel/jobs.py`, `api/main.py`, and the frontend, those are three systems pretending to be one. Duplication of concepts is more dangerous than duplication of code because it is invisible to static analysis. When a domain concept appears, find its canonical home and point everything else at it.

---

## 6. Prefer Evolution Over Revolution

Small, verified migrations beat large rewrites.

A rewrite begins with confidence and ends with a new set of unknown unknowns. An incremental migration — one bounded context at a time, each step testable and reversible — preserves continuity while still delivering the destination. When the temptation to rewrite arises, ask: what is the smallest change that moves in the right direction?

---

## 7. Automate Governance

If a rule matters, encode it in tests or tooling.

A rule that lives only in a document depends on every reader remembering it, every contributor knowing where to look, and every reviewer having the discipline to enforce it. A rule encoded in a fitness test is enforced by CI. Move every architectural law toward automation. Documents articulate intent; tests enforce it.

---

## 8. Document Intent, Not Just Implementation

Future maintainers need to know why, not only how.

Code explains what happens. Comments can explain how. Only documentation explains why a decision was made, what alternatives were considered, and what constraint it was designed to address. An undocumented decision that seemed obvious at the time becomes a mystery six months later. When in doubt, write the ADR.

---

## 9. Measure Before Optimizing

Use evidence to drive architectural decisions.

Performance assumptions are almost always wrong. Complexity assumptions are almost always wrong. Before introducing infrastructure, a new abstraction, or a structural change justified by performance, measure the current behavior. The cost of an optimization that solves the wrong problem is paid twice: once to build it, once to remove it.

---

## 10. Leave the Repository Better Than You Found It

Every session should improve the platform, even if only slightly.

This is not about heroic refactors. It is about the discipline of the small: a test added for a case that was untested, a confusing name clarified, a comment written where the code was opaque, a layer violation removed. Over months and years, those small improvements compound into a codebase that remains understandable and adaptable. Over months and years of the opposite, they compound into one that does not.

---

*These principles are not a checklist. They are a shared way of thinking. When two principles appear to conflict, that tension is worth a conversation — it usually means an architectural decision needs to be made explicit.*

*Filed: ARK Y1 · D116 (2026-07-24)*  
*Authority: Flamekeeper*
