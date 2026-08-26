# Testing

Backend and SDK checks:

```bash
uv run ruff check backend sdk
PYTHONPATH=backend:sdk uv run pytest
```

Frontend static checks and production build:

```bash
cd frontend
npm run validate
```

Browser tests require the API running on port 8001 and a completed production frontend build:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api npm run test:e2e
```

The suite covers overview aggregation, explorer filters, ordered flagship trace evidence, repeated-call diagnostics, comparison, and serious/critical Axe findings across the primary routes.
