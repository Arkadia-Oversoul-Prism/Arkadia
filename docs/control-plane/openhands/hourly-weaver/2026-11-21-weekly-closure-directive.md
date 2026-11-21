# OpenHands Hourly Weaver — Weekly Closure Directive
**Issued:** 2026-11-21  
**Owner / authority:** Human Sovereign  
**Execution model:** OpenHands hourly Weaver pulse; each pulse starts in a fresh sandbox and must reconstruct repository state.  
**Purpose:** Close verified work and reduce open-loop debt—not create parallel projects or claim unverified completion.

> **Naming correction:** “Hourly River” was an autocorrect error. The canonical name is **Hourly Weaver**. This corrected file supersedes the mistakenly named `hourly-river` draft. Do not use or link the old path.

## Bootstrap contract — every fresh sandbox
1. Clone `Arkadia-Oversoul-Prism/Arkadia` fresh; fetch and check out current `main`. Record exact `BASE_MAIN`, working tree state, and the task branch/head.
2. Read `AGENTS.md`, `.bootstrap/03_SCOPE.md`, `docs/control-plane/ENGINEERING-RUNNER.md`, current lane/control-plane instructions, and this directive.
3. Verify every referenced branch, PR, workflow, deadline, and evidence item against live GitHub/source artifacts. The dated facts below are **handoff leads, not durable truth**. Refresh them before acting; if a reference is missing or stale, mark it unresolved rather than guessing.
4. Select **one bounded repository task per pulse**, preferably updating an existing owned branch/PR. No duplicate PRs, parallel self-dispatch, or unrelated scope.
5. Change only lane-owned files. Run the applicable tests, preserve actual output/evidence, update durable state/ledger, and report. A truthful blocked/no-op pulse is acceptable; activity theater is not.

## Closure priorities
### P0 — THE PLATEAU CODE / competition evidence (repository-only)
- Preserve dated evidence for the original video, publication URL(s), Instagram suspension and appeal status as supplied by the human, other publication evidence, and official competition rules/deadline.
- Prepare an organizer-contact evidence packet and **draft only**. No contacting Ikechukwu/organizers, sending WhatsApp/email/DMs, account login, appeal submission, competition submission, or public post.
- Previously supplied handoff: appeal reportedly submitted Nov 19; competition deadline reportedly Nov 25, 2026. These dates and eligibility/alternate-entry options are **not independently verified in this repository directive**. Check official/source evidence and record provenance before relying on them.
- Do not edit, re-export, or overwrite the source video. Do not claim the entry is accepted or an alternate route approved without written evidence.

### P1 — Sonata: automatic capability detection and green CI
- Reconcile the live Sonata capability-contract PR/branch and CI. Earlier handoff named commit `e4045bb`, branch `feature/device-capability-contract-001`, and run `44824465496`; treat these as search keys only, not confirmed current status.
- Inspect current workflow/run and test source. Fix the smallest in-scope issue, make build/tests green, and update the existing PR with evidence.
- Product contract: **automatic device capability detection; Sonata adapts to the user's device; users must not be asked to supply phone specifications.** The household Samsung A23 and OPPO are first physical-validation devices. Never claim physical testing from sandbox/CI evidence.
- Do not choose/lock a production runtime until the capability contract and automated tests are verified. Record runtime decision as pending if the gate is not met.

### P1 — Chief: exact-head acceptance and governance evidence
- Reconcile Chief implementation and acceptance evidence against live `main`, CI, PRs, and source. The handoff referenced PR #669 and commit `b842892b`; the commit was found in repository history, but its presence alone does not prove acceptance or current gate status.
- Refresh any candidate/evidence on an exact current base/head using a dedicated authorized branch. Resolve only gaps within the permitted owned scope.
- Keep distinct: architecture acceptance; implementation acceptance; deployment authorization; credential issuance; workspace binding; scheduling activation; commissioning. None implies another.
- Historical reports of missing workflows, inactive runtime, 401 responses, `NOT_BOUND`, or open policy decisions are leads only. Recheck against current evidence; do not copy forward as current facts.
- No runtime activation, credentials, workspace binding, scheduling, deployment, merge/auto-merge, or commissioning.

### P2 — Arkadia One REC-002: source recovery and delivery gate
- Follow `ARK-ONE-REC-002`. Handoff evidence said prerequisite A (original source materials) was missing and the gate was FAIL/STOP; verify the actual canonical record before proceeding.
- Search only authorized locations for original provenance-preserving materials. Record exact path, source, and hash.
- Never reconstruct missing originals from chat summaries or label reconstructions as originals.
- Do not push or issue a delivery report unless the documented prerequisite and human-authorized scope are satisfied. Keep local preparation distinct from remote delivery.

### P2 — Career/opportunity evidence
- Maintain a small evidence/status record for the IDU/Serenity CV follow-up and the recent LinkedIn message only when the source artifacts are present or supplied by the human.
- Do not infer a response, offer, or commitment. No external messages or applications.

## Non-negotiable governance
- Human authority is final. The hourly schedule is a wake-up/pulse mechanism, not independent authority. **Do not assume this repository file is already wired into the hosted automation prompt/bootstrap; verify that linkage separately.**
- No direct push to `main`, force-push, protection bypass, merge, auto-merge, deploy, secret/credential mutation, production/runtime activation, or commissioning.
- Use dedicated task branches and draft PRs; preserve lane ownership and one-open-PR-per-lane policy.
- No external account action, personal-data harvesting, appeal/submission, organizer contact, WhatsApp/email/DM sending, or public communication. Prepare artifacts for human review only.
- No fabricated CI, device, publication, approval, delivery, or acceptance evidence. **Prepared ≠ sent; implemented ≠ tested; tested ≠ accepted; accepted ≠ authorized; local ≠ remotely delivered.**
- Do not repair adjacent failures or switch lanes just to keep a pulse busy. Record blocker, evidence, owner, and smallest human decision required.

## Durable pulse record
For every pulse, record:
- exact `BASE_MAIN`, branch and head SHA;
- selected lane and single bounded objective;
- changed paths and lane-ownership basis;
- commands/tests and actual result (including failures);
- source/evidence links and confidence/status classification;
- PR URL/status (draft/open/merged—verified live);
- blocker, next legal action, and required human decision;
- state/ledger/glance updated.

## Canonical source links — verify each run
- [Repository agent instructions](../../../../AGENTS.md)
- [Bootstrap scope](../../../../.bootstrap/03_SCOPE.md)
- [Engineering Runner contract](../../ENGINEERING-RUNNER.md)
- [Arkadia One mission contract](../../../architecture/ARKADIA-ONE-MISSION-CONTRACT-01.md)
- [L1 runtime implementation record](../../../architecture/GATE-L1_AGENT_RUNTIME_IMPLEMENTATION.md)
- [GOV-03 human-only merge execution evidence](../../evidence/gov-03-human-only-merge-execution/EVIDENCE.md)
- [Worker contract and merge boundary](../../WORKER_CONTRACT.md)
- [Sonata Android project README](../../../../sonata-android/README.md)
- [Sonata capability-contract branch](https://github.com/Arkadia-Oversoul-Prism/Arkadia/tree/feature/device-capability-contract-001) — verify it still exists/current
- [Sonata CI run handoff reference](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44824465496) — verify status and head
- [Search repository for REC-002](https://github.com/Arkadia-Oversoul-Prism/Arkadia/search?q=ARK-ONE-REC-002&type=code)
- [Original Plateau Code Reel reference](https://www.instagram.com/reel/Df7Cv0yqlJS/) — platform availability may be affected by account suspension

**Human-facing boundary:** This directive authorizes bounded repository engineering and evidence preparation only. It does not authorize external contact, account action, merge, deployment, or production activation.
