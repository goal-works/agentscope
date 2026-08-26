# Development

## Requirements

- Python 3.12+
- Node.js 22+
- uv (recommended) or another PEP 517 installer
- Docker Compose only for the container workflow

## Local processes

From the repository root:

```bash
uv sync --all-groups
PYTHONPATH=backend:sdk uv run uvicorn agentscope_server.main:app --reload --port 8001
```

In another terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api npm run dev
```

Open `http://localhost:3001`. The API creates the local schema and inserts six deterministic synthetic traces on first startup. Repeated startup is idempotent.

## Container workflow

```bash
docker compose up --build
```

The frontend is exposed on port 3001 and the API on port 8001. The container workflow uses PostgreSQL; direct local development defaults to SQLite for a zero-service startup.

## Configuration

Copy `.env.example` to `.env` only when overriding defaults. Never commit credentials. The demo database contains only original synthetic incident-research data.
