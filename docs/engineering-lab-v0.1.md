# Arkadia AI Engineering Lab v0.1

## Purpose

The Engineering Lab is a read-only intelligence layer inside Arkadia. It observes the existing repository, Git history, declared canon, API/frontend structure, execution surfaces, and deployment configuration, then normalizes that evidence into an inspectable system model.

**Phase 1 is observational and analytical. It cannot modify Arkadia.**

## Authority

- Level 0: observe
- Level 1: analyse
- Level 2: suggest
- Autonomous mutation: disabled
- Production mutation: disabled
- Human approval remains outside the Lab loop

The Lab does not replace Oracle, SolSpire, Weaver, Kernel, authentication, persistence, provider infrastructure, or project/workspace architecture.

## Architecture

```text
existing Arkadia substrate
        ↓
deterministic observatory
        ↓
normalized model
        ↓
trajectory + canon
        ↓
system graph
        ↓
structural patterns
        ↓
read-only engineering report
```

The current implementation uses a small `lab/` package and an authenticated `api/lab_routes.py` seam. The API router is composed through the already-mounted node router, avoiding a second application/router hierarchy.

## Observations

The observatory records repository state, files, Python/JS/TS module relationships, API declarations, deployment files, candidate execution surfaces, and redacted security signals. Secret values are never returned.

## Provenance

Facts carry source, confidence, timestamp and provenance. Graph relationships carry evidence and method. Deterministic facts use high confidence only where the collector directly establishes them. Derived interpretations are not canonical.

## Canon loading

Canonical-source discovery begins with repository governance and documentation, including `AGENTS.md`, `README.md`, `governance/`, and `docs/`. Classification is explicit. Repeated implementation patterns are treated as `DERIVED`, not constitutional truth.

## Trajectory

Git history is treated as temporal evidence. The Lab records commit SHA, parentage, timestamp, author, message, changed files and directories, then derives bounded classifications and churn signals.

## Structural patterns

Phase 1 detects evidence-backed candidates for:

- parallel execution paths
- duplicate route/capability surfaces
- deployment configuration multiplicity
- high-churn components
- potentially disconnected modules

Pattern confidence is visible and evidence is retained. A pattern is not an architectural decision.

## API

`GET /api/lab/overview`

The endpoint is authenticated through Arkadia's existing `api.auth.require_auth` dependency and is non-mutating. It reports real repository observations and distinguishes observation failures from empty results through explicit status/error metadata.

## Security

Security inspection is observational only. Detected credential references are reported as redacted classifications. The Lab does not rotate, delete, rewrite or expose credentials.

## Persistence and caching

Phase 1 does not introduce a new database or authoritative Lab store. The repository, Git history, deployment configuration and canonical documents remain sources of truth. A future derived cache must remain rebuildable and non-authoritative.

## Known limitations

- Runtime behavior is inferred from statically inspectable repository evidence rather than executing arbitrary application paths.
- GitHub Actions workflow files were not present in the inspected repository state, so no parallel CI workflow was created.
- Deployment state is configuration evidence, not a claim that a provider deployment is currently healthy.
- Documentation drift requires explicit comparable architecture declarations and is therefore conservative in v0.1.
- Frontend route/component observability is primarily static and does not replace browser verification.

## Next phase

Phase 2 may consume the Lab's evidence model for planning, but autonomous mutation, branch creation, code generation, PR creation, execution loops, durable checkpoints and deployment automation remain outside v0.1.
