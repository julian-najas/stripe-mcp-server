# Stripe Idempotent Payments Server

[![CI](https://github.com/julian-najas/stripe-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/julian-najas/stripe-mcp-server/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25%20core-brightgreen)](https://github.com/julian-najas/stripe-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

FastAPI server para Stripe PaymentIntents con idempotencia persistente y verificación de webhooks.

## Qué problema resuelve

| Problema | Solución |
|----------|----------|
| Peticiones duplicadas crean cargos duplicados | Idempotencia persistente con TTL 24h |
| Webhooks duplicados procesan múltiples veces | Deduplicación por payment_id |
| Webhooks falsificados | Verificación HMAC obligatoria |
| Agentes AI no pueden operar pagos | Endpoint MCP integrado |

## Garantías

| Métrica | Valor | Verificación |
|---------|-------|--------------|
| Cobertura módulos core | 100% | `python scripts/check_core_coverage.py` |
| Cobertura global | ≥95% | `--cov-fail-under=95` en CI |
| Tests | 87 | `pytest -v` |
| CI | GitHub Actions | Falla si baja cobertura |

Módulos core (100% branch coverage obligatorio):
- `app/core/auth.py`
- `app/services/payments.py`
- `app/services/stripe/client.py`
- `app/db/repository.py`
- `app/api/webhooks/stripe.py`

## Quick Start

```bash
git clone https://github.com/julian-najas/stripe-mcp-server.git
cd stripe-mcp-server
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -e ".[dev]"
```

Configurar `.env`:

```env
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DEBUG=true
```

Ejecutar:

```bash
uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
```

## Webhooks Local

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

Copiar `whsec_...` a `.env`.

## Deploy Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Variables requeridas en Railway:

| Variable | Valor |
|----------|-------|
| `STRIPE_API_KEY` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` |
| `API_KEY` | Clave para autenticar clientes |
| `DEBUG` | `false` |

Webhook en Stripe Dashboard: `https://tu-app.railway.app/api/v1/webhooks/stripe`

## Tests

```bash
pytest -v                              # Ejecutar todos
pytest --cov=app --cov-branch          # Con cobertura
python scripts/check_core_coverage.py  # Verificar core 100%
```

## API

### Crear Payment Intent

```bash
curl -X POST http://localhost:8000/api/v1/payments/intent \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-123" \
  -d '{"amount": 2000, "currency": "usd"}'
```

### MCP (AI Agents)

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "create_payment_intent", "arguments": {"amount": 1000, "currency": "usd"}}}'
```

## Estructura

```
app/
├── api/payments.py          # Endpoints REST
├── api/webhooks/stripe.py   # Verificación webhooks
├── core/auth.py             # Autenticación API key
├── db/repository.py         # Idempotencia persistente
├── services/payments.py     # Lógica de negocio
└── services/stripe/client.py # Cliente Stripe
```

## Documentación

- [STRIPE_INTEGRATION.md](STRIPE_INTEGRATION.md) - Integración Stripe y checklist producción
- [MCP_VALIDATION.md](MCP_VALIDATION.md) - Validación servidor MCP
- [SECURITY.md](SECURITY.md) - Autenticación y seguridad

## Licencia

MIT

## Autor

[Julian Najas](https://github.com/julian-najas)
