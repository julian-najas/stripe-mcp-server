# 🚀 Stripe MCP Server

[![CI](https://github.com/julian-najas/stripe-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/julian-najas/stripe-mcp-server/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
[![GitHub stars](https://img.shields.io/github/stars/julian-najas/stripe-mcp-server?style=social)](https://github.com/julian-najas/stripe-mcp-server)

> **Industrial-grade FastAPI + MCP server for Stripe PaymentIntents**  
> Real idempotency, verified webhooks, 34 passing tests.

---

## ✨ Why this matters

Most Stripe examples are toys. **This is production-ready**:
- ✅ **Idempotency** with TTL cache (no duplicate charges)
- ✅ **Webhook signature verification** (HMAC + replay protection)
- ✅ **MCP protocol** for AI agents to create/query payments
- ✅ **34 tests** (unit + integration + E2E)
- ✅ **Clean architecture** (Services → Repositories → DB)

Perfect for:
- 🤖 AI payment agents
- 💳 SaaS billing systems
- 🛠 Learning production Stripe patterns

---

## 🎬 Quick Start

```bash
# 1. Install dependencies
uv pip install -e ".[dev]"  # or pip install -e ".[dev]"

# 2. Set up environment
cp .env.example .env
# Edit .env with your Stripe keys

# 3. Run tests
pytest -v  # 34 tests pass ✅

# 4. Start server
uvicorn app.main:app --reload --port 8000
```

🌐 **API Docs**: http://localhost:8000/docs  
🔍 **Health check**: http://localhost:8000/health  
🚀 **Live demo setup**: See [`LIVE_DEMO.md`](./LIVE_DEMO.md) for instant public URL

---

## 📚 Key Features

### 💰 Payment Intents
```bash
POST /api/v1/payments/intent
Headers: 
  Idempotency-Key: unique-key-123
  Content-Type: application/json
Body:
  { "amount": 2000, "currency": "usd" }
```

### 🔔 Webhooks
```bash
POST /api/v1/webhooks/stripe
Headers:
  Stripe-Signature: t=...,v1=...
```
✅ Automatic signature verification  
✅ Duplicate event protection

### 🤖 MCP Tools
AI agents can:
- `create_payment_intent(amount, currency, metadata)`
- `get_payment_status(payment_id)`

---

## 🏗 Architecture

```
HTTP Request
    ↓
FastAPI Router
    ↓
Service Layer (business logic)
    ↓
Repository Layer (DB/Stripe)
    ↓
SQLAlchemy Models / Stripe API
```

**MCP endpoint**: `/mcp` (stdio or SSE transport)

**Visual architecture:**

```mermaid
graph TB
    AG[AI Agent] -->|JSON-RPC| MCP[/mcp endpoint]
    HTTP[HTTP Request] --> ROUTER[FastAPI Router]
    MCP --> ROUTER
    ROUTER --> PAYMENT[PaymentService]
    ROUTER --> WEBHOOK[WebhookService]
    PAYMENT --> REPO[PaymentRepository]
    WEBHOOK --> REPO
    REPO --> DB[(SQLite/PostgreSQL)]
    PAYMENT -.->|API calls| STRIPE[Stripe API]
    WEBHOOK -.->|Verify HMAC| STRIPE
    
    style MCP fill:#e1f5ff
    style PAYMENT fill:#fff4e6
    style WEBHOOK fill:#fff4e6
    style STRIPE fill:#635bff,color:#fff
```

**Key components:**
- **MCP Layer**: Exposes only `payments`-tagged tools to AI agents
- **Service Layer**: Business logic (idempotency, webhook verification)
- **Repository Layer**: Data persistence and Stripe API interaction
- **Database**: SQLite (dev) or PostgreSQL (prod)

---

## 🚀 Deploy to Railway

```bash
railway login
railway init
railway up
```

**Required env vars**:
```env
DEBUG=false
API_KEY=your-secret-key
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
USE_STRIPE_REAL=true
DATABASE_URL=postgresql://...  # optional, defaults to SQLite
```

---

## 📖 Documentation

| File | Description |
|------|-------------|
| [`STRIPE_INTEGRATION.md`](./STRIPE_INTEGRATION.md) | Stripe setup & production checklist |
| [`MCP_VALIDATION.md`](./MCP_VALIDATION.md) | MCP server validation guide |
| [`SECURITY.md`](./SECURITY.md) | Auth modes & security notes |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to contribute |

---

## 🧪 Testing

```bash
# All tests
pytest -v

# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests (requires Stripe test keys)
pytest tests/e2e -v
```

**Coverage**: 34 tests covering:
- Payment creation & idempotency
- Webhook verification & processing
- MCP tool exposure
- Error handling

---

## 🔐 Security

- 🔒 Webhook signature verification (HMAC-SHA256)
- 🔑 API key authentication (production mode)
- 🛡 Idempotency key validation
- 🚫 Duplicate event protection
- 📝 Structured logging (no secrets)

See [`SECURITY.md`](./SECURITY.md) for details.

---

## 📦 Tech Stack

- **FastAPI** - Modern Python API framework
- **Stripe Python SDK** - Official Stripe library
- **SQLAlchemy** - ORM with Postgres/SQLite support
- **Pydantic** - Request/response validation
- **MCP** - Model Context Protocol for AI agents
- **pytest** - Testing framework

---

## 🤝 Contributing

PRs welcome! See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 📄 License

MIT - See [`LICENSE`](./LICENSE)

---

## 🙋‍♂️ Author

Built by [Julian Najas](https://github.com/julian-najas)

---

**⭐ Star this repo if you find it useful!**
