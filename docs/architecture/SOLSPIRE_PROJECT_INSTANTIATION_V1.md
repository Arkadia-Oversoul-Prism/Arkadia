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
- Existing Arkana conversation surface and explicit project-context pack.
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
metadata. Other metadata remains project data. Unknown template IDs are rejected.

## Runtime contract

Each instantiated project declares Weaver as its operational engine and Arkana
as its conversational interface. The contract explicitly records that the
sandbox is required but not configured by template creation. A template is not
proof of a live integration and does not confer execution authority.

Consequential actions remain behind the existing human authorization and
governed execution boundaries. Project ownership remains derived from the
authenticated UID; template metadata cannot grant access.

## Bounded implementation status

This slice establishes the server-owned template contract and project-creation
surface. It does not yet implement a new sandbox runtime, change Weaver's
execution authority, bind Living Larder records, or claim that Arkana's context
is automatically injected into every conversation. Those require separate
verified seams and acceptance tests.

## Verification

- Unit tests cover default template selection, Eden's declared domain module,
  unknown-template rejection, immutable catalog copies and reserved metadata.
- Existing project ownership and project persistence contracts remain unchanged.
- No production mutation or deployment is part of this change.
