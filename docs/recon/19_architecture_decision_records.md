# 19 — Architecture Decision Records (ADR)

Format: Purpose → Reason for existence → Current implementation → Dependencies → Production status → Known limitations → Technical debt → Recommendation (Keep/Merge/Rewrite/Replace/Remove).

## ADR-01: SolSpire Kernel (`kernel/`)
- **Purpose**: Deterministic, auditable execution layer beneath the Oracle for transactional actions (image gen, logging, open loops, verse, arbitrary tool calls).
- **Reason for existence**: Per replit.md, built explicitly to avoid "no LLM in the kernel itself" risk for actions with real side effects (money/loops/assets).
- **Current implementation**: Phases 4–8 fully implemented (classify → plan → execute → verify → summary, async jobs, tool registry, goals, metrics).
- **Dependencies**: `data/oracle_store.json`, `data/job_store.json`, `data/goal_store.json`, Gemini API (Phase 7 planner only).
- **Production status**: Live, confirmed wired into `api/main.py` startup/shutdown.
- **Known limitations**: No mid-run re-planning; memory is keyword-match, not vector.
- **Technical debt**: Stub `call_image_agent` left alongside real tool.
- **Recommendation**: **Keep.** This is the most mature, well-documented subsystem in the repo.

## ADR-02: SolSpire Console (`solspire/`)
- **Purpose**: Project-management console (conversations/files/repos/tasks/memory/events) scoped per-project, backed by SQLite.
- **Reason for existence**: Different domain than `kernel/` — appears to serve a "manage my dev projects" use case rather than the Oracle's transactional actions.
- **Current implementation**: `console_router.py` mounted; SQLite store confirmed.
- **Dependencies**: `data/solspire_projects.db`, own `llm.py`/`planner.py` Gemini wrapper.
- **Production status**: Live (mounted router).
- **Known limitations**: Name collision with `kernel/`'s "SolSpire" branding causes confusion about whether they're the same system (they are not).
- **Technical debt**: Duplicate Gemini-wrapper pattern vs. `kernel/planner.py`.
- **Recommendation**: **Keep, but rename** one of the two "SolSpire" systems to eliminate the naming collision (e.g., call this one "SolSpire Console/Projects" explicitly everywhere, including in the nav label `SolSpireConsole.tsx`).

## ADR-03: `engine/`, `parsers/`+`schemas/` (unconfirmed-caller execution stacks)
- **Purpose**: Unclear — filenames suggest task execution and intent parsing, overlapping with `kernel/execution.py`.
- **Reason for existence**: Unknown without further investigation or owner input — possibly an earlier prototype superseded by `kernel/`.
- **Current implementation**: Present in the repo; no confirmed import/caller found in `api/main.py`, `kernel/`, or `weaver/` during this pass.
- **Production status**: Unconfirmed — likely dormant.
- **Recommendation**: **Investigate then Remove or Merge.** Do a repo-wide import grep for `from engine`, `from parsers`, `from schemas.intent_schema` before deciding; if truly uncalled, remove to eliminate the "which execution stack is canonical" confusion flagged repeatedly in this report.

## ADR-04: Weaver Autonomy Layer (`weaver/`)
- **Purpose**: Self-governing agent loop with symbolic 6-axis vector reasoning (`echofield/`) operating over `governance/` rules.
- **Reason for existence**: Distinct from the Oracle chat and the kernel — appears to be an experimental/parallel "autonomous agent" capability.
- **Current implementation**: `run_autonomy.py`, `agent.py`, `echofield/` vector stack + retrieval confirmed present; actual invocation trigger (cron? manual? webhook?) not confirmed this session.
- **Production status**: EXPERIMENTAL — status of whether this runs continuously in production is unconfirmed.
- **Known limitations**: Generates timestamped log files (`weaver/notes/*.txt`) accumulating in the repo.
- **Recommendation**: **Investigate production status**, then either formally document it (if live) or move it fully into an experimental/sandbox branch (if not).

## ADR-05: OpenClaw Gateway (`openclaw/`)
- **Purpose**: WhatsApp message gateway to the Oracle backend.
- **Reason for existence**: Extends Oracle access to WhatsApp users, per `docs/DOC1_MASTER_WEIGHTS.md`.
- **Current implementation**: `gateway.js` + config; three simultaneous deploy configs (Render/Fly.io/Railway).
- **Production status**: Assumed live (referenced in doctrine docs with a real phone number) but not runtime-verified this session, and not mentioned in `replit.md` at all.
- **Known limitations**: Deployment target ambiguity; undocumented in the project's own README.
- **Recommendation**: **Keep, but document.** Add an OpenClaw section to `replit.md` and resolve the triple-deploy-config ambiguity.

## ADR-06: IMS Archive (3-way duplicated frontend surface)
- **Purpose**: Display real Identity Mapping Session deliverable documents to users/prospects.
- **Reason for existence**: Grew organically across `NexusPage.tsx`, `IMSArchivePage.tsx`, and `ShereSanctuary.tsx` as the product evolved.
- **Current implementation**: Three independent, non-shared lists of IMS documents with inconsistent coverage.
- **Production status**: Live but inconsistent (already flagged as a defect being actively repaired in this session's parallel workstream).
- **Recommendation**: **Merge.** Consolidate into one shared data source + component, imported by all three entry points.

## ADR-07: Root-level frontend-adjacent dependencies (`/package.json`)
- **Purpose**: Unclear — declares React/Vite/Tailwind at different major versions than the actual shipped frontend.
- **Current implementation**: Present at repo root, not obviously consumed by any build script traced this session.
- **Production status**: Unknown — may be vestigial from an earlier project layout before `web/public_prism/` became the canonical frontend location.
- **Recommendation**: **Investigate then prune.** Confirm nothing depends on root-level `npm install`, then trim the manifest to only what's genuinely used at the root (e.g., Discord bot deps, if the bot is actually run from root rather than `bot/` — needs confirmation).

## ADR-08: `attached_assets/arkadia_spirit/GovernanceSpirit/` (nested duplicate project)
- **Purpose**: Unknown — a complete separate React+Express+Postgres application.
- **Current implementation**: Fully isolated, no confirmed integration with the live product.
- **Production status**: Not part of the live product.
- **Recommendation**: **Remove from main repo tree** (relocate to a separate archival repo if historical value is needed) to reduce repo size/noise and prevent accidental confusion during searches.

## ADR-09: `sonata/` (Java) vs `sonata-android/` (Kotlin)
- **Purpose**: Native Android client for the Sonata product surface.
- **Current implementation**: Two parallel, non-shared codebases for what is presumably the same app.
- **Production status**: Per prior-session memory, `sonata-android/` is the canonical push target.
- **Recommendation**: **Archive `sonata/`** once confirmed safe (no active build/release pipeline still targets it).
