from pydantic import BaseModel


class AddRequest(BaseModel):
    """Request model for addition."""

    a: float
    b: float


class AddResponse(BaseModel):
    """Response model for addition."""

    result: float
    a: float
    b: float


class MultiplyRequest(BaseModel):
    """Request model for multiplication."""

    a: float
    b: float


class MultiplyResponse(BaseModel):
    """Response model for multiplication."""

    result: float
    a: float
    b: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    debug: bool


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool


# ==================== Payment Schemas ====================


class CreatePaymentIntentRequest(BaseModel):
    """Request model for creating a payment intent."""

    amount: int  # Amount in cents
    currency: str = "usd"
    description: str | None = None


class PaymentIntentResponse(BaseModel):
    """Response model for payment intent."""

    id: str  # Payment ID (UUID)
    stripe_intent_id: str | None = None
    amount: int
    currency: str
    description: str | None = None
    status: str  # pending, processing, succeeded, failed, canceled
    created_at: str


class PaymentStatusResponse(BaseModel):
    """Response model for payment status."""

    id: str
    stripe_intent_id: str | None = None
    amount: int
    currency: str
    status: str
    error_message: str | None = None
    webhook_received: bool
    created_at: str
    updated_at: str
    completed_at: str | None = None
