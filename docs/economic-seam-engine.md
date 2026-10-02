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
facts, applies promotion gates, and persists the assessment. It is sovereign-only and
does not initiate execution. Submitted evidence verification flags are forcibly reset
to false by the API. A review action is stamped with the authenticated subject and
server time, but that stamp does not itself verify the underlying evidence.

## Structured NOCOPO adapter
The NOCOPO source now reads the Open Contracting Partnership's published 2026 OCDS
JSONL gzip snapshot by default. Override only with `NOCOPO_OCDS_URL` pointing to an
approved HTTPS data host. The adapter bounds compressed/decompressed size and record
count, parses each JSONL record, normalizes OCID/buyer/tender/deadline/value fields,
and persists records as structured observations. It creates a `LEAD` only when the
record marks the tender active/planned and its date is not implausibly far in the
future. Each lead instructs the operator to recheck the primary notice and documents.
This is a periodically refreshed snapshot, not a real-time tender API. Missing,
invalid, historical, or implausible dates are not promoted to active tender leads.
OCDS publisher data quality is imperfect, so the adapter retains quality flags and
does not infer eligibility, supplier fit, contract profitability, or current status.

## Promotion gates
- `LEAD`: fewer than two registered provider identities across at least two evidence classes.
- `CANDIDATE_SEAM`: at least two provider identities and two evidence classes, but one or more verification gates remain open.
- `VERIFIED_CANDIDATE`: at least two independently verified evidence records from distinct registered providers, multiple evidence classes, all required transaction facts, a documented explanation of why the spread exists, and an auditable human review of legal basis and eligibility.

Required transaction facts: demand, supply, price basis, full costs, capital requirement,
counterparty, execution path, and failure conditions. The legal basis and explanation of
why the spread exists are separately required. The pure assessment function can model a
fully reviewed case for tests or a trusted internal workflow; the public API cannot
self-attest evidence as verified. A source-backed review workflow remains required
before API-submitted cases can reach the verified status.

## Independence and provenance
A repost, duplicate URL, repeated snapshot, or second page from the same registered
provider does not count as independent evidence. Independence is keyed to the
registered `source_id`, not URL or content hash. Evidence classes describe the kind of
support, not source quality. The scanner's keyword layer never marks evidence as
independently verified.

## Source boundary and current limitations
The registry includes NOCOPO/BPP structured procurement records plus public landing-page
snapshots for NIPC, NERC, NCC, NUPRC, NMDPRA, SEC, CBN, NISER, World Bank procurement,
AfDB procurement and trade finance, IFC trade finance, NGX disclosures, CBN FX rates,
NEPC indicative commodity prices and a public carbon-registry feed. Those non-NOCOPO
sources are not yet all parsed as structured datasets. The carbon feed is not a verified
Nigerian statutory registry and must not be treated as proof of Nigerian eligibility.

The NOCOPO adapter currently uses a yearly bulk snapshot; other sources still require
source-specific structured adapters and a reviewer workflow. Consequently the engine
must not claim that it produces ten verified opportunities per day.

This deterministic gate is decision support, not legal advice, a credit decision,
investment advice, or a guarantee of execution. Human reviewers must verify current law,
eligibility, counterparty identity, price validity, taxes, logistics, settlement, and
licensing before any execution decision. No trading, bidding, financing application,
or money movement is initiated by this module.
