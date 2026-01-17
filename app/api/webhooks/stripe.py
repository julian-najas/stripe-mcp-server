"""Stripe webhook endpoint."""
from fastapi import APIRouter, Request, status, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.database import SessionLocal
from app.db.repository import PaymentRepository
from app.services.stripe.client import stripe_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook handler",
)
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Verifies webhook signature and updates payment status accordingly.
    Idempotent by event_id.
    """
    # Get signature from header
    sig_header = request.headers.get("stripe-signature")

    # Get raw body
    body = await request.body()

    # Verify signature
    event = stripe_service.verify_webhook_signature(body, sig_header)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    logger.info(f"Received Stripe webhook: {event.get('type')}, ID: {event.get('id')}")

    # Get DB session
    db = SessionLocal()

    try:
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})
        intent_id = event_data.get("id")

        # Find payment by Stripe intent ID
        payment = PaymentRepository.get_payment_by_stripe_intent_id(db, intent_id)

        if not payment:
            logger.warning(
                f"Received webhook for unknown intent: {intent_id}, "
                f"event: {event_type}"
            )
            # Return 200 anyway (Stripe expects 2xx)
            return {"status": "ok", "message": "Event received"}

        # Skip if already processed (webhook idempotency)
        if payment.webhook_received:
            logger.info(
                f"Webhook already processed for payment {payment.id}, "
                f"returning cached response"
            )
            return {"status": "ok", "message": "Event already processed"}

        # Handle different event types
        if event_type == "payment_intent.succeeded":
            PaymentRepository.update_payment_status(
                db=db,
                payment_id=payment.id,
                status="succeeded",
                stripe_intent_status="succeeded",
            )
            logger.info(f"Payment {payment.id} succeeded (Stripe: {intent_id})")

        elif event_type == "payment_intent.payment_failed":
            error_message = event_data.get("last_payment_error", {}).get("message")
            PaymentRepository.update_payment_status(
                db=db,
                payment_id=payment.id,
                status="failed",
                stripe_intent_status="requires_payment_method",
                error_message=error_message,
            )
            logger.warning(
                f"Payment {payment.id} failed (Stripe: {intent_id}): {error_message}"
            )

        elif event_type == "payment_intent.canceled":
            PaymentRepository.update_payment_status(
                db=db,
                payment_id=payment.id,
                status="canceled",
                stripe_intent_status="canceled",
            )
            logger.info(f"Payment {payment.id} canceled (Stripe: {intent_id})")

        # Mark webhook as received
        PaymentRepository.mark_webhook_received(db, payment.id)

        logger.info(f"Webhook processed successfully for payment {payment.id}")

        return {"status": "ok", "message": "Event processed"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Still return 200 to prevent Stripe from retrying
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
