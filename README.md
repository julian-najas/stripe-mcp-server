# Stripe Idempotent Payments Demo

![CI](https://github.com/YOUR_USERNAME/stripe-idempotent-payments-demo/workflows/CI/badge.svg)

**Production-ready FastAPI application** demonstrating Stripe PaymentIntents with full idempotency, webhook handling, and MCP integration for AI agents.

---

## 🎯 Features

✅ **Idempotent payment creation** - Same `Idempotency-Key` = cached response (no double charges)  
✅ **Stripe PaymentIntents** - Real integration ready (currently mocked for tests)  
✅ **Webhook listener** - Signature verification + status updates  
✅ **Database persistence** - SQLite/Postgres with SQLAlchemy  
✅ **MCP Server** - Expose payments as AI agent tools  
✅ **34 passing tests** - Unit, integration, and E2E coverage  
✅ **Production patterns** - Services layer, repositories, structured logging

---

## 📦 Quick Start

### 1. Install

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or pip
pip install -e ".[dev]"
```

### 2. Run Tests

```bash
pytest -v
# ✓ 34 passed (payments + webhooks + MCP + E2E)
```

### 3. Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🚀 API Usage

### Create Payment (Idempotent)

```bash
curl -X POST http://localhost:8000/api/v1/payments/intent \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"amount":5000,"currency":"usd","description":"Order #123"}'
```

**Response:**
```json
{
  "id": "payment_abc123",
  "stripe_intent_id": "pi_xxxxx",
  "amount": 5000,
  "currency": "usd",
  "status": "processing",
  "created_at": "2026-01-17T00:00:00Z"
}
```

### Get Payment Status

```bash
curl http://localhost:8000/api/v1/payments/{payment_id}
```

---

## 🔐 Configuration

### Development Mode (.env)

```env
DEBUG=true                                # No auth required
STRIPE_API_KEY=sk_test_xxxxx            # Stripe test key
STRIPE_WEBHOOK_SECRET=whsec_xxxxx       # Webhook secret
USE_STRIPE_REAL=false                   # Use mocks for tests
```

### Production Mode

```env
DEBUG=false
API_KEY=your-secret-key                 # Required for auth
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
USE_STRIPE_REAL=true
DATABASE_URL=postgresql://...
```

---

## 📖 Documentation

- **[STRIPE_INTEGRATION.md](./STRIPE_INTEGRATION.md)** - Full API reference, webhook setup, production checklist
- **[MCP_VALIDATION.md](./MCP_VALIDATION.md)** - MCP server setup and validation

---

## 🧪 Test Coverage

```bash
pytest -v
# 34 tests:
#   - 6 MCP integration tests
#   - 5 Stripe E2E tests (create + webhook flow)
#   - 6 Payment idempotency tests
#   - 17 API/health/tools tests
```

**Test scenarios:**
- Same idempotency key returns cached response
- Webhook updates payment status (succeeded/failed/canceled)
- Invalid webhook signatures rejected
- Duplicate webhooks handled gracefully
- MCP tools exposed correctly

---

## 🏗️ Architecture

```
POST /payments/intent
  ↓
Check idempotent cache (DB)
  ↓
Create Stripe PaymentIntent
  ↓
Store payment + cache response
  ↓
Return 201 + payment details

... User completes payment ...

Stripe webhook → POST /webhooks/stripe
  ↓
Verify signature
  ↓
Update payment status
  ↓
Return 200 OK
```

### Project Structure

```
app/
├── api/              # FastAPI routers
│   ├── payments.py   # Payment endpoints
│   ├── webhooks/     # Stripe webhook handler
│   └── ...
├── services/         # Business logic
│   ├── payments.py   # Payment service
│   └── stripe/       # Stripe client wrapper
├── db/               # Database layer
│   ├── models.py     # SQLAlchemy models
│   └── repository.py # Data access
└── core/             # Config, auth, logging
```

---

## 🛠️ Key Features Explained

### Idempotency

**Problem:** Network timeouts can cause double charges.

**Solution:** 
```python
# Same key = same response (cached)
POST /payments/intent
Headers: Idempotency-Key: "abc123"

# First request: Creates charge
# Retry: Returns cached response ✅
```

### Webhook Handling

```python
# Stripe sends: payment_intent.succeeded
POST /webhooks/stripe
Headers: stripe-signature: "..."

# Server:
# 1. Verify signature (HMAC)
# 2. Update payment status in DB
# 3. Return 200 OK
```

### MCP Integration

Payments exposed as Model Context Protocol tools at `/mcp`:
```python
# AI agents can:
# - create_payment_intent(amount, currency)
# - get_payment_status(payment_id)
```

Run `python validate_mcp.py` to test.

---

## 🔧 Development

### Run Server

```bash
uvicorn app.main:app --reload
```

### Run Tests

```bash
# All tests
pytest -v

# Specific suite
pytest tests/test_stripe_e2e.py -v

# With coverage
pytest --cov=app tests/
```

### Validate MCP

```bash
python validate_mcp.py
# ✓ MCP VALIDATION PASSED
```

---

## 📋 Production Checklist

Before deploying:

- [ ] Set `DEBUG=false` and configure `API_KEY`
- [ ] Use real Stripe keys (`sk_live_...`)
- [ ] Set `USE_STRIPE_REAL=true`
- [ ] Configure webhook endpoint in Stripe Dashboard
- [ ] Use Postgres instead of SQLite
- [ ] Enable HTTPS for webhook endpoint
- [ ] Add rate limiting
- [ ] Configure monitoring (Sentry, DataDog, etc.)

---

## 📚 Further Reading

- [Stripe PaymentIntents API](https://stripe.com/docs/api/payment_intents)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Built with:** FastAPI • Stripe • SQLAlchemy • Pydantic • MCP
4. **Postgres** → Para producción escalable
5. **Refunds** → Manejo de reembolsos

## Licencia

MIT
