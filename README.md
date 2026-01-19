# Stripe MCP Production Server

This is not:

- Not a Stripe SDK
- Not a tutorial
- Not a playground

This is a production MCP payment server.
---
## Agent roles

| Role      | Allowed actions      |
|-----------|---------------------|
| read_only | list_intents        |
| payments  | create, confirm     |
| admin     | refunds             |

Role is resolved from ENV or upstream agent identity.

**Stripe payments for AI agents in production.  
Idempotency. Verified webhooks. Audit-ready.**

Not a demo.  
Not an SDK.  
Operational infrastructure.

---

## Guarantees

- Core logic covered by tests
- Webhooks verified with HMAC
- Idempotency enforced
- CI blocks regression

## What this server solves

Stripe integrations usually fail in production because of:

- Retries with different payloads
- Duplicated webhooks
- Partial failures
- Agent hallucinations calling payment tools

This server enforces:

- Persistent idempotency
- Webhook signature verification
- Deterministic responses
- E2E tested payment flows

---

## MCP Identity

This server exposes a Model Context Protocol interface for AI agents.

It can be consumed by any MCP-compatible client using `server.json`.

---

## Tool risk model

| Tool | Description | Risk |
|------|-------------|------|
| create_payment_intent | Create Stripe PaymentIntent | Medium |
| confirm_payment_intent | Confirm intent with idempotency | Medium |
| handle_webhook | Consume verified webhook | Low |
| refund_payment | Refund an intent | High |
| list_intents | Query intents | Low |

High-risk tools must be restricted by role or environment.

---

## Quickstart — 5 minutes

```bash
git clone https://github.com/julian-najas/stripe-mcp-server
cd stripe-mcp-server
cp .env.example .env
pip install -e .
uvicorn app.main:app --reload
Set Stripe test keys in .env.


Your MCP Stripe server is now running.

## Example flow — SaaS subscription

1. Agent receives: "Create 29€/month subscription for user@email.com"
2. list_customers(email)
3. create_payment_intent(amount=2900, customer_id)
4. Frontend confirms
5. Webhook validates
6. Agent updates user status

Every step is idempotent and auditable.
