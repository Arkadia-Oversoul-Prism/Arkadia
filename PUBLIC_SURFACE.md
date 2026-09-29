# Public Surface Contract

**Status:** ACTIVE  
**Scope:** public GitHub repository  
**Authority:** human  
**Rule:** public architecture is inspectable; private operational data is not.

## Purpose

This document defines what Arkadia intentionally exposes through its public repository.

The public repository is a **proof surface**, not a private memory store and not a complete dump of the operating environment.

## Green: public by design

These may be committed when they contain no private data:

- architecture specifications
- public-facing documentation
- ADRs and evidence records
- implementation code
- tests and fixtures that contain no real credentials or private data
- public demos and UI
- public opportunity research
- public contact information published by organizations themselves
- sanitized operational examples
- explicit records of uncertainty, limitations, and deferred work

## Amber: structure may be public, contents require review

These need case-by-case handling:

- partner intelligence
- client requirements
- proposal material
- internal commercial strategy
- negotiation notes
- detailed opportunity-response tracking
- personal relationship records
- deployment diagnostics
- datasets derived from private sources
- screenshots or transcripts containing private information

Prefer public schemas, contracts, and sanitized examples over private contents.

## Red: never commit

- API keys
- passwords
- bearer tokens
- private keys
- Firebase service-account credentials
- webhook secrets
- authentication artifacts
- private Knowledge OS vault notes
- client-confidential documents
- unpublished personal data
- private financial/account information

`.gitignore` is a hygiene control, not an authorization boundary. A human-authorized review is still required before sensitive material enters a public commit.

## Knowledge OS boundary

The repository contains the implementation of the Knowledge OS, but the **personal vault runtime is private**.

Tracked vault content is limited to scaffolding and documentation. Runtime-generated personal notes are excluded by repository hygiene rules.

The distinction is:

```
Knowledge OS implementation     → PUBLIC
Knowledge OS schema/contracts    → PUBLIC
Private vault contents           → PRIVATE
Private credentials              → PRIVATE
```

## Opportunity Radar boundary

Opportunity Radar may persist public opportunity intelligence and the structure needed to operate the radar.

It must not become a public dumping ground for:

- private conversations
- unpublished partner responses
- sensitive negotiation state
- personal contact databases
- confidential proposal material

The repository should preserve the **economic movement and evidence model**, while private operational detail belongs behind the appropriate access boundary.

## Verification rule

A public statement should be classified before it is treated as evidence:

- **VERIFIED** — directly verified against current implementation/runtime/source
- **SUPPORTED** — supported by reliable evidence but not independently runtime-verified here
- **LEAD** — useful signal requiring verification
- **UNKNOWN** — not established
- **EXPIRED** — previously valid, no longer current
- **REJECTED** — tested or sourced and found invalid

Historical documents remain historical. They are not automatically current truth.

## Review questions

Before merging a public-facing change:

1. Does it contain a secret?
2. Does it contain private personal or client data?
3. Does it reveal a private operational boundary that should remain private?
4. Does the documentation accurately distinguish implemented, proposed, and verified?
5. Does the change create a second database, memory system, or authority path?
6. Can a stranger inspect the claim from the repository without requiring private context?

If the answer to any of the first three is yes, stop and sanitize or move the material to the appropriate private boundary.

**Public architecture. Private substrate. Human authority. Evidence over assertion.**
