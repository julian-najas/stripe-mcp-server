# Stripe MCP Server (FastAPI)

Servidor FastAPI + MCP para cobros con Stripe, diseñado para producción: idempotencia real, verificación de webhooks y tests E2E.

## Qué resuelve

Muchos ejemplos de Stripe funcionan en demo, pero fallan cuando hay reintentos, latencia o webhooks duplicados.  
Este repositorio está pensado para esos escenarios reales.

## Características

- Stripe PaymentIntents (server-side)
- Idempotencia persistente (TTL + verificación por hash)
- Webhooks verificados (signature verification)
- MCP expuesto y filtrado (solo tools de pagos)
- Tests E2E (34 tests)
- Documentación operativa

## Arquitectura

HTTP → Services → Repositories → Stripe / DB  
MCP actúa como capa adaptadora entre el agente y la API.

## Quick start

Requisitos: Python 3.12

```bash
cp .env.example .env
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8000
Health:
http://localhost:8000/health
Documentación
STRIPE_INTEGRATION.md
MCP_VALIDATION.md
SECURITY.md
English summary
Production-oriented FastAPI + MCP server for Stripe PaymentIntents with persistent idempotency, verified webhooks, and E2E tests.
```

---

## Ahora ejecuta

```bash
git add README.md
git commit -m "docs: restore Spanish README and remove emojis"
git push
```

Resultado
Tu repo vuelve a:
hablar tu idioma
respetar tu voz
mantener nivel técnico
sin postureo Copilot
sin estética TikTok
sin perder autoridad internacional (bloque en inglés)
Cuando esté subido, seguimos con:
Coverage badge
Demo live
Diagrama
Pero ahora el repo vuelve a ser Julián Najas, no Copilot.
Cuando hagas el push, dime y pasamos al siguiente paso quirúrgico.