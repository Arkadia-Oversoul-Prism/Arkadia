# CAL-10 — Solariun / SolSpire Product Boundary + Enterprise Onboarding

**Status:** IMPLEMENTED ON BRANCH · RUNTIME VERIFICATION PENDING · HUMAN MERGE GATE

## Product boundary

Arkadia now exposes two distinct authenticated product surfaces:

- **Solariun** — personal intelligence canvas: personal projects, knowledge, files, conversations, tasks, memory and Weaver context.
- **SolSpire** — enterprise organizational operating console: enterprises, teams/workspaces, projects, workloads, workstreams, members, knowledge, files, operating context and master dashboards.

They share the existing Arkadia authentication and governed backend substrate, but their product responsibilities are explicit in the UI.

## Enterprise onboarding protocol

The first enterprise experience is a generic seven-step protocol:

1. Create enterprise workspace context.
2. Establish the pilot workload.
3. Establish workstream records.
4. Assign member relationships and ownership.
5. Attach operating context, including budget and operating assumptions.
6. Create Week 1 operating objectives and tasks.
7. Project the governed context into the master dashboard.

The protocol contains no Eden, Barnabas, commodity, department, or other tenant-specific assumptions.

## AI analysis

Each onboarding step can invoke the existing Arkana/LLM channel for advisory analysis.

The model may identify:
- missing information;
- structural gaps;
- dependencies;
- relationship candidates;
- operating risks;
- questions for the human operator.

LLM output is stored as advisory analysis. It does not create authority, authorization, provenance, execution, or completion evidence.

## Master dashboard

The dashboard is a projection of enterprise context:

ENTERPRISE → WORKLOAD → WORKSTREAMS → MEMBERS → OPERATING CONTEXT → WEEK 1 → DASHBOARD

Unknown or unprovided values remain UNKNOWN.

Budget entered during onboarding is operating context. It is not evidence that funds were deposited, committed, spent, recovered, or reconciled.

## Sovereignty boundary

- Enterprise membership is not sovereign authority.
- Product tier is not authorization.
- LLM analysis is not authorization.
- Dashboard state is not provenance.
- Dashboard state is not execution.
- Existing WorkEvent and protected K15/K3 boundaries remain authoritative.