# AgentScope

Trace observability and deterministic diagnostics for AI agents.

AgentScope answers: **what exactly happened while the agent was working?** It persists the execution graph—traces, hierarchical spans, ordered events, model usage, tool calls, errors, and final results—then makes that evidence searchable and comparable.

## Overview

The V1 is a locally reproducible full-stack product with a dependency-free Python SDK, validated FastAPI ingestion boundary, relational trace model, deterministic diagnostic detectors, and a Next.js trace explorer. Six original synthetic traces cover success, error recovery, a repeated tool loop, expensive context growth, malformed arguments, and a failed result.

## Key capabilities

- create and upload traces through a small context-manager SDK;
- reconstruct parent/child spans even when children arrive first;
- preserve uniquely ordered model, tool, retrieval, log, error, and output events;
- aggregate latency, tokens, estimated cost, outcome, and common-tool metrics;
- filter traces by agent, status, duration, cost, error, and tool;
- inspect event payloads and final results;
- compare two durable traces and their metric deltas;
- detect repeated identical calls, tool errors, malformed arguments, context growth, slow traces, and expensive traces;
- avoid duplicate graphs on delivery retries.

## Architecture

```text
Python SDK → FastAPI ingestion → PostgreSQL → FastAPI query API → Next.js explorer
                         └──── deterministic diagnostics ────┘
```

See [docs/architecture.md](docs/architecture.md) for graph reconstruction, idempotency, and diagnostic decisions.

## Quick start

```bash
uv sync --all-groups
PYTHONPATH=backend:sdk uv run uvicorn agentscope_server.main:app --port 8001
```

In another terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api npm run dev
```

Open `http://localhost:3001`.

Alternatively, run `docker compose up --build` for PostgreSQL, API, and frontend containers.

## SDK

```python
from agentscope import AgentScope

scope = AgentScope(project_slug="research", project_name="Research")

with scope.trace("research-agent", input={"question": question}) as trace:
    with trace.span("web_search", type="tool") as span:
        trace.event("tool_call", "web_search", payload={"arguments": {"query": question}})
        result = search(question)
        span.set_output(result)
    trace.set_result({"answer": summarize(result)})
```

## Testing

```bash
uv run ruff check backend sdk
PYTHONPATH=backend:sdk uv run pytest
cd frontend && npm run validate
```

After the production frontend build, execute `npm run test:e2e` in `frontend`. Playwright manages an isolated SQLite API and the frontend server for the browser and Axe suite. See [docs/testing.md](docs/testing.md).

## Project structure

```text
backend/agentscope_server/  FastAPI API, persistence, ingestion, diagnostics
backend/tests/              API and domain tests
sdk/agentscope/             dependency-free instrumentation client
sdk/tests/                  SDK contract tests
frontend/                   Next.js trace explorer
docs/                       architecture, development, and testing notes
```

## Technical decisions and tradeoffs

- PostgreSQL is the production-shaped store; SQLite keeps direct local startup small.
- Deterministic diagnostics remain explainable and testable.
- Complete-document uploads make V1 retries simple; streaming spans are deferred.
- Seed records are synthetic and clearly identified.
- Authentication, tenant isolation, retention policy, and arbitrary telemetry volume are not claimed in V1.

## Roadmap

- schema migrations and retention controls;
- streaming or batched span delivery;
- background diagnostic processing for higher throughput;
- project access controls;
- deployment hardening and an optional hosted demo.

## Contributing and license

No contribution policy or license is claimed yet. Add them only after the repository owner chooses the terms.
