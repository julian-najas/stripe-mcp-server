"""End-to-end test: PaymentIntent creation + webhook simulation."""
import uuid
import json
import hmac
import hashlib
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.db.repository import PaymentRepository
from app.core.settings import settings


client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}


def generate_stripe_signature(payload: bytes, secret: str) -> str:
    """Generate Stripe webhook signature for testing."""
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def mock_stripe_intent(**kwargs):
    """Create mock Stripe PaymentIntent."""
    return MagicMock(
        id=f"pi_test_{str(uuid.uuid4())[:8]}",
        status=kwargs.get("status", "requires_payment_method"),
        amount=kwargs.get("amount", 1000),
        currency=kwargs.get("currency", "usd"),
        client_secret=f"pi_test_{str(uuid.uuid4())[:8]}_secret_xyz",
        charges=MagicMock(data=[]),
    )


class TestStripeEndToEnd:
    """End-to-end tests for Stripe PaymentIntent + Webhook flow."""

    @patch("stripe.PaymentIntent.create")
    def test_complete_payment_flow(self, mock_create):
        """Test full flow: create payment → receive webhook → verify status."""
        # Step 1: Create payment
        mock_create.return_value = mock_stripe_intent(amount=5000, currency="usd")
        
        idempotency_key = str(uuid.uuid4())
        payload = {
            "amount": 5000,
            "currency": "usd",
            "description": "E2E test payment",
        }

        response = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 201
        payment_data = response.json()
        payment_id = payment_data["id"]
        stripe_intent_id = payment_data["stripe_intent_id"]

        assert payment_data["status"] == "processing"
        assert payment_data["amount"] == 5000
        assert stripe_intent_id.startswith("pi_test_")

        # Step 2: Simulate webhook (payment succeeded)
        webhook_payload = {
            "id": f"evt_{uuid.uuid4()}",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": stripe_intent_id,
                    "status": "succeeded",
                    "amount": 5000,
                    "currency": "usd",
                }
            },
        }

        payload_bytes = json.dumps(webhook_payload).encode()
        signature = generate_stripe_signature(payload_bytes, settings.STRIPE_WEBHOOK_SECRET)

        # Mock webhook verification
        with patch("stripe.Webhook.construct_event") as mock_verify:
            mock_verify.return_value = webhook_payload

            webhook_response = client.post(
                "/api/v1/webhooks/stripe",
                content=payload_bytes,
                headers={"stripe-signature": signature, "Content-Type": "application/json"},
            )

            assert webhook_response.status_code == 200

        # Step 3: Verify payment status updated
        status_response = client.get(f"/api/v1/payments/{payment_id}", headers=HEADERS)

        assert status_response.status_code == 200
        final_status = status_response.json()

        assert final_status["status"] == "succeeded"
        assert final_status["webhook_received"] is True
        assert final_status["completed_at"] is not None

    @patch("stripe.PaymentIntent.create")
    def test_payment_failed_webhook(self, mock_create):
        """Test webhook handling for failed payment."""
        mock_create.return_value = mock_stripe_intent()

        # Create payment
        idempotency_key = str(uuid.uuid4())
        response = client.post(
            "/api/v1/payments/intent",
            json={"amount": 1000, "currency": "usd", "description": "Will fail"},
            headers={**HEADERS, "Idempotency-Key": idempotency_key},
        )

        assert response.status_code == 201
        payment_id = response.json()["id"]
        stripe_intent_id = response.json()["stripe_intent_id"]

        # Simulate payment_failed webhook
        webhook_payload = {
            "id": f"evt_{uuid.uuid4()}",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": stripe_intent_id,
                    "status": "requires_payment_method",
                    "last_payment_error": {
                        "message": "Card declined"
                    },
                }
            },
        }

        payload_bytes = json.dumps(webhook_payload).encode()
        signature = generate_stripe_signature(payload_bytes, settings.STRIPE_WEBHOOK_SECRET)

        with patch("stripe.Webhook.construct_event") as mock_verify:
            mock_verify.return_value = webhook_payload

            webhook_response = client.post(
                "/api/v1/webhooks/stripe",
                content=payload_bytes,
                headers={"stripe-signature": signature},
            )

            assert webhook_response.status_code == 200

        # Verify status
        status_response = client.get(f"/api/v1/payments/{payment_id}", headers=HEADERS)
        status_data = status_response.json()

        assert status_data["status"] == "failed"
        assert status_data["error_message"] == "Card declined"

    def test_webhook_invalid_signature(self):
        """Test that invalid webhook signature is rejected."""
        webhook_payload = {
            "id": f"evt_{uuid.uuid4()}",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_fake"}},
        }

        payload_bytes = json.dumps(webhook_payload).encode()

        # Use WRONG signature
        with patch("stripe.Webhook.construct_event") as mock_verify:
            # Simulate signature verification failure
            mock_verify.return_value = None

            response = client.post(
                "/api/v1/webhooks/stripe",
                content=payload_bytes,
                headers={"stripe-signature": "invalid_signature"},
            )

            # Should reject with 401
            assert response.status_code == 401
            assert "Invalid" in response.json()["detail"]

    @patch("stripe.PaymentIntent.create")
    def test_duplicate_webhook_is_idempotent(self, mock_create):
        """Test that duplicate webhook is handled gracefully."""
        mock_create.return_value = mock_stripe_intent()

        # Create payment
        idempotency_key = str(uuid.uuid4())
        response = client.post(
            "/api/v1/payments/intent",
            json={"amount": 2000, "currency": "eur"},
            headers={**HEADERS, "Idempotency-Key": idempotency_key},
        )

        payment_id = response.json()["id"]
        stripe_intent_id = response.json()["stripe_intent_id"]

        # Send webhook TWICE with same event
        webhook_payload = {
            "id": f"evt_{uuid.uuid4()}",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": stripe_intent_id,
                    "status": "succeeded",
                }
            },
        }

        payload_bytes = json.dumps(webhook_payload).encode()
        signature = generate_stripe_signature(payload_bytes, settings.STRIPE_WEBHOOK_SECRET)

        with patch("stripe.Webhook.construct_event") as mock_verify:
            mock_verify.return_value = webhook_payload

            # First webhook
            response1 = client.post(
                "/api/v1/webhooks/stripe",
                content=payload_bytes,
                headers={"stripe-signature": signature},
            )
            assert response1.status_code == 200

            # Second webhook (duplicate)
            response2 = client.post(
                "/api/v1/webhooks/stripe",
                content=payload_bytes,
                headers={"stripe-signature": signature},
            )
            assert response2.status_code == 200
            assert "already processed" in response2.json()["message"].lower()

    @patch("stripe.PaymentIntent.create")
    def test_idempotency_returns_same_payment(self, mock_create):
        """Test that same idempotency key returns cached response."""
        mock_create.return_value = mock_stripe_intent()

        idempotency_key = str(uuid.uuid4())
        payload = {"amount": 3000, "currency": "gbp", "description": "Same key test"}

        # First request
        response1 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": idempotency_key},
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Second request with SAME idempotency key
        response2 = client.post(
            "/api/v1/payments/intent",
            json=payload,
            headers={**HEADERS, "Idempotency-Key": idempotency_key},
        )
        assert response2.status_code == 201
        data2 = response2.json()

        # Should return identical data
        assert data1["id"] == data2["id"]
        assert data1["stripe_intent_id"] == data2["stripe_intent_id"]
        assert data1["status"] == data2["status"]

        # Verify Stripe API was only called ONCE
        assert mock_create.call_count == 1
