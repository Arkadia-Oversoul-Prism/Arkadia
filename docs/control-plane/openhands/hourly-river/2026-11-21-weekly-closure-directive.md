# OpenHands Hourly River — Weekly Closure Directive
**Issued:** 2026-11-21  
**Owner / authority:** Human Sovereign (Prestige)  
**Execution model:** OpenHands hourly fresh-sandbox pulse; repository state must be reconstructed each run.  
**Purpose:** Close verified work and reduce open-loop debt—not create parallel projects or claim unverified completion.

## Required hourly bootstrap
At the beginning of every fresh sandbox:
1. Clone `Arkadia-Oversoul-Prism/Arkadia` fresh and check out current `main`. Record exact BASE_MAIN.
2. Read `AGENTS.md`, `.bootstrap/03_SCOPE.md`, `docs/control-plane/ENGINEERING-RUNNER.md`, the current reconciliation/control-plane documents, and applicable lane-owned instructions.
3. Read this directive and linked workstream records below. Reconcile every status against live GitHub, CI, and source artifacts. The statuses in this document are a 2026-11-21 handoff snapshot, not permanent truth.
4. Select **one bounded repository task per pulse**. Prefer an existing owned branch/PR and repair/update it rather than opening duplicates. Do not concurrently dispatch or self-dispatch.
5. Work only in the assigned lane's owned paths. Produce tests, evidence, durable state/ledger updates, and a concise pulse report. If blocked, record the precise blocker and the smallest human decision needed; do not manufacture progress.

## Priority order for the current closure cycle
### P0 — Competition / Plateau Code evidence (repository-only)
- Preserve a dated evidence record for the published video, original Reel URL, platform suspension/appeal status as supplied by the human, existing Facebook/LinkedIn publication evidence, and official competition deadline/requirements.
- Create a concise organizer-contact evidence packet and a **draft only** message for human review. OpenHands must not contact Ikechukwu, send WhatsApp/email/DMs, log into Instagram/Meta, submit appeals, or make public posts.
- Keep account recovery and competition-entry contingency separate. The Instagram appeal was reportedly submitted Nov 19; the competition deadline was reportedly Nov 25. Verify dates and source links before relying on them. Record that organizer recognition/alternate submission is pending until a human obtains written confirmation.
- Do not alter, re-export, or overwrite the original video. Do not claim the entry is accepted unless official evidence proves it.

### P1 — Sonata adaptive-capability contract and CI
- Reconcile PR/branch for commit `e4045bb` (`feature/device-capability-contract-001`) and workflow run `44824465496` from live GitHub; these were reported as six contract tests and queued CI.
- Inspect the actual current workflow. Make the build and tests green with the smallest focused fix; add durable test/evidence and update the existing PR.
- Contract: automatic capability detection; app adapts to the device; users are not asked to provide phone specifications. Initial physical validation targets are the two household Android phones (Samsung A23 and OPPO), but sandbox automation must not claim on-device tests without device evidence.
- Do not select or lock a production runtime before the capability contract and tests are verified. Do not invent device-specific capabilities or mark physical validation complete.

### P1 — Chief acceptance dossier
- Reconcile Chief merge `b842892b`, PR #669 and all associated checks/workflows against live main.
- Refresh the candidate against current main where permitted on a dedicated branch; resolve evidence/test/workflow gaps in owned scope and prepare an exact-head acceptance dossier.
- Distinguish architecture acceptance, implementation acceptance, deployment authorization, credential issuance, workspace binding, scheduling, and commissioning. They are separate gates.
- The reported merge baseline had 15/15 runs; a later audit reported 30/45 expected workflows absent, runtime inactive, protected routes 401, workspace `NOT_BOUND`, and policy/git-hygiene decisions open. Recheck each fact before action.
- No runtime activation, credentials, workspace binding, scheduling activation, deployment, auto-merge, merge, or commissioning.

### P2 — Arkadia One source recovery and delivery
- Follow `ARK-ONE-REC-002`: prerequisite A (original source materials) was reported missing; gate FAIL/STOP, recovery not run, no push and no delivery report.
- Search only authorized repository/workspace locations for original, provenance-preserving materials. Record paths, hashes, and source evidence.
- Do not reconstruct missing originals from conversation summaries or claim recovered artifacts are originals.
- Resume the prescribed recovery sequence only after the prerequisite is demonstrably satisfied and the human-authorized scope is clear. Keep local preparation separate from remote delivery.

### P2 — Career and opportunity evidence
- Maintain a small status/evidence entry for IDU/Serenity CV follow-up and the recent LinkedIn message only if source artifacts are present in the repository or supplied by the human.
- Do not infer a response, offer, or commitment. No external messages or applications.

## Universal safety and governance
- Human authority remains final. Automation is a wake signal / bounded worker, not independent authority.
- Never push directly to `main`, force-push, bypass protections, merge PRs, enable auto-merge, deploy, change secrets/credentials, activate production/runtime, or commission.
- Use dedicated task branches and draft PRs. Preserve existing PR ownership and the one-open-PR-per-lane rule.
- No account login, personal-data harvesting, platform appeal submission, competition submission, WhatsApp/email/DM sending, or public communication. Prepare artifacts for human action only.
- No fabricated CI, device, publication, approval, delivery, or acceptance evidence. “Implemented” ≠ “tested”; “tested” ≠ “accepted”; “accepted” ≠ “authorized”; “prepared” ≠ “delivered.”
- Do not change unrelated lanes or scope merely to keep the hourly pulse busy. A truthful no-op/blocked report is preferable to activity theater.

## Durable output required each pulse
Write/update a dated record containing:
- exact BASE_MAIN and branch/head SHA;
- selected lane and bounded objective;
- paths changed and why they are lane-owned;
- commands/tests and actual results;
- evidence links and status classification;
- PR link/status (draft, unmerged);
- blocker / next legal step / human decision required;
- ledger/state/glance updated.

## Source links — read and follow
- [Repository agent instructions](../../../../AGENTS.md)
- [Bootstrap scope](../../../../.bootstrap/03_SCOPE.md)
- [Engineering Runner contract](../../ENGINEERING-RUNNER.md)
- [Arkadia One mission contract](../../../architecture/ARKADIA-ONE-MISSION-CONTRACT-01.md)
- [L1 agent runtime implementation and mutation boundary](../../../architecture/GATE-L1_AGENT_RUNTIME_IMPLEMENTATION.md)
- [Chief / human merge governance](../evidence/gov-01-weaver-conditional-merge-authority/AUTHORIZATION.md)
- [Current Chief merge / regression evidence](../evidence/)
- [Sonata Android project](../../../../sonata-android/)
- [Sonata capability-contract branch](https://github.com/Arkadia-Oversoul-Prism/Arkadia/tree/feature/device-capability-contract-001)
- [Sonata CI run](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/44824465496)
- [Arkadia One REC-002 source recovery record](https://github.com/Arkadia-Oversoul-Prism/Arkadia/search?q=ARK-ONE-REC-002&type=code)
- [Plateau Code preserved Reel URL](https://www.instagram.com/reel/Df7Cv0yqlJS/)

**Human-facing summary:** This directive authorizes focused repository engineering and evidence preparation only. It does not authorize any external contact, account action, merge, deployment, or production activation.
