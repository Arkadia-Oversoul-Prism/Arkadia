# 21 — Prioritized Refactor Roadmap

## P0 — Security (do before next production deploy)
1. Add a startup guard preventing the unsigned-JWT dev-mode auth fallback from ever activating when `ENVIRONMENT=production` (`api/auth.py`).
2. Rotate and remove the hardcoded Gemini API key from `archive/legacy_python/entrypoint.sh` and `DEPLOYMENT_GUIDE.md`.
3. Move `SOVEREIGN_KEY` (`api/main.py:36`) to an environment secret; rotate the current value.

## P1 — Product-Facing Correctness
4. Consolidate the three IMS Archive rendering surfaces (`NexusPage.tsx`, `IMSArchivePage.tsx`, `ShereSanctuary.tsx`) into one shared data source + component — directly resolves the user-reported "incomplete/placeholder" IMS Archive issue. *(Already in progress in this session's parallel workstream.)*
5. Restrict CORS from wildcard to the known frontend origin(s).
6. Add basic rate limiting to Gemini-backed endpoints (`/api/commune/resonance`, `/api/ceo/chat`, `arkana_space` `/oracle`) to control cost/abuse exposure.

## P2 — Architectural Clarity
7. Resolve the up-to-four-parallel-execution-stacks ambiguity: grep-confirm whether `engine/` and `parsers/`+`schemas/` have any live callers; if not, remove them; if so, document their role relative to `kernel/`.
8. Rename one of the two "SolSpire" systems (`kernel/` vs `solspire/`) to eliminate the naming collision in documentation, nav labels, and onboarding conversations.
9. Reconcile `openclaw/`'s three simultaneous deploy configs (Render/Fly.io/Railway) down to whichever is actually live; delete the rest.
10. Document the OpenClaw gateway, Weaver autonomy layer, and SolSpire console in `replit.md` — all three are real, live-or-experimental subsystems currently absent from the project's own README.

## P3 — Dependency & Config Hygiene
11. Audit and prune root-level `package.json` — confirm which dependencies are genuinely used at the repo root vs. vestigial from an earlier layout; align versions with `web/public_prism/package.json` where both are legitimately needed.
12. Remove `piper-tts` from `requirements.txt` if confirmed fully replaced by Edge TTS.
13. Confirm whether `wouter` or `react-router-dom` (or neither) is actually needed in the frontend, given navigation is state-based; remove the unused one.

## P4 — Repository Hygiene
14. Relocate or remove `attached_assets/arkadia_spirit/GovernanceSpirit/` (full duplicate nested project) from the main repo tree.
15. Confirm `sonata/` (Java) is safe to archive now that `sonata-android/` (Kotlin) is canonical.
16. Confirm `weaver/notes/*.txt` runtime logs are gitignored; if not, add to `.gitignore` and purge from history.
17. Resolve the Encyclopedia Galactica naming collision between the standalone page and `NexusPage.tsx`'s differently-scoped `EncyclopediaGalacticaMatrix`.

## P5 — Documentation Accuracy
18. Update `replit.md`'s corpus-scoring description from "TF-IDF semantic relevance" to the actual priority-tier scoring mechanism, or implement true TF-IDF/embedding scoring if the richer behavior is desired.
19. Update `replit.md`'s conversation-summarization claim to reflect that summarization is currently inactive (sliding-window history only), or re-activate the logic that exists in `archive/legacy_python/build_corpus_summaries.py` if summarization is still wanted.

## P6 — Measurement Before Further Performance Work
20. Run a production frontend build and inspect actual bundle sizes/code-splitting before making any performance-related architectural changes (no performance data currently exists to act on).
21. Add basic request-timing instrumentation to Gemini-backed endpoints to establish real latency baselines.

## Sequencing Note
P0 items are independent of each other and can be done in parallel. P1 item 4 (IMS Archive) is already underway per this session's other active task and should be finished there rather than re-started here. Items P2–P6 are lower urgency and should be scheduled as dedicated cleanup sessions with the user's sign-off, since several (7, 9, 14, 15) involve deleting or relocating code and require explicit confirmation before any destructive action, per this mission's own read-only mandate and the project's broader safety conventions.
