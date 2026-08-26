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

Browser tests require a completed production frontend build. Playwright starts an isolated SQLite API on port 8001 and the production frontend on port 3001, then stops both:

```bash
cd frontend
npm run test:e2e
```

The suite covers overview aggregation, explorer filters, ordered flagship trace evidence, repeated-call diagnostics, comparison, and serious/critical Axe findings across the primary routes.
