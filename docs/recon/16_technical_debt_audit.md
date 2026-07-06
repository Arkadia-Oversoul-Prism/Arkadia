# 16 — Technical Debt Audit

| Item | Location | Risk Level | Estimated Cleanup Effort |
|---|---|---|---|
| Unsigned-JWT dev-mode auth fallback reachable if env var missing | `api/auth.py:31-41,197` | Critical (security) | Small — add a startup guard (few lines) |
| Hardcoded Gemini key in committed files | `archive/legacy_python/entrypoint.sh:30`, `DEPLOYMENT_GUIDE.md` | High (security) | Small — rotate key, scrub docs |
| Hardcoded `SOVEREIGN_KEY` | `api/main.py:36` | High (security) | Small — move to env var |
| Wildcard CORS | `api/main.py:186-190` | Medium (security) | Small — restrict origin list |
| No rate limiting on LLM-backed endpoints | `api/main.py`, `arkana_space/app.py` | Medium (cost/abuse) | Medium — add middleware + limits |
| Stub `call_image_agent` left in codebase after real tool exists | `kernel/agents.py:16` | Low (dead code) | Small — remove or clearly mark deprecated |
| Inactive `_piper_fallback.py` alongside active Edge TTS | `kernel/_piper_fallback.py` | Low (dead code) | Small — remove if confirmed unused |
| Up to 4 parallel intent-execution stacks (`kernel`, `solspire`, `engine`, `parsers`+`schemas`) | repo-wide | Medium-High (maintainability, onboarding confusion) | Large — requires an explicit architecture decision + possible removal/consolidation |
| Three-way duplicated IMS Archive rendering | `IMSArchivePage.tsx`, `NexusPage.tsx`, `ShereSanctuary.tsx` | Medium (product-facing inconsistency, actively being fixed elsewhere this session) | Medium |
| Encyclopedia Galactica name collision (two different features, same name) | `EncyclopediaGalactica.tsx` vs `NexusPage.tsx`'s `EncyclopediaGalacticaMatrix` | Low-Medium (naming confusion) | Small — rename one |
| Root `package.json` version drift vs. shipped frontend | `/package.json` vs `web/public_prism/package.json` | Medium (build confusion risk) | Medium — audit which root deps are actually used, prune the rest |
| `piper-tts` still in `requirements.txt` despite being replaced | `/requirements.txt` | Low (bloat) | Small — remove if confirmed unused |
| `openclaw/` has 3 simultaneous deploy configs | `openclaw/render.yaml`, `fly.toml`, `railway.json` | Medium (deployment ambiguity) | Small — confirm and remove the unused two |
| Full nested duplicate project inside assets folder | `attached_assets/arkadia_spirit/GovernanceSpirit/` | Low (repo bloat/noise) | Medium — relocate or archive externally |
| Two parallel Android clients | `sonata/` (Java), `sonata-android/` (Kotlin) | Low-Medium (maintenance overhead if both are still built) | Medium — confirm `sonata/` is safe to archive |
| Documentation-vs-code drift: TF-IDF/summarization claims in `replit.md` don't match simpler actual implementations | `replit.md` vs `corpus/`, `api/main.py` | Low (accuracy only, not a functional bug) | Small — update replit.md wording |
| Unclear caller status of `engine/`, `parsers/`, `schemas/`, `arkana_rasa/`, `sanctum/` | repo-wide | Medium (unknown-unknowns risk) | Medium — grep for imports repo-wide to confirm live/dead status definitively |
| `weaver/notes/*.txt` runtime log accumulation in version control (if committed) | `weaver/notes/` | Low (repo bloat, potential secret-in-logs risk) | Small — confirm gitignored; if not, add to `.gitignore` and purge |

## Commented-Out Code / Broken Integrations
Not exhaustively grepped this session for commented-out code blocks specifically (would require a dedicated `# TODO`/`# FIXME`/block-comment sweep across ~40+ Python/TS files) — flagged as a follow-up if deeper technical-debt granularity is desired.

## Overall Technical Debt Posture
The codebase shows the classic signature of **rapid, ambitious, multi-phase iterative development** (explicit Phase 4 → Phase 8 kernel evolution, well-documented in replit.md) rather than accumulated neglect. Most debt here is **architectural sprawl** (parallel stacks, parallel deploy configs, parallel duplicate pages) rather than classic code rot. The security findings (auth fallback, hardcoded keys) are the only items that carry real production risk today; everything else is a maintainability/clarity concern.
