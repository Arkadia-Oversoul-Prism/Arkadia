"""Eden Food Systems project seed.

This module contains domain knowledge only. Runtime behavior remains generic:
Weaver, Arkana, Workload, WorkEvents, Knowledge and Files operate through the
canonical SolSpire project instance.
"""
from __future__ import annotations

from solspire.project_store import add_memory, create_file, create_task

EDEN_SEED_VERSION = "2026-10-03.v1"

def seed_eden_project(project_id: str) -> dict:
    """Populate an Eden project from the known operating brief."""
    knowledge = [
        ("01 — Eden operating brief.md", """# Eden Food Systems

Motto: From Source to Market.

Mission: make agricultural food supply more reliable by connecting producers,
markets and buyers through coordinated sourcing, quality control and distribution.

Customer promise: Quality food commodities, sourced and coordinated for you.

Initial sourcing: Plateau State.
Initial destination markets: Abuja, Yola, Maiduguri.
Initial commodities: Irish potato, dry onion, cabbage.

Operating chain:
Plateau Sourcing → Aggregation → Quality Inspection → Packaging →
Transportation → Buyer Delivery → Payment → Financial Reconciliation.

Customer segments:
- food vendors / restaurants
- caterers / event-food operators
- hotels / institutional kitchens
- retailers / market traders
- wholesalers / distributors
Secondary: supermarkets / grocery and processors.

The initial operating cycle is a controlled pilot, not proof of scale.
"""),
        ("02 — Eden controlled pilot.md", """# Controlled Pilot Cycle 01

Pilot allocation: ₦1,000,000.

Allocation:
- commodity acquisition / trading float: ₦500,000
- logistics / transport: ₦120,000
- packaging / handling / QC: ₦45,000
- marketing / customer acquisition: ₦75,000
- branding / content: ₦35,000
- digital tools / data / communications: ₦25,000
- customer care / field operations: ₦30,000
- pilot coordination / management: ₦100,000
- contingency / reserve: ₦70,000

The ₦500,000 commodity float is not yet committed to a fixed commodity or route.
Buyer confirmation, supplier pricing/specification, logistics and transaction
economics must be reconciled before consequential deployment.
"""),
        ("03 — R02 preliminary commercial assessment.md", """# R02 — Preliminary Commercial Assessment / Pre-Pilot

Reference date: 20 September 2026.
Markets under consideration: Abuja, Yola, Maiduguri.
Commodities: potato, onion, cabbage.

Maiduguri field-reported ranges:
- potato lower: ₦65,000–₦67,000
- potato higher: ₦75,000–₦77,000
- dry onion lower: ₦32,000–₦35,000
- dry onion higher: ₦40,000–₦45,000
- cabbage: ₦67,000–₦68,000

These are field-reported reference ranges, not confirmed selling prices.
Exact units, weights, specifications, grades, quote basis and period require
reconciliation before prices become comparable.

Transaction model:
Commodity Purchase Cost + Packaging/Handling + Transportation + Other Direct
Costs = Total Operating Cost.

Expected Gross Sales - Total Operating Cost = Estimated Contribution.

No fixed ROI is to be invented until transaction inputs are reconciled.
"""),
        ("04 — Eden operating control sequence.md", """# Controlled Execution Sequence

1. Buyer Confirmation
2. Supply Confirmation
3. Financial Reconciliation
4. Controlled Execution
5. Financial Reconciliation

For consequential actions, evidence and decision preparation precede human
authorization. WorkEvent records continuity after execution. Where evidence
stops, the claim stops.
"""),
        ("05 — Eden domain projection.md", """# Living Larder

Living Larder is Eden's commercial / market projection layer.

It is not a second operating database. It should project canonical SolSpire
project state and transaction records rather than create a parallel task,
memory or event spine.

Current domain capability remains subject to live verification.
"""),
    ]
    memories = [
        ("Eden identity", "Eden Food Systems is the project instance for the food sourcing and distribution operating business.", ["identity", "business"]),
        ("Eden route", "Plateau State sourcing toward Abuja, Yola and Maiduguri.", ["route", "market"]),
        ("Eden commodities", "Initial commodities are Irish potato, dry onion and cabbage.", ["commodities"]),
        ("Pilot guardrail", "The ₦1m cycle is a controlled pilot. No fixed ROI or transaction commitment is valid until buyer, supplier, specification, logistics and cost inputs reconcile.", ["governance", "finance"]),
        ("Operating chain", "Sourcing → aggregation → inspection → packaging → transport → delivery → payment → reconciliation.", ["operations"]),
        ("Living Larder", "Living Larder is the commercial projection layer, not a parallel canonical store.", ["domain", "living-larder"]),
    ]
    tasks = [
        ("Confirm first buyer", "Capture buyer, commodity, quantity, specification, destination, required date and quote basis as project evidence.", "high"),
        ("Reconcile first supply quote", "Capture supplier, commodity, quantity, unit, grade/specification, price, geography and quote period.", "high"),
        ("Reconcile logistics", "Capture route, carrier, load assumptions, transport quote and other direct costs.", "high"),
        ("Build first transaction economics", "Calculate purchase cost, direct costs, expected gross sales and contribution only from reconciled inputs.", "high"),
        ("Verify Living Larder seam", "Inspect the existing Living Larder route and determine the minimum project binding required for a canonical commercial projection.", "normal"),
    ]
    counts = {"files": 0, "memory": 0, "tasks": 0}
    for name, body in knowledge:
        create_file(project_id, name, body); counts["files"] += 1
    for title, body, tags in memories:
        add_memory(project_id, title, body, tags); counts["memory"] += 1
    for title, description, priority in tasks:
        create_task(project_id, title, description, assigned_to="WEAVER", priority=priority); counts["tasks"] += 1
    return {"seed_version": EDEN_SEED_VERSION, **counts}
