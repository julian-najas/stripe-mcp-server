# Servidor Stripe MCP (FastAPI)

[![CI](https://github.com/julian-najas/stripe-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/julian-najas/stripe-mcp-server/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![GitHub stars](https://img.shields.io/github/stars/julian-najas/stripe-mcp-server?style=social)](https://github.com/julian-najas/stripe-mcp-server)

Servidor FastAPI preparado para producción que implementa el protocolo MCP y gestiona PaymentIntents de Stripe con idempotencia, verificación de webhooks y pruebas.

## Por qué existe

Este repositorio muestra prácticas aplicables en entornos de producción, atendiendo aspectos que suelen omitirse en ejemplos de Stripe:

- Idempotencia con caché y TTL para evitar cargos duplicados.
- Verificación de firma de webhooks (HMAC) y protección frente a duplicados.
- Persistencia con SQLAlchemy; preparado para PostgreSQL o SQLite.
- Exposición de herramientas MCP para que agentes puedan crear y consultar pagos.
- Cobertura de pruebas: 34 tests (unitarios, integración y E2E).

## Características

- Creación de PaymentIntents en servidor con gestión de idempotencia.
- Verificación de firmas y procesamiento seguro de webhooks.
- Arquitectura en capas: routers → servicios → repositorios → Stripe/DB.
- Endpoints MCP: crear intent y obtener estado de pago.
- Registro estructurado y modo de autenticación configurable (DEBUG vs API_KEY).

## Arquitectura

HTTP → FastAPI routers → Servicios → Repositorios → Stripe / Base de datos

El adaptador MCP queda expuesto en /mcp.

## Inicio rápido

Instalación:

```bash
pip install -e ".[dev]"
```

Ejecutar tests:

```bash
pytest -v
```

Iniciar servidor en desarrollo:

```bash
uvicorn app.main:app --reload --port 8000
```

## Configuración mínima

Crea un archivo `.env` para desarrollo local con el contenido mínimo:

```
DEBUG=true
STRIPE_API_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
USE_STRIPE_REAL=false
```

En producción configura `DEBUG=false`, `API_KEY=<token>`, `USE_STRIPE_REAL=true` y `DATABASE_URL` para Postgres.

## Despliegue (Railway)

Comandos básicos:

```bash
railway login
railway init
railway up
```

Variables de entorno necesarias en Railway:

```
DEBUG=false
API_KEY=<token>
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
USE_STRIPE_REAL=true|false
DATABASE_URL=postgresql://...
```

## Fragmentos de API

- Crear intent (idempotente): `POST /api/v1/payments/intent` con cabecera `Idempotency-Key`.
- Obtener estado: `GET /api/v1/payments/{payment_id}`.
- Webhook: `POST /api/v1/webhooks/stripe` con la cabecera de firma de Stripe.

## Documentación adicional

- `STRIPE_INTEGRATION.md` – Referencia de integración con Stripe y lista de comprobación para producción.
- `MCP_VALIDATION.md` – Validación y pruebas del servidor MCP.
- `SECURITY.md` – Modos de autenticación y notas de seguridad.

## Seguridad

- Verificación de firma de webhooks (HMAC-SHA256).
- Autenticación por clave API en producción.
- Validación de claves de idempotencia y protección ante eventos duplicados.

## Licencia

MIT

## Autor

Julian Najas (https://github.com/julian-najas)
