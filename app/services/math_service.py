from app.core.logging import logger


class MathService:
    """Service for mathematical operations."""

    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        logger.info(f"Addition: {a} + {b} = {result}")
        return result

    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        logger.info(f"Multiplication: {a} * {b} = {result}")
        return result
