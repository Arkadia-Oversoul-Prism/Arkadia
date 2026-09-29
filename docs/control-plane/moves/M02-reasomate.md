# M02 — ReasoMate Truth

Status: PENDING
Depends on: M01

## Objective
Make ReasoMate a truthful authenticated conversational surface inside the NovaNet architecture.

## Required invariants
- `/reasomate` must not silently resolve to Oracle.
- ReasoMate uses the existing conversational runtime.
- No second chatbot, identity, memory, or reasoning subsystem.
- Private conversation remains user-scoped.

## Acceptance
Navigation, direct route handling, authentication, message send/load, and persistence resolve to ReasoMate without semantic redirection to Oracle.

## Verification
Run route tests, authenticated conversation tests, build checks, and inspect runtime paths for duplicate memory/chat systems.

## Stop condition
Stop at review. Do not advance to M03 until M02 is accepted.
