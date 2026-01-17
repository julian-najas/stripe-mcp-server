from fastapi import APIRouter, Depends, status

from app.core.auth import verify_api_key
from app.models.schemas import AddRequest, AddResponse, MultiplyRequest, MultiplyResponse
from app.services.math_service import MathService

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post(
    "/add", response_model=AddResponse, status_code=status.HTTP_200_OK, summary="Add two numbers"
)
async def add_numbers(request: AddRequest, _: str = Depends(verify_api_key)):
    """
    Add two numbers. Requires X-API-Key header.
    """
    result = MathService.add(request.a, request.b)
    return AddResponse(result=result, a=request.a, b=request.b)


@router.post(
    "/multiply",
    response_model=MultiplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Multiply two numbers",
)
async def multiply_numbers(request: MultiplyRequest, _: str = Depends(verify_api_key)):
    """
    Multiply two numbers. Requires X-API-Key header.
    """
    result = MathService.multiply(request.a, request.b)
    return MultiplyResponse(result=result, a=request.a, b=request.b)


@router.get(
    "/say-hi",
    status_code=status.HTTP_200_OK,
    summary="Greet a user",
)
async def say_hi(name: str = "World"):
    """
    Greet a user by name. No authentication required.
    """
    return {"message": f"¡Hola {name}! Bienvenido a Stripe Idempotent Payments Demo."}
