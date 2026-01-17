"""Test unit tests for math service."""

from app.services.math_service import MathService


class TestMathService:
    """Test suite for MathService."""

    def test_add_positive_numbers(self):
        """Test addition of positive numbers."""
        result = MathService.add(2, 3)
        assert result == 5

    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        result = MathService.add(-2, -3)
        assert result == -5

    def test_add_mixed_numbers(self):
        """Test addition with mixed positive and negative."""
        result = MathService.add(10, -5)
        assert result == 5

    def test_add_floats(self):
        """Test addition of floating point numbers."""
        result = MathService.add(1.5, 2.5)
        assert result == 4.0

    def test_multiply_positive_numbers(self):
        """Test multiplication of positive numbers."""
        result = MathService.multiply(3, 4)
        assert result == 12

    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers."""
        result = MathService.multiply(-2, -3)
        assert result == 6

    def test_multiply_mixed_numbers(self):
        """Test multiplication with mixed signs."""
        result = MathService.multiply(-2, 3)
        assert result == -6

    def test_multiply_by_zero(self):
        """Test multiplication by zero."""
        result = MathService.multiply(5, 0)
        assert result == 0

    def test_multiply_floats(self):
        """Test multiplication of floating point numbers."""
        result = MathService.multiply(2.5, 4.0)
        assert result == 10.0
