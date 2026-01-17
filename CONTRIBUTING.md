# Contributing to Stripe Idempotent Payments Demo

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 📋 Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

## 🚀 Getting Started

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/stripe-idempotent-payments-demo.git
cd stripe-idempotent-payments-demo
```

2. **Set up development environment**

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
# OR: pip install -e ".[dev]"
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your Stripe test keys
```

4. **Run tests to verify setup**

```bash
pytest tests/
```

## 🔧 Development Workflow

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use [ruff](https://github.com/astral-sh/ruff) for linting
- Maximum line length: 120 characters
- Use type hints wherever possible

```bash
# Run linter
ruff check app tests

# Auto-fix issues
ruff check --fix app tests
```

### Testing

Write tests for all new features and bug fixes:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_payment_idempotency.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new payment method support
fix: resolve webhook signature validation issue
docs: update API documentation
test: add E2E tests for payment flow
refactor: simplify stripe client error handling
```

## 🐛 Reporting Issues

When reporting issues, please include:

- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs/errors

## 💡 Submitting Pull Requests

1. **Create a feature branch**

```bash
git checkout -b feat/your-feature-name
```

2. **Make your changes**
   - Write code with type hints
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**

```bash
# Linting
ruff check app tests

# Tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=app --cov-report=term-missing
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat: add your feature description"
```

5. **Push to your fork**

```bash
git push origin feat/your-feature-name
```

6. **Open a Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Ensure CI passes

## 📚 Project Structure

```
.
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Configuration and logging
│   ├── db/           # Database models and repositories
│   ├── schemas/      # Pydantic models
│   └── services/     # Business logic
├── tests/            # Test suite
├── .env.example      # Environment template
└── pyproject.toml    # Dependencies and metadata
```

## 🔐 Security

If you discover a security vulnerability, please **DO NOT** open a public issue. Instead, email the maintainers directly.

## 📖 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project
- Show empathy towards other contributors

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## 🤝 Questions?

- Open a [Discussion](https://github.com/YOUR_USERNAME/stripe-idempotent-payments-demo/discussions)
- Check existing [Issues](https://github.com/YOUR_USERNAME/stripe-idempotent-payments-demo/issues)
- Read the [Documentation](./README.md)

---

Thank you for contributing! 🎉
