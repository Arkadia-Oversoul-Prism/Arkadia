# Economic Seam Engine: evidence-gated correlation

Evidence-first economic reconnaissance for procurement, incentives, energy, petroleum,
telecoms, capital markets, finance and public economic data.

## Truth contract
- A source is not an opportunity. A keyword hit is a lead, not a valuation.
- Every scanner lead carries a source URL and content hash. A legal-basis string is a citation lead, not proof of eligibility.
- Fetch failure produces a source error, never synthetic data.
- The scanner does not execute trades, move money, submit bids, or create authorization.

## Runtime and API
The engine runs inside the existing long-lived FastAPI process. Default cadence is 30
minutes via `ECONOMIC_SEAM_INTERVAL_SECONDS`. `POST /api/economic-seams/scan` forces
a sovereign scan. Authenticated users can read status and opportunities.
`POST /api/economic-seams/assess` accepts an explicit evidence bundle and transaction
facts, applies the promotion gates, and persists the assessment. It is sovereign-only
and does not initiate execution.

## Promotion gates
- `LEAD`: fewer than two independent evidence classes with distinct source identities.
- `CANDIDATE_SEAM`: at least two evidence classes and distinct source identities, but one or more verification gates remain open.
- `VERIFIED_CANDIDATE`: at least two independently verified evidence records from distinct source identities, multiple evidence classes, all required transaction facts, a documented explanation of why the spread exists, and explicit human review of legal basis and eligibility.

Required transaction facts: demand, supply, price basis, full costs, capital requirement,
counterparty, execution path, and failure conditions. The legal basis and explanation of
why the spread exists are separately required.

## Independence and provenance
A repost, duplicate URL, or repeated snapshot of the same content hash does not count as
independent evidence. Evidence identity is derived from source ID, source URL, and content
hash. Evidence classes describe the kind of support, not source quality. The
`independently_verified` field is an explicit reviewer attestation, not something the
keyword scanner can set. API callers must not mark evidence verified without having
performed that review.

## Source boundary and current limitations
The scanner currently visits public endpoints for NOCOPO/BPP, NIPC, NERC, NCC, NUPRC,
NMDPRA, SEC, CBN, NISER, World Bank procurement, AfDB procurement and trade finance,
IFC trade finance, NGX disclosures, CBN FX rates, NEPC indicative commodity prices and
a public carbon-registry feed. The carbon feed is not a verified Nigerian statutory
registry and must not be treated as proof of Nigerian project eligibility.

The current scanner still snapshots landing pages rather than parsing individual
NOCOPO tender records, FX time series, commodity prices or company filing events.
Consequently it must not claim that it produces ten verified opportunities per day.
Those source-specific adapters and a reviewer workflow are still required.

This deterministic gate is decision support, not legal advice, a credit decision,
investment advice, or a guarantee of execution. Human reviewers must verify current law,
eligibility, counterparty identity, price validity, taxes, logistics, settlement, and
licensing before any execution decision. No trading, bidding, financing application,
or money movement is initiated by this module.
