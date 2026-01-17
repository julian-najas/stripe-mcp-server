# Release Notes

## v0.1.0 (2026-01-17)

🎉 **Initial Release** - Production-ready Stripe PaymentIntents with idempotency and MCP integration.

### ✨ Features

- **Stripe PaymentIntents Integration**
  - Create payment intents via REST API
  - Real Stripe API support (configurable via `USE_STRIPE_REAL` flag)
  - Mock mode for testing without Stripe credentials
  - Support for USD and multi-currency payments

- **Idempotency System**
  - Prevent duplicate payments with `Idempotency-Key` header
  - 24-hour TTL on cached responses
  - Request hash verification to detect accidental key reuse
  - Database-backed idempotency storage

- **Webhook Handling**
  - HMAC SHA256 signature verification
  - Support for `payment_intent.succeeded`, `payment_intent.payment_failed`, `payment_intent.canceled`
  - Automatic payment status updates
  - Webhook idempotency to handle duplicate events

- **MCP (Model Context Protocol) Integration**
  - Expose payment tools to AI agents
  - HTTP transport at `/mcp` endpoint
  - Restricted to `payments` tag for security
  - Header forwarding: `authorization`, `x-api-key`, `idempotency-key`

- **Production Architecture**
  - Services layer for business logic
  - Repository pattern for data access
  - Structured logging with request IDs
  - Environment-based configuration
  - SQLite (dev) and PostgreSQL (prod) support

### 🧪 Testing

- **34 passing tests** with comprehensive coverage:
  - 6 MCP integration tests
  - 5 Stripe end-to-end tests
  - 6 payment idempotency tests
  - 17 API and health check tests
- GitHub Actions CI pipeline
- Coverage reporting with codecov

### 📚 Documentation

- Complete API reference in `STRIPE_INTEGRATION.md`
- MCP validation report in `MCP_VALIDATION.md`
- Production deployment checklist
- Contribution guidelines in `CONTRIBUTING.md`

### 🛠️ Technical Stack

- Python 3.12
- FastAPI 0.115.0
- Stripe SDK 11.5.0
- fastapi-mcp 0.4.0
- SQLAlchemy 2.x
- Pydantic v2
- pytest for testing

### 🔧 Configuration

All configuration via environment variables (see `.env.example`):
- `STRIPE_API_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Webhook signing secret
- `USE_STRIPE_REAL` - Enable real Stripe API (default: false)
- `DATABASE_URL` - SQLite or PostgreSQL connection
- `API_KEY` - API authentication key

### 🚀 Quick Start

```bash
# Install
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your Stripe keys

# Run tests
pytest tests/

# Start server
uvicorn app.main:app --reload
```

### 📋 API Endpoints

- `POST /api/v1/payments/intent` - Create payment intent
- `GET /api/v1/payments/{payment_id}` - Get payment status
- `POST /api/v1/webhooks/stripe` - Stripe webhook handler
- `POST /mcp` - MCP endpoint for AI agents

### 🔒 Security

- API key authentication required
- Webhook signature verification
- Idempotency key validation
- Environment variable secrets
- No hardcoded credentials

### 📈 Next Steps

Future enhancements planned:
- Support for Stripe Checkout Sessions
- Payment method management
- Refund handling
- Advanced webhook event support
- GraphQL API
- Docker deployment

---

For detailed documentation, see [README.md](./README.md) and [STRIPE_INTEGRATION.md](./STRIPE_INTEGRATION.md).
