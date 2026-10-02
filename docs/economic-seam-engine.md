# Economic Seam Engine

Evidence-first economic reconnaissance for procurement, incentives, energy, petroleum, telecoms, capital markets, finance and public economic data.

## Truth contract
- A source is not an opportunity.
- A keyword hit is a lead, not a valuation.
- Every emitted lead carries a legal-basis string and evidence IDs tied to a fetched source URL and content hash.
- Fetch failure produces a source error, never synthetic data.
- Eligibility, price, counterparty, licensing, tax treatment and transaction economics remain unresolved until independently verified.
- The engine does not execute trades, move money, submit bids, or create authorization.

## Runtime
The engine runs inside the existing long-lived FastAPI process. Default cadence is 30 minutes via ECONOMIC_SEAM_INTERVAL_SECONDS. POST /api/economic-seams/scan forces a sovereign scan. Authenticated users can read status and opportunities.

## Source boundary
The engine currently scans official/public endpoints for NOCOPO/BPP, NIPC, NERC, NCC, NUPRC, NMDPRA, SEC, CBN, NISER, World Bank procurement, AfDB procurement and trade finance, IFC trade finance, NGX disclosures, CBN FX rates, NEPC indicative commodity prices and a public carbon-registry feed. The engine never invents a feed URL. Cross-border settlement feeds and any registry requiring authentication remain gated until an authoritative endpoint is validated.

## Promotion path
Future promotion from LEAD to VERIFIED_CANDIDATE must require at least two independent evidence classes plus explicit eligibility, transaction economics and counterparty verification.
