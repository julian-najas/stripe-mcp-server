"""Payment endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.logging import logger
from app.db.database import get_db
from app.models.schemas import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentStatusResponse,
)
from app.services.payments import (
    create_payment_service,
    get_payment_status_service,
    list_payments_service,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment intent (idempotent)",
)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    idempotency_key: str = Header(...),  # Required header
    _: str = Depends(verify_api_key),  # Auth required
    db: Session = Depends(get_db),
):
    """
    Create a payment intent with idempotency.

    Headers:
        Idempotency-Key: UUID or unique identifier for this payment

    If the same Idempotency-Key is used again, returns the cached response.
    This ensures no double charges even if the request is retried.
    """
    try:
        response = create_payment_service(
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            idempotency_key=idempotency_key,
            db=db,
        )
        return PaymentIntentResponse(**response)

    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent",
        )


@router.get(
    "/{payment_id}",
    response_model=PaymentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment status",
)
async def get_payment_status(
    payment_id: str,
    _: str = Depends(verify_api_key),  # Auth required
    db: Session = Depends(get_db),
):
    """Get the current status of a payment."""
    try:
        response = get_payment_status_service(payment_id, db=db)
        return PaymentStatusResponse(**response)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment status",
        )
