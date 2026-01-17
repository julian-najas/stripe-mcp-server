"""Payment service business logic (separated from API)."""
import uuid
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.repository import IdempotencyRepository, PaymentRepository
from app.services.stripe.client import stripe_service


def create_payment_service(
    amount: int,
    currency: str = "usd",
    description: str | None = None,
    idempotency_key: str | None = None,
    db: Session | None = None,
) -> dict:
    """
    Create a payment intent with idempotency.
    
    Returns: dict with payment details
    """
    if db is None:
        from app.db.database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        # Check if this request was already processed
        existing = IdempotencyRepository.get_request(db, idempotency_key)
        if existing:
            logger.info(f"Returning cached payment for idempotency key: {idempotency_key}")
            return existing.get_response()

        # Create payment record in DB
        payment_id = str(uuid.uuid4())
        payment = PaymentRepository.create_payment(
            db=db,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            description=description,
        )

        # Create Stripe PaymentIntent
        stripe_data = stripe_service.create_payment_intent(
            amount=amount,
            currency=currency,
            description=description or f"Payment {payment_id}",
            metadata={"payment_id": payment_id, "idempotency_key": idempotency_key},
            idempotency_key=idempotency_key,
        )

        # Link payment to Stripe intent
        PaymentRepository.update_payment_stripe_intent(
            db=db,
            payment_id=payment_id,
            stripe_intent_id=stripe_data["id"],
            status="processing",
        )

        # Prepare response
        response_data = {
            "id": payment_id,
            "stripe_intent_id": stripe_data["id"],
            "amount": amount,
            "currency": currency,
            "description": description,
            "status": "processing",
            "created_at": payment.created_at.isoformat(),
        }

        # Store for idempotency
        IdempotencyRepository.store_request(
            db=db,
            idempotency_key=idempotency_key,
            request_method="POST",
            request_path="/api/v1/payments/intent",
            request_body={"amount": amount, "currency": currency, "description": description},
            response_data=response_data,
            response_status_code=201,
        )

        logger.info(
            f"Created payment: {payment_id}, Stripe intent: {stripe_data['id']}, "
            f"amount: {amount}{currency}"
        )

        return response_data

    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        raise

    finally:
        if close_db:
            db.close()


def get_payment_status_service(payment_id: str, db: Session | None = None) -> dict:
    """
    Get payment status by ID.
    
    Returns: dict with payment details
    """
    if db is None:
        from app.db.database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        payment = PaymentRepository.get_payment_by_id(db, payment_id)

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        return {
            "id": payment.id,
            "stripe_intent_id": payment.stripe_intent_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "error_message": payment.error_message,
            "webhook_received": payment.webhook_received,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
        }

    finally:
        if close_db:
            db.close()


def list_payments_service(limit: int = 20, db: Session | None = None) -> list[dict]:
    """
    List recent payments.
    
    Returns: list of payment dicts
    """
    if db is None:
        from app.db.database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        from app.db.models import Payment

        payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(limit).all()

        return [
            {
                "id": p.id,
                "stripe_intent_id": p.stripe_intent_id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in payments
        ]

    finally:
        if close_db:
            db.close()
