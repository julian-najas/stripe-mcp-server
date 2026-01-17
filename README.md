# Stripe MCP Server (FastAPI)

Servidor FastAPI + MCP para cobros con Stripe, diseñado para produccion: idempotencia real, verificacion de webhooks y tests E2E.

## Que resuelve

Muchos ejemplos de Stripe funcionan en demo, pero fallan cuando hay reintentos, latencia o webhooks duplicados.  
Este repositorio esta pensado para esos escenarios reales.

## Caracteristicas

- Stripe PaymentIntents (server-side)
- Idempotencia persistente (TTL + verificacion por hash)
- Webhooks verificados (signature verification)
- MCP expuesto y filtrado (solo tools de pagos)
- Tests E2E (34 tests)
- Documentacion operativa

## Arquitectura


graph TB
  AG[AI Agent] --> MCP["/mcp endpoint"]
  MCP --> API[FastAPI Router]
  API --> SVC[PaymentService]
  SVC --> IDEM[IdempotencyRepository]
  IDEM --> DB[(SQLite)]
  API -.->|Webhook| STRIPE[Stripe API]



## Quick start

Requisitos: Python 3.12

```bash
cp .env.example .env
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health:

[http://localhost:8000/health](http://localhost:8000/health)

## Documentacion

* STRIPE_INTEGRATION.md
* MCP_VALIDATION.md
* SECURITY.md

## English summary

Production-oriented FastAPI + MCP server for Stripe PaymentIntents with persistent idempotency, verified webhooks, and E2E tests.
