# WEAVER-K13 — Governed Implementation Synthesis

**PROPOSED CHANGESET ≠ EXECUTION ≠ AUTHORIZATION**

## Module

`weaver/implementation.py` — `synthesize_changeset`, `review_changeset`

## Design only

Produces `ProposedFileChange` with operation ADD/MODIFY, symbols from AST, implementation instructions — never applies patches.
