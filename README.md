# Stripe MCP Server (FastAPI)

[![CI](https://github.com/julian-najas/stripe-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/julian-najas/stripe-mcp-server/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

Industrial FastAPI + MCP server for Stripe PaymentIntents with idempotency, webhook verification, and 34 passing tests.

🚀 Live demo (Railway): https://stripe-mcp-server.up.railway.app/health (actualiza si tu subdominio difiere)

## Why this exists
- Most Stripe samples are demo-only; this repo mirrors production concerns: idempotency, signatures, persistence, and test coverage.
- MCP exposure lets AI agents create and query payments through tools.

## Features
- Stripe PaymentIntents (server-side) with idempotency cache and TTL
- Webhook signature verification (HMAC) with duplicate protection
- Services/Repository layering, SQLAlchemy models, Postgres/SQLite ready
- MCP tools: create payment intent, get payment status
- 34 tests: unit + integration + E2E (Stripe and MCP)
- Structured logging and minimal auth toggle (`DEBUG` vs `API_KEY`)

## Architecture
HTTP → FastAPI routers → Services → Repositories → Stripe / DB. MCP is exposed as an adapter at `/mcp`.

```
POST /api/v1/payments/intent
  ↓ check idempotent cache
  ↓ create PaymentIntent (or return cached)
  ↓ persist + return

Stripe → POST /api/v1/webhooks/stripe
  ↓ verify signature
  ↓ update payment status
  ↓ 200 OK
```

## Quick start
```bash
# Install (uv recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Run tests (34 passing)
pytest -v

# Run server
uvicorn app.main:app --reload --port 8000
```

### Minimal config
Create `.env` for local dev:
```
DEBUG=true
STRIPE_API_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
USE_STRIPE_REAL=false
```

For production, set `DEBUG=false`, `API_KEY=<token>`, `USE_STRIPE_REAL=true`, `DATABASE_URL=postgresql://...`, and real Stripe secrets.

## Deployment (Railway)
```bash
railway login
railway init
railway up
```

Ensure env vars in Railway: `DEBUG=false`, `API_KEY=<token>`, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `USE_STRIPE_REAL=true|false`, `DATABASE_URL` (if Postgres). Start command is in Procfile: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## API snippets
- Create intent (idempotent): `POST /api/v1/payments/intent` with `Idempotency-Key` header.
- Get status: `GET /api/v1/payments/{payment_id}`.
- Webhook: `POST /api/v1/webhooks/stripe` with Stripe signature.

## Docs
- STRIPE_INTEGRATION.md – API reference, webhook setup, production checklist
- MCP_VALIDATION.md – MCP server setup and validation

## Security
See SECURITY.md for auth modes, Stripe secret handling, and webhook verification notes.

## License
MIT
