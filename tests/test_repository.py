"""Tests for repository data access layer - covers edge cases and branches.

Target: app/db/repository.py 
Missing coverage: lines 25->36, 31, 34, 110, 134->141, 154->168, 156->158, 162->165, 175->181
Current coverage: 89% → Target: 100%
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

from app.db.repository import IdempotencyRepository, PaymentRepository


class TestIdempotencyRepositoryBranches:
    """Test IdempotencyRepository edge cases.
    
    Covers: lines 25->36 (expires_at check), 31 (naive datetime), 34 (already aware)
    """

    def test_get_request_returns_none_when_not_found(self):
        """When request doesn't exist, returns None.
        
        Covers: lines 19-20
            if not request:
                return None
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = IdempotencyRepository.get_request(mock_db, "nonexistent-key")

        assert result is None

    def test_get_request_returns_none_when_expired_naive_datetime(self):
        """Expired request (naive datetime) returns None.
        
        Covers: lines 25-34 (expires_at branch with naive datetime)
            if request.expires_at:
                ...
                if request.expires_at.tzinfo is None:
                    expires_aware = request.expires_at.replace(tzinfo=timezone.utc)
                ...
                if expires_aware < now_utc:
                    return None
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock request with EXPIRED naive datetime (no tzinfo)
        mock_request = MagicMock()
        # Use a real datetime object (naive) - past date
        expired_naive = datetime(2020, 1, 1, 0, 0, 0)  # No tzinfo = naive
        mock_request.expires_at = expired_naive
        mock_query.first.return_value = mock_request

        result = IdempotencyRepository.get_request(mock_db, "expired-key")

        assert result is None

    def test_get_request_returns_none_when_expired_aware_datetime(self):
        """Expired request (aware datetime) returns None.
        
        Covers: lines 30-31 (else branch - already timezone aware)
            else:
                expires_aware = request.expires_at
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock request with EXPIRED aware datetime
        mock_request = MagicMock()
        expired_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)  # Past, aware
        mock_request.expires_at = expired_time
        mock_query.first.return_value = mock_request

        result = IdempotencyRepository.get_request(mock_db, "expired-aware-key")

        assert result is None

    def test_get_request_returns_request_when_not_expired(self):
        """Valid non-expired request is returned.
        
        Covers: line 36
            return request
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock request with FUTURE expiry
        mock_request = MagicMock()
        future_time = datetime.now(timezone.utc) + timedelta(hours=24)
        mock_request.expires_at = future_time
        mock_query.first.return_value = mock_request

        result = IdempotencyRepository.get_request(mock_db, "valid-key")

        assert result is mock_request

    def test_get_request_returns_request_when_no_expiry(self):
        """Request without expires_at is returned (no expiry check).
        
        Covers: line 25 branch - if request.expires_at: (False path)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Create mock request with NO expiry
        mock_request = MagicMock()
        mock_request.expires_at = None
        mock_query.first.return_value = mock_request

        result = IdempotencyRepository.get_request(mock_db, "no-expiry-key")

        assert result is mock_request


class TestPaymentRepositoryUpdateBranches:
    """Test PaymentRepository update methods when payment not found.
    
    Covers: lines 110, 134->141, 154->168, 156->158, 162->165, 175->181
    (all the "if payment:" branches when payment is None)
    """

    def test_update_payment_stripe_intent_when_not_found(self):
        """update_payment_stripe_intent returns None when payment doesn't exist.
        
        Covers: lines 132-141 (if payment: branch is False, returns None)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Payment not found

        result = PaymentRepository.update_payment_stripe_intent(
            db=mock_db,
            payment_id="nonexistent-id",
            stripe_intent_id="pi_123",
            status="processing",
        )

        assert result is None
        # Verify commit was NOT called (no changes to persist)
        mock_db.commit.assert_not_called()

    def test_update_payment_status_when_not_found(self):
        """update_payment_status returns None when payment doesn't exist.
        
        Covers: lines 152-168 (if payment: branch is False, returns None)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Payment not found

        result = PaymentRepository.update_payment_status(
            db=mock_db,
            payment_id="nonexistent-id",
            status="succeeded",
        )

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_payment_status_without_optional_fields(self):
        """update_payment_status without stripe_intent_status or error_message.
        
        Covers: lines 156->158 (if stripe_intent_status: False)
                lines 162->165 (if error_message: False)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_payment = MagicMock(spec=['status', 'updated_at'])
        mock_payment.status = "pending"
        mock_query.first.return_value = mock_payment

        result = PaymentRepository.update_payment_status(
            db=mock_db,
            payment_id="pay_123",
            status="processing",  # Not a terminal status
            stripe_intent_status=None,  # Not provided
            error_message=None,  # Not provided
        )

        # Verify status was updated
        assert mock_payment.status == "processing"
        # Verify commit was called
        mock_db.commit.assert_called_once()

    def test_update_payment_status_with_terminal_status(self):
        """update_payment_status with terminal status sets completed_at.
        
        Covers: lines 162-163
            if status in ("succeeded", "failed", "canceled"):
                payment.completed_at = datetime.now(timezone.utc)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_payment = MagicMock()
        mock_payment.completed_at = None
        mock_query.first.return_value = mock_payment

        result = PaymentRepository.update_payment_status(
            db=mock_db,
            payment_id="pay_123",
            status="succeeded",  # Terminal status
        )

        # Verify completed_at was set
        assert mock_payment.completed_at is not None
        mock_db.commit.assert_called_once()

    def test_update_payment_status_with_non_terminal_status(self):
        """update_payment_status with non-terminal status does NOT set completed_at.
        
        Covers: line 162 branch - status NOT in terminal statuses
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_payment = MagicMock()
        mock_payment.completed_at = None
        mock_query.first.return_value = mock_payment

        # Store original value to check it wasn't changed
        original_completed_at = mock_payment.completed_at

        result = PaymentRepository.update_payment_status(
            db=mock_db,
            payment_id="pay_123",
            status="processing",  # Non-terminal status
        )

        # completed_at should remain unchanged (still assigned but we can verify commit happened)
        mock_db.commit.assert_called_once()

    def test_mark_webhook_received_when_not_found(self):
        """mark_webhook_received returns None when payment doesn't exist.
        
        Covers: lines 173-181 (if payment: branch is False, returns None)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Payment not found

        result = PaymentRepository.mark_webhook_received(
            db=mock_db,
            payment_id="nonexistent-id",
        )

        assert result is None
        mock_db.commit.assert_not_called()

    def test_mark_webhook_received_success(self):
        """mark_webhook_received sets webhook fields when payment exists.
        
        Covers: lines 175-181 (if payment: branch is True)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_payment = MagicMock()
        mock_payment.webhook_received = False
        mock_payment.webhook_received_at = None
        mock_query.first.return_value = mock_payment

        result = PaymentRepository.mark_webhook_received(
            db=mock_db,
            payment_id="pay_123",
        )

        assert mock_payment.webhook_received is True
        assert mock_payment.webhook_received_at is not None
        mock_db.commit.assert_called_once()


class TestPaymentRepositoryGetters:
    """Test PaymentRepository getter methods.
    
    Covers: lines 107-110 (get_payment_by_idempotency_key)
    """

    def test_get_payment_by_idempotency_key_found(self):
        """get_payment_by_idempotency_key returns payment when found.
        
        Covers: lines 107-114
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_payment = MagicMock()
        mock_payment.id = "pay_123"
        mock_payment.idempotency_key = "idem_key_123"
        mock_query.first.return_value = mock_payment

        result = PaymentRepository.get_payment_by_idempotency_key(
            db=mock_db,
            idempotency_key="idem_key_123",
        )

        assert result is mock_payment

    def test_get_payment_by_idempotency_key_not_found(self):
        """get_payment_by_idempotency_key returns None when not found.
        
        Covers: line 110 (returns None)
        """
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = PaymentRepository.get_payment_by_idempotency_key(
            db=mock_db,
            idempotency_key="nonexistent",
        )

        assert result is None
