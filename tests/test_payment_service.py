"""Tests for payment service business logic - covers all branches.

Target: app/services/payments.py lines 23-25, 32, 103, 113-115, 140, 149-176
Current coverage: 63% → Target: 100%
"""
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.payments import (
    create_payment_service,
    get_payment_status_service,
    list_payments_service,
)


class TestCreatePaymentServiceBranches:
    """Test create_payment_service branches not covered by E2E tests.

    Covers: lines 23-25, 32 (db=None local session), line 103 (exception handling)
    """

    def test_creates_local_db_session_when_none_provided(self):
        """When db=None, service creates and closes its own session.

        Covers: lines 23-26
            if db is None:
                from app.db.database import SessionLocal
                db = SessionLocal()
                close_db = True

        And lines 97-98 (finally block):
            finally:
                if close_db:
                    db.close()
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.created_at = datetime.now(UTC)

        with patch("app.db.database.SessionLocal", return_value=mock_session) as mock_session_local:
            with patch("app.services.payments.IdempotencyRepository") as mock_idem_repo:
                with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
                    with patch("app.services.payments.stripe_service") as mock_stripe:
                        # Setup mocks
                        mock_idem_repo.get_request.return_value = None
                        mock_pay_repo.create_payment.return_value = mock_payment
                        mock_stripe.create_payment_intent.return_value = {
                            "id": "pi_test_123",
                            "status": "requires_payment_method",
                        }

                        # Call with db=None
                        create_payment_service(
                            amount=1000,
                            currency="usd",
                            description="Test",
                            idempotency_key="test-key-123",
                            db=None,  # Force local session creation
                        )

                        # Verify SessionLocal was called
                        mock_session_local.assert_called_once()
                        # Verify session was closed
                        mock_session.close.assert_called_once()

    def test_does_not_close_db_when_provided(self):
        """When db is provided, service does NOT close it.

        Covers: lines 27-28
            else:
                close_db = False
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.created_at = datetime.now(UTC)

        with patch("app.services.payments.IdempotencyRepository") as mock_idem_repo:
            with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
                with patch("app.services.payments.stripe_service") as mock_stripe:
                    # Setup mocks
                    mock_idem_repo.get_request.return_value = None
                    mock_pay_repo.create_payment.return_value = mock_payment
                    mock_stripe.create_payment_intent.return_value = {
                        "id": "pi_test_123",
                        "status": "requires_payment_method",
                    }

                    # Call with provided db session
                    create_payment_service(
                        amount=1000,
                        currency="usd",
                        description="Test",
                        idempotency_key="test-key-456",
                        db=mock_session,  # Provided session
                    )

                    # Verify session was NOT closed (caller's responsibility)
                    mock_session.close.assert_not_called()

    def test_generates_idempotency_key_when_not_provided(self):
        """When idempotency_key is None, service generates UUID.

        Covers: lines 31-32
            if not idempotency_key:
                idempotency_key = str(uuid.uuid4())
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.created_at = datetime.now(UTC)

        with patch("app.services.payments.IdempotencyRepository") as mock_idem_repo:
            with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
                with patch("app.services.payments.stripe_service") as mock_stripe:
                    # Setup mocks
                    mock_idem_repo.get_request.return_value = None
                    mock_pay_repo.create_payment.return_value = mock_payment
                    mock_stripe.create_payment_intent.return_value = {
                        "id": "pi_test_123",
                        "status": "requires_payment_method",
                    }

                    # Call without idempotency_key
                    create_payment_service(
                        amount=1000,
                        currency="usd",
                        db=mock_session,
                        idempotency_key=None,  # Not provided
                    )

                    # Verify a UUID was generated and used
                    call_args = mock_pay_repo.create_payment.call_args
                    used_key = call_args.kwargs.get("idempotency_key")
                    assert used_key is not None
                    assert len(used_key) == 36  # UUID format

    def test_exception_is_logged_and_reraised(self):
        """Exceptions are logged and re-raised.

        Covers: lines 92-94
            except Exception as e:
                logger.error(f"Error creating payment: {str(e)}")
                raise
        """
        mock_session = MagicMock()

        with patch("app.services.payments.IdempotencyRepository") as mock_idem_repo:
            with patch("app.services.payments.logger") as mock_logger:
                # Setup mock to raise exception
                mock_idem_repo.get_request.side_effect = RuntimeError("DB connection failed")

                with pytest.raises(RuntimeError) as exc_info:
                    create_payment_service(
                        amount=1000,
                        currency="usd",
                        idempotency_key="test-key",
                        db=mock_session,
                    )

                assert "DB connection failed" in str(exc_info.value)
                # Verify error was logged
                mock_logger.error.assert_called()


class TestGetPaymentStatusServiceBranches:
    """Test get_payment_status_service branches.

    Covers: lines 113-115, 140 (db=None local session)
    """

    def test_creates_local_db_session_when_none_provided(self):
        """When db=None, service creates and closes its own session.

        Covers: lines 113-116
            if db is None:
                from app.db.database import SessionLocal
                db = SessionLocal()
                close_db = True

        And lines 138-139 (finally block):
            finally:
                if close_db:
                    db.close()
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.id = "pay_123"
        mock_payment.stripe_intent_id = "pi_123"
        mock_payment.amount = 2000
        mock_payment.currency = "usd"
        mock_payment.status = "succeeded"
        mock_payment.error_message = None
        mock_payment.webhook_received = True
        mock_payment.created_at = datetime.now(UTC)
        mock_payment.updated_at = datetime.now(UTC)
        mock_payment.completed_at = datetime.now(UTC)

        with patch("app.db.database.SessionLocal", return_value=mock_session) as mock_session_local:
            with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
                mock_pay_repo.get_payment_by_id.return_value = mock_payment

                # Call with db=None
                result = get_payment_status_service(
                    payment_id="pay_123",
                    db=None,  # Force local session creation
                )

                # Verify SessionLocal was called
                mock_session_local.assert_called_once()
                # Verify session was closed
                mock_session.close.assert_called_once()
                # Verify result
                assert result["id"] == "pay_123"

    def test_does_not_close_db_when_provided(self):
        """When db is provided, service does NOT close it.

        Covers: lines 117-118
            else:
                close_db = False
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.id = "pay_456"
        mock_payment.stripe_intent_id = "pi_456"
        mock_payment.amount = 3000
        mock_payment.currency = "eur"
        mock_payment.status = "processing"
        mock_payment.error_message = None
        mock_payment.webhook_received = False
        mock_payment.created_at = datetime.now(UTC)
        mock_payment.updated_at = datetime.now(UTC)
        mock_payment.completed_at = None

        with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
            mock_pay_repo.get_payment_by_id.return_value = mock_payment

            # Call with provided db session
            get_payment_status_service(
                payment_id="pay_456",
                db=mock_session,  # Provided session
            )

            # Verify session was NOT closed
            mock_session.close.assert_not_called()

    def test_payment_with_no_completed_at(self):
        """Payment without completed_at returns None for that field.

        Covers: line 133
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
        """
        mock_session = MagicMock()
        mock_payment = MagicMock()
        mock_payment.id = "pay_789"
        mock_payment.stripe_intent_id = "pi_789"
        mock_payment.amount = 1000
        mock_payment.currency = "usd"
        mock_payment.status = "processing"
        mock_payment.error_message = None
        mock_payment.webhook_received = False
        mock_payment.created_at = datetime.now(UTC)
        mock_payment.updated_at = datetime.now(UTC)
        mock_payment.completed_at = None  # Not completed yet

        with patch("app.services.payments.PaymentRepository") as mock_pay_repo:
            mock_pay_repo.get_payment_by_id.return_value = mock_payment

            result = get_payment_status_service(
                payment_id="pay_789",
                db=mock_session,
            )

            assert result["completed_at"] is None


class TestListPaymentsService:
    """Test list_payments_service - completely uncovered function.

    Covers: lines 149-176 (entire function)
    """

    def test_list_payments_with_local_session(self):
        """When db=None, creates local session.

        Covers: lines 158-161
            if db is None:
                from app.db.database import SessionLocal
                db = SessionLocal()
                close_db = True
        """
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch("app.db.database.SessionLocal", return_value=mock_session) as mock_session_local:
            result = list_payments_service(limit=10, db=None)

            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()
            assert result == []

    def test_list_payments_with_provided_session(self):
        """When db is provided, does not close it.

        Covers: lines 162-163
            else:
                close_db = False
        """
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        list_payments_service(limit=10, db=mock_session)

        mock_session.close.assert_not_called()

    def test_list_payments_returns_formatted_list(self):
        """Returns list of payment dicts with correct fields.

        Covers: lines 168-178 (query and list comprehension)
        """
        mock_session = MagicMock()

        # Create mock payments
        mock_payment_1 = MagicMock()
        mock_payment_1.id = "pay_001"
        mock_payment_1.stripe_intent_id = "pi_001"
        mock_payment_1.amount = 1000
        mock_payment_1.currency = "usd"
        mock_payment_1.status = "succeeded"
        mock_payment_1.created_at = datetime(2026, 1, 19, 10, 0, 0, tzinfo=UTC)
        mock_payment_1.updated_at = datetime(2026, 1, 19, 10, 5, 0, tzinfo=UTC)

        mock_payment_2 = MagicMock()
        mock_payment_2.id = "pay_002"
        mock_payment_2.stripe_intent_id = "pi_002"
        mock_payment_2.amount = 2500
        mock_payment_2.currency = "eur"
        mock_payment_2.status = "processing"
        mock_payment_2.created_at = datetime(2026, 1, 19, 11, 0, 0, tzinfo=UTC)
        mock_payment_2.updated_at = datetime(2026, 1, 19, 11, 0, 0, tzinfo=UTC)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_payment_1, mock_payment_2]

        result = list_payments_service(limit=20, db=mock_session)

        assert len(result) == 2

        # Check first payment
        assert result[0]["id"] == "pay_001"
        assert result[0]["stripe_intent_id"] == "pi_001"
        assert result[0]["amount"] == 1000
        assert result[0]["currency"] == "usd"
        assert result[0]["status"] == "succeeded"
        assert "created_at" in result[0]
        assert "updated_at" in result[0]

        # Check second payment
        assert result[1]["id"] == "pay_002"
        assert result[1]["amount"] == 2500
        assert result[1]["currency"] == "eur"

    def test_list_payments_empty_result(self):
        """Returns empty list when no payments exist.

        Covers: lines 168-178 (empty query result)
        """
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = list_payments_service(limit=20, db=mock_session)

        assert result == []
        assert isinstance(result, list)

    def test_list_payments_respects_limit(self):
        """Limit parameter is passed to query.

        Covers: line 168
            payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(limit).all()
        """
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        list_payments_service(limit=5, db=mock_session)

        # Verify limit was called with correct value
        mock_query.limit.assert_called_once_with(5)
