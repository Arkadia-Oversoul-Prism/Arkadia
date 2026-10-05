# G12-A · Canonical Capture Reconciliation

Bounded move: preserve one canonical WorkEvent for an authenticated subject + stable capture ID. Exact retry replays the same WorkEvent; conflicting digest/metadata is a deterministic 409. Do not expand into mobile queue behavior.

Current evidence: PR #307. Human review/merge and acceptance remain required.
