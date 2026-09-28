# Eden Food Systems — SolSpire Enterprise Pilot

**Move:** EDEN-SOLSPIRE-01  
**Role:** First real enterprise instance inside existing SolSpire substrate.

## Product boundary

| Surface | Role |
|---------|------|
| **Solariun** | Personal intelligence canvas — *not* the Eden office |
| **SolSpire** | Enterprise / team operating console — Eden lives here |

## Instantiation

Authenticated POST:

```http
POST /solspire/enterprise/workspaces/templates/eden-food-systems
Authorization: Bearer <firebase-id-token>
```

Creates for the **calling subject only**:

1. Enterprise: Eden Food Systems  
2. Pilot workload: ₦1m Controlled Food Systems Pilot — Cycle 01  
3. Seven active workstreams (D01–D07)  
4. Contingency reserve as **budget allocation**, not a staffed department  
5. Member **roles** with status `UNASSIGNED` until real people bind  
6. Week 1 operating cadence  
7. Dashboard projection config  

## Truthfulness

- Budget allocations ≠ committed ≠ spent ≠ recovered  
- Dashboard preserves `UNKNOWN` for committed/spent/remaining until evidence exists  
- Identity / ownership ≠ execution authorization  

## What this is not

- Not a new Eden database  
- Not a new auth system  
- Not a second Solariun shell  
- Not a financial ledger  
- Not autonomous execution  

