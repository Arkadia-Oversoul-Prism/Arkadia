# MIE · Decisions

## DEC-001

**Date:** 2026-10-02

**Decision:** MIE lives as a bounded musical-instrument track inside the Arkadia Prism repository rather than as a separate repository.

**Context:** The project needs access to Prism's engineering, Android, testing, and agent substrate while retaining an independently discoverable musical grammar.

**Why:** Shared substrate reduces duplication; bounded product space prevents premature coupling to SolSpire or the control plane.

**Evidence:** Existing repository contains `sonata-android/`, Engineering Lab, provider abstractions, and established agent/control-plane discipline.

**Status:** ACTIVE

## DEC-002

**Decision:** The intelligence layer must be replaceable.

**Why:** The product's identity belongs in the musical-object and interaction model, not in a single model provider.

**Status:** ACTIVE
