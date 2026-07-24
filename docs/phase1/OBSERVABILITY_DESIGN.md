# Phase 1 — Observability Design

**Status:** Design complete. Awaiting approval before implementation.  
**Date:** 2026-07-24  
**Workstream:** D — Observability

---

## Current State

`kernel/metrics.py` provides in-process counters for tool usage, plan success rates, and goal runs. It is a good foundation but has gaps:

| What exists | What is missing |
|---|---|
| Per-tool call counts, success rate, p50/p95 latency | Request ID correlation across the full request/job lifecycle |
| Plan source tracking (LLM vs fallback) | Execution ID (unique per job run — distinct from job ID) |
| Goal run tracking | Planner latency separate from provider latency |
| In-memory snapshot (resets on restart) | Knowledge retrieval timing |
| No structured log format | Per-step timing within a plan chain |
| Python `logging` is unstructured text | Persistent metrics (survive restart) |

---

## Observability Philosophy (Phase 1)

Phase 1 is **structured logging first**. The sequence is intentional:

```
Phase 1:  Structured logs  ← this document
Phase 2:  Metrics          ← expose structured data as queryable counters
Phase 3:  Tracing          ← correlate spans across the full chain
```

Do not instrument for Prometheus, OpenTelemetry, or any external system yet.
Emit structured JSON logs to stdout. Every log event carries enough context
that a human (or a future metrics layer) can reconstruct the full picture
from the log stream alone.

---

## Context IDs (Required)

Every request that enters the system must carry two IDs through its entire lifecycle:

### `request_id`
- Generated at the API boundary (FastAPI middleware)
- Returned in every HTTP response as `X-Request-Id` header
- Propagated into the job intent when a job is created: `intent["request_id"]`
- Included in every log event for the duration of the request

### `execution_id`
- Generated fresh each time `execute_intent()` is called
- Distinct from `job_id` (a job can re-run after failure; each run gets a new execution_id)
- Included in all step-level log events

```python
# Proposed shape:
request_id    = "req_a3f7c1"    # at API boundary
job_id        = "job_4e9d20"    # at job creation
execution_id  = "exec_b2d8f4"   # at each execute_intent() call
step_id       = "step_0"        # per step within a plan
```

---

## Structured Log Events

All log events are emitted as JSON objects via `logging` at INFO level.
A single `StructuredLogger` wrapper converts them:

```python
# kernel/observability.py

import json, logging, time, uuid

class StructuredLogger:
    def __init__(self, name: str):
        self._log = logging.getLogger(name)

    def emit(self, event: str, **fields) -> None:
        record = {"event": event, "ts": time.time(), **fields}
        self._log.info(json.dumps(record, default=str))
```

### Event Catalog

```
REQUEST_RECEIVED
  request_id, method, path, source

JOB_CREATED
  request_id, job_id, intent_type, source

JOB_CLAIMED
  job_id, execution_id, worker_id, retries

PLAN_STARTED
  job_id, execution_id, request_id, intent_type, input_len

PLAN_GENERATED
  job_id, execution_id, plan_source (llm|fallback|user),
  planner_latency_ms, step_count

STEP_STARTED
  job_id, execution_id, step_id, tool, input_summary

STEP_COMPLETED
  job_id, execution_id, step_id, tool,
  step_latency_ms, success, status

KNOWLEDGE_RETRIEVED
  job_id, execution_id, query_len,
  retrieval_latency_ms, source (knowledge_vault|oracle_store|none),
  result_count

PROVIDER_CALLED
  job_id, execution_id, provider (gemini|claude|gpt),
  model, provider_latency_ms, tokens_in, tokens_out, success

JOB_COMPLETED
  job_id, execution_id, total_latency_ms, success, step_count

JOB_FAILED
  job_id, execution_id, total_latency_ms, retries, error_summary

GOAL_TRIGGERED
  goal_id, job_id, cadence_seconds, run_count

TOOL_BLOCKED
  execution_id, tool, reason (not_in_allowlist|not_permitted|no_approval)

SECURITY_EVENT
  event_subtype, execution_id, detail (never log actual content)
```

---

## Timing Model

Every timed span is recorded as `<name>_latency_ms`:

```
total_latency_ms
  └── planner_latency_ms
      ├── knowledge_latency_ms   (context retrieval)
      ├── provider_latency_ms    (LLM call)
      └── sum(step_latency_ms)   (chain execution)
```

Timing is always wall-clock, never CPU time (external I/O dominates).
Use `time.perf_counter()` for sub-millisecond precision; convert to ms for logging.

---

## Implementation Plan

### Step 1: `kernel/observability.py` (new file)

```python
class StructuredLogger:
    def emit(self, event, **fields): ...

def get_logger(name: str) -> StructuredLogger: ...

# Context vars for request_id / execution_id propagation
# Use contextvars.ContextVar — safe across async and thread boundaries
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_execution_id_var: ContextVar[str | None] = ContextVar("execution_id", default=None)

def set_request_id(rid: str) -> Token: ...
def get_request_id() -> str | None: ...
def new_execution_id() -> str: ...
```

`contextvars.ContextVar` propagates correctly:
- In FastAPI async routes (each request gets its own context)
- In daemon worker threads (`copy_context().run(...)` pattern)

### Step 2: FastAPI middleware

```python
# api/main.py — add after CORS middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex[:8]}"
    token = set_request_id(rid)
    try:
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response
    finally:
        _request_id_var.reset(token)
```

### Step 3: Instrument execute_intent()

```python
def execute_intent(intent: dict) -> dict:
    eid = new_execution_id()
    token = _execution_id_var.set(eid)
    t0 = time.perf_counter()
    try:
        obs.emit("JOB_STARTED", execution_id=eid, intent_type=intent.get("type"))
        result = _do_execute(intent)
        obs.emit("JOB_COMPLETED", execution_id=eid,
                 total_latency_ms=_ms(t0), success=result.get("success"))
        return result
    except Exception as e:
        obs.emit("JOB_FAILED", execution_id=eid,
                 total_latency_ms=_ms(t0), error_summary=str(e)[:200])
        raise
    finally:
        _execution_id_var.reset(token)
```

### Step 4: Instrument planner, knowledge retrieval, provider calls

Each emit point takes ~3 lines. Add in a single commit to `kernel/planner.py` and `kernel/memory.py`.

### Step 5: Connect existing metrics.py

`metrics.record_tool_call()` is called from the structured log emit path:
```python
# In StructuredLogger.emit() for STEP_COMPLETED:
if event == "STEP_COMPLETED":
    metrics.record_tool_call(fields["tool"], success=fields["success"],
                              duration_ms=fields["step_latency_ms"])
```

This keeps `metrics.py` in sync without duplicating instrumentation points.

---

## What This Does Not Do

- Does not write to a file (stdout only; log aggregation is the platform's job)
- Does not integrate with Prometheus, Datadog, or OpenTelemetry (Phase 2)
- Does not add distributed tracing (Phase 3)
- Does not persist metrics across restarts (Phase 2 — store snapshots in SQLite)
- Does not log user content (only lengths, counts, and hashes where needed)
- Does not change `kernel/metrics.py` (it continues to work as before; the new logger calls into it)

---

## File Plan

```
kernel/
  observability.py    ← new: StructuredLogger, context vars, event helpers

api/
  main.py             ← add: request_id middleware (5 lines)

kernel/
  execution.py        ← add: execution_id context, JOB_STARTED/COMPLETED/FAILED events
  planner.py          ← add: PLAN_STARTED, PLAN_GENERATED, PROVIDER_CALLED events
  memory.py           ← add: KNOWLEDGE_RETRIEVED event
  worker.py           ← add: JOB_CLAIMED event with worker_id and execution_id

tests/
  test_observability.py   ← new: verify event shapes, context propagation
```

---

## Example Log Output

```json
{"event": "JOB_CREATED", "ts": 1753401600.123, "request_id": "req_a3f7c1", "job_id": "job_4e9d20", "intent_type": "__plan__", "source": "web"}
{"event": "JOB_CLAIMED", "ts": 1753401600.145, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "worker_id": 0, "retries": 0}
{"event": "PLAN_STARTED", "ts": 1753401600.146, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "intent_type": "__plan__", "input_len": 47}
{"event": "KNOWLEDGE_RETRIEVED", "ts": 1753401600.167, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "retrieval_latency_ms": 21.3, "source": "knowledge_vault", "result_count": 3}
{"event": "PLAN_GENERATED", "ts": 1753401601.234, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "plan_source": "llm", "planner_latency_ms": 1088.2, "step_count": 2}
{"event": "STEP_COMPLETED", "ts": 1753401601.287, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "step_id": "step_0", "tool": "read_file", "step_latency_ms": 53.1, "success": true, "status": "success"}
{"event": "JOB_COMPLETED", "ts": 1753401601.301, "job_id": "job_4e9d20", "execution_id": "exec_b2d8f4", "total_latency_ms": 1156.8, "success": true, "step_count": 2}
```

Every line is a self-contained JSON object. `grep exec_b2d8f4 | jq .` reconstructs the full execution trace without a tracing backend.

---

*Next document: CONTINUATION_LEDGER.md*
