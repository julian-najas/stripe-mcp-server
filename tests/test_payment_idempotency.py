"""Tests for payment idempotency."""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.db.repository import PaymentRepository


client = TestClient(app)

# Use fake API key for tests (DEBUG mode)
HEADERS = {"X-API-Key": "test-key"}
IDEMPOTENCY_KEY_1 = str(uuid.uuid4())
IDEMPOTENCY_KEY_2 = str(uuid.uuid4())


def mock_stripe_intent(**kwargs):
    """Create mock Stripe intent with unique ID."""
    import uuid
    return MagicMock(
        id=f"pi_test_{str(uuid.uuid4())[:8]}",
        status="requires_payment_method",
        amount=kwargs.get("amount", 1000),
        currency=kwargs.get("currency", "usd"),
        client_secret=f"pi_test_{str(uuid.uuid4())[:8]}_secret_xyz",
        charges=MagicMock(data=[]),
    )


class TestPaymentIdempotency:
    """Test idempotent payment intent creation."""

    @patch("stripe.PaymentIntent.create")
    def test_same_idempotency_key_returns_same_response(self, mock_create):
        """Calling with same idempotency key should return cached response."""
        mock_create.return_value = mock_stripe_intent()

        payload = {
            "amount": 1000,
            "currency": "usd",
            "description": "Test payment",
        }

        # First request
        response1 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": IDEMPOTENCY_KEY_1},
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Second request with same key
        response2 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": IDEMPOTENCY_KEY_1},
        )
        assert response2.status_code == 201
        data2 = response2.json()

        # Should return identical response
        assert data1["id"] == data2["id"], "Payment IDs should be the same"
        assert data1["stripe_intent_id"] == data2["stripe_intent_id"]
        assert data1["status"] == data2["status"]

    @patch("stripe.PaymentIntent.create")
    def test_different_idempotency_key_creates_different_payment(self, mock_create):
        """Different idempotency keys should create different payments."""
        mock_create.return_value = mock_stripe_intent()

        payload = {
            "amount": 1000,
            "currency": "usd",
            "description": "Test payment",
        }

        # First request
        response1 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": IDEMPOTENCY_KEY_1},
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Second request with different key
        response2 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": IDEMPOTENCY_KEY_2},
        )
        assert response2.status_code == 201
        data2 = response2.json()

        # Should create different payments
        assert data1["id"] != data2["id"], "Different keys should create different payments"

    def test_missing_idempotency_key_returns_error(self):
        """Missing idempotency key should return error."""
        payload = {
            "amount": 1000,
            "currency": "usd",
            "description": "Test payment",
        }

        response = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers=HEADERS,
        )
        assert response.status_code == 422  # Validation error

    @patch("stripe.PaymentIntent.create")
    def test_payment_in_database(self, mock_create):
        """Created payment should be stored in database."""
        mock_create.return_value = mock_stripe_intent(amount=2000, currency="eur")
        db = SessionLocal()
        key = str(uuid.uuid4())

        try:
            payload = {
                "amount": 2000,
                "currency": "eur",
                "description": "DB test",
            }

            response = client.post(
                "/api/v1/payments/intent",
                json=payload,
                headers={**HEADERS, "Idempotency-Key": key},
            )
            assert response.status_code == 201
            payment_id = response.json()["id"]

            # Verify in DB
            payment = PaymentRepository.get_payment_by_id(db, payment_id)
            assert payment is not None
            assert payment.idempotency_key == key
            assert payment.amount == 2000
            assert payment.currency == "eur"
            assert payment.status == "processing"

        finally:
            db.close()

    @patch("stripe.PaymentIntent.create")
    def test_get_payment_status(self, mock_create):
        """Can retrieve payment status by ID."""
        mock_create.return_value = mock_stripe_intent(amount=3000, currency="gbp")
        db = SessionLocal()
        key = str(uuid.uuid4())

        try:
            payload = {
                "amount": 3000,
                "currency": "gbp",
                "description": "Status test",
            }

            # Create payment
            response = client.post(
                "/api/v1/payments/intent",
                json=payload,
                headers={**HEADERS, "Idempotency-Key": key},
            )
            assert response.status_code == 201
            payment_id = response.json()["id"]

            # Get status
            status_response = client.get(
                f"/api/v1/payments/{payment_id}",
                headers=HEADERS,
            )
            assert status_response.status_code == 200
            status_data = status_response.json()

            assert status_data["id"] == payment_id
            assert status_data["amount"] == 3000
            assert status_data["currency"] == "gbp"
            assert status_data["status"] == "processing"

        finally:
            db.close()

    def test_nonexistent_payment_returns_404(self):
        """Requesting non-existent payment returns 404."""
        response = client.get(
            "/api/v1/payments/nonexistent-id",
            headers=HEADERS,
        )
        assert response.status_code == 404
