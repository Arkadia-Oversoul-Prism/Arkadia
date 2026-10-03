# 72-Hour Deal Machine

The Economic Seam Engine now has a transaction-level handoff for Eden's 72-hour hunt.

## Operating sequence

1. **FIND** a demand/supply signal.
2. **COLLAPSE** it into a DealSheet.
3. **CALL** the buyer and supplier and verify the facts.
4. **CALCULATE** revenue, total cost, net realizable spread and capital efficiency.
5. **AUTHORIZE** only after human review.
6. **DEPLOY** the smallest capital amount required to close the verified transaction.

## Hard gates

A DealSheet cannot become executable when any of these remain unverified:

- buyer commitment
- supplier commitment
- buyer/supplier prices
- counterparty identity
- logistics path and cost
- eligibility/compliance
- payment/settlement path
- human authorization

A market-price difference is **not** a profit claim. The engine subtracts logistics and other stated costs before calculating net realizable spread. Missing numbers remain UNKNOWN.

## Capital-efficiency lens

The primary 72-hour metric is:

`capital_efficiency = net_realizable_spread / peak capital required`

This is a transaction-efficiency measure, not a forecast or guarantee.

The engine does not bid, purchase, transfer funds, or bind Eden to a counterparty.
