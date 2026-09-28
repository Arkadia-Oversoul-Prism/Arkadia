# Eden Food Systems — SolSpire Enterprise Pilot

**Status:** EDEN-SOLSPIRE-01 INSTANTIATION + ARCHITECTURE SCAFFOLD

Eden Food Systems is the first enterprise workload modelled against the existing SolSpire Enterprise layer.

This is not a separate intelligence system. It is an enterprise operating context projected through the canonical SolSpire workspace, WorkEvent spine, Workload model, project resources, and governed dashboard surfaces.

## Product boundary

| Surface | Role |
|---------|------|
| **Solariun** | Personal intelligence canvas — *not* the Eden office |
| **SolSpire** | Enterprise / team operating console — Eden lives here |

## Instantiation (runtime)

Authenticated:

```http
POST /solspire/enterprise/workspaces/templates/eden-food-systems
Authorization: Bearer <firebase-id-token>
```

Or in UI: **SolSpire → Instantiate Eden Food Systems pilot**

Creates for the calling subject:

1. Enterprise: Eden Food Systems  
2. Pilot workload: ₦1m Controlled Food Systems Pilot — Cycle 01  
3. Seven active workstreams (D01–D07)  
4. Contingency reserve as budget allocation (not a staffed department)  
5. Member roles with status `UNASSIGNED` until real people bind  
6. Week 1 operating cadence  
7. Dashboard projection config  

## Pilot

- Budget: ₦1,000,000  
- Operating window: 4 weeks  
- Objective: execute one controlled commodity transaction while building the minimum repeatable operating system  
- Motto: From Source to Market  
- Active workstreams: Procurement, Logistics, Quality, Marketing, Brand/CX, Digital, Operations/Finance  
- Contingency / Reserve: budget control only  

## Architectural rule

The eight budget categories are resource streams. The seven active departments are accountable desks. Contingency is reserve. The eight execution phases are the transaction lifecycle. The dashboard is the projection that makes those dimensions inspectable together.

```
Enterprise
  └── Eden Food Systems
       └── Pilot Workload
            ├── Workstreams / Departments
            ├── Four-week Calendar
            ├── WorkEvents / evidence
            └── Master Dashboard (projection)
```

## Existing SolSpire surfaces reused

- Canonical authenticated workspace  
- Enterprise onboarding  
- Workloads / WorkEvents  
- Projects / files / conversations / tasks / memory  
- Enterprise dashboard projection  
- Advisory analysis channel  
- Knowledge OS / source attachments  

## Truth boundary

The dashboard MUST distinguish:

- RECORDED — supported by a stored work event or artifact  
- COMMITTED — explicitly approved/assigned but not yet completed  
- ESTIMATED — planning assumption  
- UNKNOWN — not yet supplied or evidenced  

Budget allocations ≠ committed ≠ spent ≠ recovered.  
Identity / ownership ≠ execution authorization.

## What this is not

- Not a new Eden database  
- Not a new auth system  
- Not a second Solariun shell  
- Not a financial ledger  
- Not autonomous execution  
