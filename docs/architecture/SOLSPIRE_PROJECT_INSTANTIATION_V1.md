# SolSpire Sovereign Project Instantiation v1

## Purpose

SolSpire Projects are the enterprise layer of Arkadia Oversoul Prism. A project
is an instance of the existing canonical project model plus system-managed
runtime configuration. Business identity and operating procedures are project
data, not product-specific branches.

## Existing spine reused

- Authenticated Firebase UID and the existing project ownership check.
- Existing `projects` row and its `metadata` field.
- Existing project files, conversations, tasks, memory and activity events.
- Existing project-scoped Weaver endpoints and governed engineering execution.
- Existing Arkana conversation surface and explicit project-context pack. This slice now fetches a bounded snapshot of project tasks, files, memory and activity through owner-scoped APIs and injects it into project-scoped Arkana turns; project threads use a project-specific local thread key.
- Existing Daily Pulse, WorkEvent, workload, evidence and Knowledge OS routes.

No second project database, task system, memory store or event spine is introduced.

## Template contract

`GET /solspire/project-templates` exposes the supported template catalog.
`POST /solspire/projects` accepts `template_id` and persists the resolved
contract under system-owned `metadata.project_runtime`.

Initial templates:

- `enterprise`: generic reusable enterprise project.
- `eden-food-systems`: Eden's operating profile with Living Larder declared as
  a domain module that still requires live capability verification.

The server owns `project_runtime`; clients cannot override it through supplied
metadata. Its capability list is explicitly a target list, not a live-capability
claim. Weaver and Arkana binding states are named; sandbox and Living Larder
remain separately classified. Other metadata remains project data. Unknown
template IDs are rejected.

## Runtime contract

Each instantiated project declares Weaver as its operational engine and Arkana
as its conversational interface. The contract explicitly records that the
sandbox is required but not configured by template creation. A template is not
proof of a live integration and does not confer execution authority.

Consequential actions remain behind the existing human authorization and
governed execution boundaries. Project ownership remains derived from the
authenticated UID; template metadata cannot grant access.

## Bounded implementation status

This slice establishes the server-owned template contract, project
creation surface, bounded Arkana context, and a project-scoped read-only canvas
that reuses the existing Engineering Lab session, authorization, sandbox and
evidence spine. Canvas sessions store `project_ref` on the existing session
model, verify the project owner, and materialize only canonical project files
under a server-derived root. A human must authorize the session before a model
run. Weaver is limited to read/list tools; writes, terminal execution, network
access and client-supplied sandbox roots are refused.

This is a filesystem-confined, read-only sandbox, not an OS/container isolation
boundary. It does not yet persist agent-generated workspace changes into
canonical project files, automatically include Daily Pulse/WorkEvent/Knowledge
Graph results in Arkana's context, or bind Living Larder transaction records.
The current bounded Arkana context includes project tasks, file names, memory
entries, activity events, workflow summaries and a knowledge-graph count
projection; unavailable sources remain visible. The next seams require separate
verification and acceptance tests.

## Verification

- Unit tests cover default template selection, Eden's declared domain module,
  unknown-template rejection, immutable catalog copies and reserved metadata.
- Existing project ownership and project persistence contracts remain unchanged.
- No production mutation or deployment is part of this change.
