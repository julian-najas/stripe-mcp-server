"""SQLAlchemy models for idempotency and payments."""
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from app.db.database import Base


class IdempotentRequest(Base):
    """Store idempotent request results to prevent duplicate processing."""

    __tablename__ = "idempotent_requests"

    # Idempotency key (UUID or similar)
    idempotency_key = Column(String(255), primary_key=True, index=True)

    # Request metadata
    request_method = Column(String(10), nullable=False)  # POST, GET, etc.
    request_path = Column(String(500), nullable=False)   # /api/v1/payments/intent
    request_hash = Column(String(64), nullable=False, index=True)  # SHA256 of body

    # Response (JSON serialized)
    response_data = Column(Text, nullable=False)  # JSON string
    response_status_code = Column(Integer, default=200)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=True)  # Optional: auto-expire after 24h

    def get_response(self):
        """Parse response data from JSON."""
        return json.loads(self.response_data)


class Payment(Base):
    """Store payment intents and their status."""

    __tablename__ = "payments"

    # Primary key
    id = Column(String(36), primary_key=True, index=True)  # UUID

    # Stripe reference
    stripe_intent_id = Column(String(255), unique=True, index=True, nullable=True)
    stripe_intent_status = Column(String(50), default="requires_payment_method")

    # Payment details
    amount = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default="usd")
    description = Column(String(500), nullable=True)

    # Idempotency tracking
    idempotency_key = Column(String(255), nullable=False, index=True)

    # Status lifecycle
    status = Column(String(50), default="pending")  # pending, processing, succeeded, failed, canceled
    error_message = Column(Text, nullable=True)

    # Webhook tracking
    webhook_received = Column(Boolean, default=False)
    webhook_received_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "stripe_intent_id": self.stripe_intent_id,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
