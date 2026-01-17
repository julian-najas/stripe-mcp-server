"""Conftest for pytest configuration and fixtures."""
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock


# Ensure env is configured before app/settings modules are imported during test collection.
os.environ.setdefault("DEBUG", "1")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_fake_key_for_testing_only")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake_secret_for_testing_only")


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set up environment for tests."""
    os.environ["DEBUG"] = os.environ.get("DEBUG", "1")
    os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "test")
    os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    os.environ["STRIPE_API_KEY"] = os.environ.get("STRIPE_API_KEY", "sk_test_fake_key_for_testing_only")
    os.environ["STRIPE_WEBHOOK_SECRET"] = os.environ.get(
        "STRIPE_WEBHOOK_SECRET", "whsec_test_fake_secret_for_testing_only"
    )

    # Ensure DB tables exist for tests (especially with in-memory SQLite).
    # Import models so they're registered on Base.metadata before create_all().
    from app.db import models  # noqa: F401
    from app.db.database import init_db, Base, engine

    # Drop and recreate all tables to ensure fresh schema with timezone-aware datetimes
    Base.metadata.drop_all(bind=engine)
    init_db()


@pytest.fixture
def mock_stripe():
    """Mock Stripe API responses."""
    with patch("stripe.PaymentIntent.create") as mock_create:
        mock_create.return_value = MagicMock(
            id="pi_test_1234567890",
            status="requires_payment_method",
            amount=1000,
            currency="usd",
            client_secret="pi_test_1234567890_secret_xyz",
            charges=MagicMock(data=[]),
        )

        yield mock_create
