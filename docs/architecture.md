# Architecture

AgentScope separates instrumentation, validated ingestion, durable trace state, deterministic diagnostics, and the query interface.

```text
Python SDK
   │ complete trace document
   ▼
FastAPI ingestion boundary
   ├── validates timestamps, identities, parent references, and event ordering
   ├── resolves Project and Agent identity
   ├── persists Trace, Span, and Event records atomically
   └── runs explainable diagnostic detectors
             │
             ▼
        PostgreSQL / SQLite local mode
             │
             ▼
FastAPI query API ──► Next.js overview, explorer, detail, comparison, diagnostics
```

## Trace graph reconstruction

Ingestion writes spans in two passes. The first pass assigns durable IDs for every external span ID. The second resolves `parent_external_id` values to database foreign keys, so parent records do not need to arrive before children in the submitted array. Events then resolve their optional span reference and persist in unique sequence order.

The payload validator rejects missing parents, self-parenting, duplicate span IDs, unknown event span references, duplicate sequences, and reversed timestamps before the transaction begins.

## Idempotency

`(project_id, external_id)` uniquely identifies a trace. A repeated upload returns the existing trace with HTTP 200 and does not duplicate spans or events. New traces return HTTP 201.

## Diagnostics

V1 diagnostics are explicit rules rather than opaque anomaly scores:

- the same tool and canonical arguments at least three times;
- recorded execution errors;
- non-object tool arguments;
- context that more than doubles and exceeds 8,000 input tokens;
- execution lasting at least 60 seconds;
- estimated cost of at least $0.10.

Every finding persists its threshold or matching evidence alongside a human-readable explanation.

## Deliberate constraints

- PostgreSQL is sufficient for the measured V1 workload; ClickHouse is not justified.
- Diagnostics run inline with ingestion for determinism and a small operational surface.
- The SDK uploads the complete graph when a trace closes; streaming ingestion is deferred.
- Authentication and multi-tenant access control are outside this synthetic local V1.
