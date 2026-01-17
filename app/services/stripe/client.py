"""Stripe client and payment operations."""
import stripe
from typing import Optional

from app.core.settings import settings
from app.core.logging import logger


class StripeService:
    """Handle Stripe API operations."""

    def __init__(self):
        """Initialize Stripe client with API key."""
        stripe.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.use_real_stripe = settings.USE_STRIPE_REAL
        
        if self.use_real_stripe:
            logger.info("Using REAL Stripe API")
        else:
            logger.info("Using MOCKED Stripe API (tests/dev mode)")

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        description: str | None = None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Create a Stripe PaymentIntent.

        Args:
            amount: Amount in cents
            currency: Currency code (e.g., 'usd')
            description: Payment description
            metadata: Custom metadata to attach
            idempotency_key: Idempotency key for request (handled by Stripe client)

        Returns:
            PaymentIntent dict
        """
        try:
            params = {
                "amount": amount,
                "currency": currency,
                "payment_method_types": ["card"],
            }

            if description:
                params["description"] = description

            if metadata:
                params["metadata"] = metadata

            # Use idempotency key if provided (Stripe handles this)
            request_options = {}
            if idempotency_key:
                request_options["idempotency_key"] = idempotency_key

            intent = stripe.PaymentIntent.create(**params, **request_options)

            logger.info(
                f"Created Stripe PaymentIntent: {intent.id}, "
                f"amount={amount}, status={intent.status}"
            )

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "client_secret": intent.client_secret,
            }

        except stripe.error.CardError as e:
            # Card error (declined, insufficient funds, etc.)
            logger.error(f"Stripe card error: {str(e)}")
            raise
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Stripe invalid request: {str(e)}")
            raise
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe API failed
            logger.error(f"Stripe authentication error: {str(e)}")
            raise
        except stripe.error.APIConnectionError as e:
            # Network error
            logger.error(f"Stripe API connection error: {str(e)}")
            raise
        except stripe.error.StripeError as e:
            # Generic Stripe error
            logger.error(f"Stripe error creating PaymentIntent: {str(e)}")
            raise
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error creating PaymentIntent: {str(e)}")
            raise

    def get_payment_intent(self, intent_id: str) -> dict:
        """Get PaymentIntent details."""
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "charges": {
                    "data": [
                        {
                            "id": charge.id,
                            "status": charge.status,
                            "amount": charge.amount,
                        }
                        for charge in intent.charges.data
                    ]
                },
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving PaymentIntent: {str(e)}")
            raise

    def verify_webhook_signature(
        self, payload: bytes, sig_header: str | None
    ) -> Optional[dict]:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body
            sig_header: Stripe signature header

        Returns:
            Event dict if valid, None otherwise
        """
        if not sig_header:
            logger.warning("Webhook called without signature header")
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            return None

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            return None


# Singleton instance
stripe_service = StripeService()
