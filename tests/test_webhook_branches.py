"""Tests for Stripe webhook handler - covers remaining branches.

Target: app/api/webhooks/stripe.py lines 54-59, 92-99, 108-111
Current coverage: 79% → Target: 100%
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestWebhookPaymentFailed:
    """Test webhook for payment_intent.payment_failed event.
    
    Covers: lines 54-59 (payment_failed handling with error_message extraction)
    """

    def test_webhook_payment_failed_with_error_message(self):
        """payment_intent.payment_failed extracts error message from event.
        
        Covers: lines 75-84
            elif event_type == "payment_intent.payment_failed":
                error_message = event_data.get("last_payment_error", {}).get("message")
                PaymentRepository.update_payment_status(
                    db=db,
                    payment_id=payment.id,
                    status="failed",
                    stripe_intent_status="requires_payment_method",
                    error_message=error_message,
                )
        """
        webhook_payload = {
            "id": "evt_test_failed",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_failed_123",
                    "status": "requires_payment_method",
                    "amount": 5000,
                    "last_payment_error": {
                        "message": "Your card was declined.",
                        "code": "card_declined",
                    },
                }
            },
        }

        # Mock the webhook verification and repository
        with patch("app.api.webhooks.stripe.stripe_service") as mock_stripe:
            with patch("app.api.webhooks.stripe.PaymentRepository") as mock_repo:
                # Setup mock payment
                mock_payment = MagicMock()
                mock_payment.id = "pay_internal_123"
                mock_payment.webhook_received = False
                mock_repo.get_payment_by_stripe_intent_id.return_value = mock_payment

                # Mock webhook verification to return our event
                mock_stripe.verify_webhook_signature.return_value = webhook_payload

                response = client.post(
                    "/api/v1/webhooks/stripe",
                    content=json.dumps(webhook_payload).encode(),
                    headers={
                        "stripe-signature": "t=123,v1=test_sig",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                # Verify update_payment_status was called with error_message
                mock_repo.update_payment_status.assert_called_once()
                call_kwargs = mock_repo.update_payment_status.call_args.kwargs
                assert call_kwargs["status"] == "failed"
                assert call_kwargs["error_message"] == "Your card was declined."


class TestWebhookPaymentCanceled:
    """Test webhook for payment_intent.canceled event.
    
    Covers: lines 92-99 (canceled handling)
    """

    def test_webhook_payment_canceled(self):
        """payment_intent.canceled updates status to canceled.
        
        Covers: lines 86-93
            elif event_type == "payment_intent.canceled":
                PaymentRepository.update_payment_status(
                    db=db,
                    payment_id=payment.id,
                    status="canceled",
                    stripe_intent_status="canceled",
                )
        """
        webhook_payload = {
            "id": "evt_test_canceled",
            "type": "payment_intent.canceled",
            "data": {
                "object": {
                    "id": "pi_test_canceled_123",
                    "status": "canceled",
                    "amount": 3000,
                }
            },
        }

        with patch("app.api.webhooks.stripe.stripe_service") as mock_stripe:
            with patch("app.api.webhooks.stripe.PaymentRepository") as mock_repo:
                mock_payment = MagicMock()
                mock_payment.id = "pay_internal_456"
                mock_payment.webhook_received = False
                mock_repo.get_payment_by_stripe_intent_id.return_value = mock_payment

                mock_stripe.verify_webhook_signature.return_value = webhook_payload

                response = client.post(
                    "/api/v1/webhooks/stripe",
                    content=json.dumps(webhook_payload).encode(),
                    headers={
                        "stripe-signature": "t=123,v1=test_sig",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                mock_repo.update_payment_status.assert_called_once()
                call_kwargs = mock_repo.update_payment_status.call_args.kwargs
                assert call_kwargs["status"] == "canceled"
                assert call_kwargs["stripe_intent_status"] == "canceled"


class TestWebhookExceptionHandling:
    """Test webhook exception handling.
    
    Covers: lines 108-111 (except Exception block)
    """

    def test_webhook_exception_returns_200_with_error(self):
        """Exception during processing still returns 200 (to prevent Stripe retries).
        
        Covers: lines 101-104
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
                # Still return 200 to prevent Stripe from retrying
                return {"status": "error", "message": str(e)}
        """
        webhook_payload = {
            "id": "evt_test_error",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_error_123",
                    "status": "succeeded",
                }
            },
        }

        with patch("app.api.webhooks.stripe.stripe_service") as mock_stripe:
            with patch("app.api.webhooks.stripe.PaymentRepository") as mock_repo:
                mock_payment = MagicMock()
                mock_payment.id = "pay_error_test"
                mock_payment.webhook_received = False
                mock_repo.get_payment_by_stripe_intent_id.return_value = mock_payment

                # Make update_payment_status raise an exception
                mock_repo.update_payment_status.side_effect = RuntimeError("DB connection lost")

                mock_stripe.verify_webhook_signature.return_value = webhook_payload

                response = client.post(
                    "/api/v1/webhooks/stripe",
                    content=json.dumps(webhook_payload).encode(),
                    headers={
                        "stripe-signature": "t=123,v1=test_sig",
                        "Content-Type": "application/json",
                    },
                )

                # Should still return 200 to prevent Stripe retries
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"
                assert "DB connection lost" in data["message"]


class TestWebhookUnknownPayment:
    """Test webhook for unknown payment (not in our DB).
    
    Covers: lines 54-59 (payment not found branch)
    """

    def test_webhook_unknown_payment_returns_ok(self):
        """Webhook for unknown payment returns 200 OK (Stripe expects 2xx).
        
        Covers: lines 49-56
            if not payment:
                logger.warning(...)
                return {"status": "ok", "message": "Event received"}
        """
        webhook_payload = {
            "id": "evt_unknown",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_unknown_not_in_db",
                    "status": "succeeded",
                }
            },
        }

        with patch("app.api.webhooks.stripe.stripe_service") as mock_stripe:
            with patch("app.api.webhooks.stripe.PaymentRepository") as mock_repo:
                # Payment NOT found
                mock_repo.get_payment_by_stripe_intent_id.return_value = None

                mock_stripe.verify_webhook_signature.return_value = webhook_payload

                response = client.post(
                    "/api/v1/webhooks/stripe",
                    content=json.dumps(webhook_payload).encode(),
                    headers={
                        "stripe-signature": "t=123,v1=test_sig",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"
                assert "Event received" in data["message"]


class TestWebhookUnhandledEventType:
    """Test webhook for unhandled event types.
    
    Covers: line 92->102 (event type not in handled list)
    """

    def test_webhook_unhandled_event_type_still_marks_received(self):
        """Unhandled event type still marks webhook as received and returns ok.
        
        Covers: lines 92->102 (no matching event_type branch, goes to mark_webhook_received)
        """
        webhook_payload = {
            "id": "evt_unhandled",
            "type": "charge.refunded",  # Event type we don't handle
            "data": {
                "object": {
                    "id": "pi_test_unhandled_123",
                    "status": "succeeded",
                }
            },
        }

        with patch("app.api.webhooks.stripe.stripe_service") as mock_stripe:
            with patch("app.api.webhooks.stripe.PaymentRepository") as mock_repo:
                mock_payment = MagicMock()
                mock_payment.id = "pay_internal_unhandled"
                mock_payment.webhook_received = False
                mock_repo.get_payment_by_stripe_intent_id.return_value = mock_payment

                mock_stripe.verify_webhook_signature.return_value = webhook_payload

                response = client.post(
                    "/api/v1/webhooks/stripe",
                    content=json.dumps(webhook_payload).encode(),
                    headers={
                        "stripe-signature": "t=123,v1=test_sig",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                # update_payment_status should NOT be called (unhandled event type)
                mock_repo.update_payment_status.assert_not_called()
                # But mark_webhook_received SHOULD be called
                mock_repo.mark_webhook_received.assert_called_once_with(
                    mock_repo.mark_webhook_received.call_args.args[0],
                    mock_payment.id
                )
