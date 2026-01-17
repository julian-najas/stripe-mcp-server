# Stripe PaymentIntents Integration

## Overview

This project implements **production-ready** Stripe PaymentIntents with:
- ✅ Full idempotency on payment creation
- ✅ Webhook listener with signature verification  
- ✅ Database persistence of payment state
- ✅ End-to-end test coverage
- ✅ MCP (Model Context Protocol) exposure for AI agents

---

## Architecture

```
Client Request
    ↓
POST /api/v1/payments/intent (with Idempotency-Key)
    ↓
Check DB for existing idempotent request
    ↓
Create Stripe PaymentIntent (with idempotency_key)
    ↓
Store in DB: Payment + IdempotentRequest
    ↓
Return 201 + payment_id + client_secret
    
... User completes payment on frontend ...

Stripe sends webhook → POST /webhooks/stripe
    ↓
Verify signature (HMAC SHA256)
    ↓
Update payment status in DB
    ↓
Mark webhook_received = true
    ↓
Return 200 OK
```

---

## API Endpoints

### 1. Create Payment Intent (Idempotent)

```http
POST /api/v1/payments/intent
Headers:
  X-API-Key: <your-api-key>         # Required in production (DEBUG=false)
  Idempotency-Key: <uuid>           # Required for idempotency
  Content-Type: application/json
Body:
{
  "amount": 5000,                    # Amount in cents
  "currency": "usd",
  "description": "Order #12345"
}
```

**Response** (201):
```json
{
  "id": "payment_uuid",
  "stripe_intent_id": "pi_xxxxx",
  "amount": 5000,
  "currency": "usd",
  "status": "processing",
  "created_at": "2026-01-17T00:00:00"
}
```

**Idempotency behavior:**
- Same `Idempotency-Key` → returns cached response (no duplicate charge)
- Different `Idempotency-Key` → creates new payment

---

### 2. Get Payment Status

```http
GET /api/v1/payments/{payment_id}
Headers:
  X-API-Key: <your-api-key>
```

**Response** (200):
```json
{
  "id": "payment_uuid",
  "stripe_intent_id": "pi_xxxxx",
  "amount": 5000,
  "currency": "usd",
  "status": "succeeded",             # succeeded | failed | processing | canceled
  "webhook_received": true,
  "error_message": null,
  "created_at": "2026-01-17T00:00:00",
  "updated_at": "2026-01-17T00:05:00",
  "completed_at": "2026-01-17T00:05:00"
}
```

---

### 3. Stripe Webhook Listener

```http
POST /api/v1/webhooks/stripe
Headers:
  stripe-signature: t=xxx,v1=yyy    # Stripe signature for verification
  Content-Type: application/json
Body:
{
  "id": "evt_xxxxx",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_xxxxx",
      "status": "succeeded",
      ...
    }
  }
}
```

**Supported events:**
- `payment_intent.succeeded` → status = "succeeded"
- `payment_intent.payment_failed` → status = "failed"
- `payment_intent.canceled` → status = "canceled"

**Webhook idempotency:**
- Duplicate webhooks are detected and return 200 without re-processing

---

## Configuration

### Environment Variables

```bash
# .env
DEBUG=true                                      # Skip API key validation
ENVIRONMENT=development

# Stripe
STRIPE_API_KEY=sk_test_xxxxx                   # Your Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_xxxxx              # Webhook signing secret
USE_STRIPE_REAL=false                          # false = mock (tests), true = real API

# Database
DATABASE_URL=sqlite:///./stripe_demo.db        # Or postgres://...

# API
API_KEY=your-secret-key                        # Required when DEBUG=false
```

---

## Running the Application

### 1. Install Dependencies
```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 2. Start Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Create payment (DEBUG mode, no API key needed)
curl -X POST http://localhost:8000/api/v1/payments/intent \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"amount":1000,"currency":"usd","description":"Test payment"}'

# Get payment status
curl http://localhost:8000/api/v1/payments/{payment_id}
```

---

## Testing

### Run All Tests
```bash
pytest -v
```

### Test Coverage
- **34 tests** covering:
  - Payment creation with idempotency
  - Webhook handling (success, failure, cancellation)
  - Signature verification
  - Duplicate webhook handling
  - MCP integration
  - End-to-end flows

### Example Test Scenarios

**1. Idempotency Test:**
```python
# Same idempotency key returns same payment
response1 = create_payment(idempotency_key="key-1")
response2 = create_payment(idempotency_key="key-1")
assert response1["id"] == response2["id"]
```

**2. Webhook Test:**
```python
# Create payment → simulate webhook → verify status
payment = create_payment()
send_webhook(event="payment_intent.succeeded", intent_id=payment["stripe_intent_id"])
status = get_payment_status(payment["id"])
assert status["status"] == "succeeded"
```

---

## MCP Integration

Payment endpoints are exposed via **Model Context Protocol** at `/mcp` for AI agents.

### Available Tools
- `create_payment_intent` - Create idempotent payment
- `get_payment_status` - Query payment state

### Connect MCP Client
```bash
# Run validation
python validate_mcp.py
```

See [MCP_VALIDATION.md](./MCP_VALIDATION.md) for details.

---

## Production Checklist

Before deploying:

- [ ] Set `DEBUG=false`
- [ ] Configure real `STRIPE_API_KEY` (starts with `sk_live_`)
- [ ] Configure `STRIPE_WEBHOOK_SECRET` from Stripe Dashboard
- [ ] Set strong `API_KEY` for authentication
- [ ] Use Postgres instead of SQLite (`DATABASE_URL`)
- [ ] Set up Stripe webhook endpoint in dashboard
- [ ] Configure HTTPS for webhook endpoint
- [ ] Set `USE_STRIPE_REAL=true`
- [ ] Enable rate limiting
- [ ] Configure logging/monitoring (Sentry, DataDog, etc.)

---

## Troubleshooting

### Webhook Signature Verification Fails
- Ensure `STRIPE_WEBHOOK_SECRET` matches value from Stripe Dashboard
- Verify webhook endpoint uses HTTPS in production
- Check that raw body is passed to verification (no JSON parsing before verification)

### Payment Shows "processing" Forever
- Check that webhook endpoint is publicly accessible
- Verify webhook is configured in Stripe Dashboard
- Check logs for webhook errors

### Idempotency Not Working
- Ensure `Idempotency-Key` header is sent
- Check that database is properly initialized
- Verify SQLite/Postgres connection

---

## Next Steps

1. **Frontend Integration:**
   - Use `client_secret` from payment creation
   - Integrate Stripe.js or Stripe Elements
   - Handle payment confirmation on client

2. **Additional Features:**
   - Refunds API
   - Payment method management
   - Subscription support
   - Multi-currency

3. **Monitoring:**
   - Add Stripe webhook monitoring
   - Track payment success/failure rates
   - Alert on failed webhooks

---

**Documentation:** [Stripe PaymentIntents API](https://stripe.com/docs/api/payment_intents)  
**Webhook Guide:** [Stripe Webhooks](https://stripe.com/docs/webhooks)
