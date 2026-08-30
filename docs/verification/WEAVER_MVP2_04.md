# WEAVER-MVP2-04 — Embedding Provider Seam

## Invariant

Project Knowledge OS has a real provider adapter boundary, while the default runtime remains honestly `NOT_AVAILABLE` until a concrete provider is configured.

## Proven by tests

- Default provider reports `NOT_AVAILABLE` with no provider, coverage, or dimensions invented.
- A deterministic injected provider can report availability and return vectors through the same adapter contract.
- Knowledge remains read-only and execution remains `LOCKED` regardless of embedding state.
- No semantic graph authority is introduced.
- No authorization, mutation, K15, or K3 path is added.

## Scope

This pass establishes only the provider seam. It does not add a live external embedding service, credentials, vector database, semantic retrieval, or automatic indexing.

## Publication

MVP2-04 is a small adapter-boundary pass and must remain independently reviewable.
