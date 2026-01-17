"""Data access layer for idempotency and payments."""
import json
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.models import IdempotentRequest, Payment


class IdempotencyRepository:
    """Handle idempotent request storage and retrieval."""

    @staticmethod
    def get_request(db: Session, idempotency_key: str) -> IdempotentRequest | None:
        """Get stored idempotent request if it exists and is still valid."""
        request = db.query(IdempotentRequest).filter(
            IdempotentRequest.idempotency_key == idempotency_key
        ).first()

        if not request:
            return None

        # Check if expired
        # Note: SQLite doesn't store timezone info, so expires_at is naive UTC
        # We need to make it aware or compare with naive UTC
        if request.expires_at:
            now_utc = datetime.now(timezone.utc)
            # Make expires_at timezone-aware if it's naive (from DB)
            if request.expires_at.tzinfo is None:
                expires_aware = request.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_aware = request.expires_at
            
            if expires_aware < now_utc:
                return None

        return request

    @staticmethod
    def store_request(
        db: Session,
        idempotency_key: str,
        request_method: str,
        request_path: str,
        request_body: dict,
        response_data: dict,
        response_status_code: int = 200,
        ttl_hours: int = 24,
    ) -> IdempotentRequest:
        """Store idempotent request result."""
        # Calculate hash of request to detect accidental key reuse with different data
        request_hash = hashlib.sha256(
            json.dumps(request_body, sort_keys=True).encode()
        ).hexdigest()

        request = IdempotentRequest(
            idempotency_key=idempotency_key,
            request_method=request_method,
            request_path=request_path,
            request_hash=request_hash,
            response_data=json.dumps(response_data),
            response_status_code=response_status_code,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        )

        db.add(request)
        db.commit()
        db.refresh(request)

        return request


class PaymentRepository:
    """Handle payment storage and retrieval."""

    @staticmethod
    def create_payment(
        db: Session,
        payment_id: str,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str | None = None,
    ) -> Payment:
        """Create a new payment record."""
        payment = Payment(
            id=payment_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            description=description,
            status="pending",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: str) -> Payment | None:
        """Get payment by ID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_payment_by_idempotency_key(
        db: Session, idempotency_key: str
    ) -> Payment | None:
        """Get payment by idempotency key (useful for duplicate detection)."""
        return (
            db.query(Payment)
            .filter(Payment.idempotency_key == idempotency_key)
            .first()
        )

    @staticmethod
    def get_payment_by_stripe_intent_id(
        db: Session, stripe_intent_id: str
    ) -> Payment | None:
        """Get payment by Stripe intent ID."""
        return (
            db.query(Payment)
            .filter(Payment.stripe_intent_id == stripe_intent_id)
            .first()
        )

    @staticmethod
    def update_payment_stripe_intent(
        db: Session, payment_id: str, stripe_intent_id: str, status: str = "processing"
    ) -> Payment:
        """Link payment to Stripe intent and update status."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if payment:
            payment.stripe_intent_id = stripe_intent_id
            payment.status = status
            payment.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(payment)

        return payment

    @staticmethod
    def update_payment_status(
        db: Session,
        payment_id: str,
        status: str,
        stripe_intent_status: str | None = None,
        error_message: str | None = None,
    ) -> Payment:
        """Update payment status (usually from webhook)."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if payment:
            payment.status = status
            if stripe_intent_status:
                payment.stripe_intent_status = stripe_intent_status
            if error_message:
                payment.error_message = error_message
            payment.updated_at = datetime.now(timezone.utc)

            if status in ("succeeded", "failed", "canceled"):
                payment.completed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(payment)

        return payment

    @staticmethod
    def mark_webhook_received(db: Session, payment_id: str) -> Payment:
        """Mark that webhook was processed."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if payment:
            payment.webhook_received = True
            payment.webhook_received_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(payment)

        return payment
