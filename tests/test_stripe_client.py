"""Tests for Stripe client service - covers error handling and all methods.

Target: app/services/stripe/client.py lines 79-126, 142-157
Current coverage: 55% → Target: 100%
"""
import pytest
from unittest.mock import patch, MagicMock
import stripe

from app.services.stripe.client import StripeService


class TestStripeServiceInit:
    """Test StripeService initialization branches.
    
    Covers: lines 17-19 (USE_STRIPE_REAL logging)
    """

    def test_init_real_stripe_mode(self):
        """Test initialization with real Stripe API.
        
        Covers: line 19 - logger.info("Using REAL Stripe API")
        """
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_live_real_key"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_real"
        mock_settings.USE_STRIPE_REAL = True

        with patch("app.services.stripe.client.settings", mock_settings):
            with patch("app.services.stripe.client.logger") as mock_logger:
                service = StripeService()
                mock_logger.info.assert_called_with("Using REAL Stripe API")
                assert service.use_real_stripe is True

    def test_init_mock_stripe_mode(self):
        """Test initialization with mocked Stripe API.
        
        Covers: line 21 - logger.info("Using MOCKED Stripe API...")
        """
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_test_fake"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.USE_STRIPE_REAL = False

        with patch("app.services.stripe.client.settings", mock_settings):
            with patch("app.services.stripe.client.logger") as mock_logger:
                service = StripeService()
                mock_logger.info.assert_called_with("Using MOCKED Stripe API (tests/dev mode)")
                assert service.use_real_stripe is False


class TestCreatePaymentIntentErrors:
    """Test create_payment_intent error handling branches.
    
    Covers: lines 79-100 (all Stripe exception types)
    """

    @pytest.fixture
    def stripe_service(self):
        """Create StripeService with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_test_fake"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.USE_STRIPE_REAL = False

        with patch("app.services.stripe.client.settings", mock_settings):
            return StripeService()

    def test_card_error_is_raised(self, stripe_service):
        """CardError (declined, insufficient funds) should be re-raised.
        
        Covers: lines 79-81
            except stripe.error.CardError as e:
                logger.error(f"Stripe card error: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                message="Card declined",
                param="card_number",
                code="card_declined",
            )

            with pytest.raises(stripe.error.CardError) as exc_info:
                stripe_service.create_payment_intent(amount=1000, currency="usd")

            assert "Card declined" in str(exc_info.value)

    def test_invalid_request_error_is_raised(self, stripe_service):
        """InvalidRequestError (bad params) should be re-raised.
        
        Covers: lines 83-85
            except stripe.error.InvalidRequestError as e:
                logger.error(f"Stripe invalid request: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = stripe.error.InvalidRequestError(
                message="Invalid amount",
                param="amount",
            )

            with pytest.raises(stripe.error.InvalidRequestError) as exc_info:
                stripe_service.create_payment_intent(amount=-100, currency="usd")

            assert "Invalid amount" in str(exc_info.value)

    def test_authentication_error_is_raised(self, stripe_service):
        """AuthenticationError (bad API key) should be re-raised.
        
        Covers: lines 87-89
            except stripe.error.AuthenticationError as e:
                logger.error(f"Stripe authentication error: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = stripe.error.AuthenticationError(
                message="Invalid API Key provided",
            )

            with pytest.raises(stripe.error.AuthenticationError) as exc_info:
                stripe_service.create_payment_intent(amount=1000, currency="usd")

            assert "Invalid API Key" in str(exc_info.value)

    def test_api_connection_error_is_raised(self, stripe_service):
        """APIConnectionError (network issues) should be re-raised.
        
        Covers: lines 91-93
            except stripe.error.APIConnectionError as e:
                logger.error(f"Stripe API connection error: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = stripe.error.APIConnectionError(
                message="Network unreachable",
            )

            with pytest.raises(stripe.error.APIConnectionError) as exc_info:
                stripe_service.create_payment_intent(amount=1000, currency="usd")

            assert "Network unreachable" in str(exc_info.value)

    def test_generic_stripe_error_is_raised(self, stripe_service):
        """Generic StripeError should be re-raised.
        
        Covers: lines 95-97
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating PaymentIntent: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = stripe.error.StripeError(
                message="Unknown Stripe error",
            )

            with pytest.raises(stripe.error.StripeError) as exc_info:
                stripe_service.create_payment_intent(amount=1000, currency="usd")

            assert "Unknown Stripe error" in str(exc_info.value)

    def test_unexpected_exception_is_raised(self, stripe_service):
        """Unexpected exceptions should be re-raised.
        
        Covers: lines 99-101
            except Exception as e:
                logger.error(f"Unexpected error creating PaymentIntent: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected failure")

            with pytest.raises(RuntimeError) as exc_info:
                stripe_service.create_payment_intent(amount=1000, currency="usd")

            assert "Unexpected failure" in str(exc_info.value)


class TestCreatePaymentIntentBranches:
    """Test create_payment_intent optional parameter branches.
    
    Covers: lines 51-62 (description and metadata conditionals)
    """

    @pytest.fixture
    def stripe_service(self):
        """Create StripeService with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_test_fake"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.USE_STRIPE_REAL = False

        with patch("app.services.stripe.client.settings", mock_settings):
            return StripeService()

    def test_without_description(self, stripe_service):
        """Create payment without description.
        
        Covers: line 54 branch - if description: (False path)
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.return_value = MagicMock(
                id="pi_test_123",
                status="requires_payment_method",
                amount=1000,
                currency="usd",
                client_secret="secret_123",
            )

            result = stripe_service.create_payment_intent(
                amount=1000,
                currency="usd",
                description=None,  # No description
            )

            # Verify description was NOT in params
            call_kwargs = mock_create.call_args[1]
            assert "description" not in call_kwargs

    def test_without_metadata(self, stripe_service):
        """Create payment without metadata.
        
        Covers: line 58 branch - if metadata: (False path)
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.return_value = MagicMock(
                id="pi_test_123",
                status="requires_payment_method",
                amount=1000,
                currency="usd",
                client_secret="secret_123",
            )

            result = stripe_service.create_payment_intent(
                amount=1000,
                currency="usd",
                metadata=None,  # No metadata
            )

            # Verify metadata was NOT in params
            call_kwargs = mock_create.call_args[1]
            assert "metadata" not in call_kwargs

    def test_without_idempotency_key(self, stripe_service):
        """Create payment without idempotency key.
        
        Covers: line 62 branch - if idempotency_key: (False path)
        """
        with patch("stripe.PaymentIntent.create") as mock_create:
            mock_create.return_value = MagicMock(
                id="pi_test_123",
                status="requires_payment_method",
                amount=1000,
                currency="usd",
                client_secret="secret_123",
            )

            result = stripe_service.create_payment_intent(
                amount=1000,
                currency="usd",
                idempotency_key=None,  # No idempotency key
            )

            # Verify idempotency_key was NOT passed
            call_kwargs = mock_create.call_args[1]
            assert "idempotency_key" not in call_kwargs


class TestGetPaymentIntent:
    """Test get_payment_intent method.
    
    Covers: lines 104-126 (entire method, never called in existing tests)
    """

    @pytest.fixture
    def stripe_service(self):
        """Create StripeService with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_test_fake"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.USE_STRIPE_REAL = False

        with patch("app.services.stripe.client.settings", mock_settings):
            return StripeService()

    def test_get_payment_intent_success(self, stripe_service):
        """Successfully retrieve a PaymentIntent.
        
        Covers: lines 104-123 (happy path)
        """
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_intent.amount = 2000
        mock_intent.currency = "usd"
        mock_intent.charges.data = [
            MagicMock(id="ch_123", status="succeeded", amount=2000),
            MagicMock(id="ch_456", status="succeeded", amount=2000),
        ]

        with patch("stripe.PaymentIntent.retrieve") as mock_retrieve:
            mock_retrieve.return_value = mock_intent

            result = stripe_service.get_payment_intent("pi_test_123")

            assert result["id"] == "pi_test_123"
            assert result["status"] == "succeeded"
            assert result["amount"] == 2000
            assert result["currency"] == "usd"
            assert len(result["charges"]["data"]) == 2
            assert result["charges"]["data"][0]["id"] == "ch_123"

    def test_get_payment_intent_stripe_error(self, stripe_service):
        """StripeError during retrieve should be re-raised.
        
        Covers: lines 125-127
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error retrieving PaymentIntent: {str(e)}")
                raise
        """
        with patch("stripe.PaymentIntent.retrieve") as mock_retrieve:
            mock_retrieve.side_effect = stripe.error.StripeError(
                message="Intent not found",
            )

            with pytest.raises(stripe.error.StripeError) as exc_info:
                stripe_service.get_payment_intent("pi_nonexistent")

            assert "Intent not found" in str(exc_info.value)


class TestVerifyWebhookSignature:
    """Test verify_webhook_signature method.
    
    Covers: lines 142-157 (signature verification edge cases)
    """

    @pytest.fixture
    def stripe_service(self):
        """Create StripeService with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.STRIPE_API_KEY = "sk_test_fake"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"
        mock_settings.USE_STRIPE_REAL = False

        with patch("app.services.stripe.client.settings", mock_settings):
            return StripeService()

    def test_missing_signature_header(self, stripe_service):
        """Missing signature header returns None.
        
        Covers: lines 142-144
            if not sig_header:
                logger.warning("Webhook called without signature header")
                return None
        """
        result = stripe_service.verify_webhook_signature(
            payload=b'{"test": "data"}',
            sig_header=None,  # Missing header
        )

        assert result is None

    def test_invalid_payload_returns_none(self, stripe_service):
        """Invalid payload (ValueError) returns None.
        
        Covers: lines 151-153
            except ValueError as e:
                logger.error(f"Invalid webhook payload: {str(e)}")
                return None
        """
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = ValueError("Invalid JSON payload")

            result = stripe_service.verify_webhook_signature(
                payload=b"not-valid-json",
                sig_header="t=123,v1=abc",
            )

            assert result is None

    def test_invalid_signature_returns_none(self, stripe_service):
        """Invalid signature returns None.
        
        Covers: lines 155-157
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid webhook signature: {str(e)}")
                return None
        """
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                message="Signature mismatch",
                sig_header="invalid",
            )

            result = stripe_service.verify_webhook_signature(
                payload=b'{"test": "data"}',
                sig_header="t=123,v1=wrong_signature",
            )

            assert result is None

    def test_valid_signature_returns_event(self, stripe_service):
        """Valid signature returns the event dict.
        
        Covers: lines 146-149 (success path)
        """
        expected_event = {
            "id": "evt_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_123"}},
        }

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = expected_event

            result = stripe_service.verify_webhook_signature(
                payload=b'{"test": "data"}',
                sig_header="t=123,v1=valid_sig",
            )

            assert result == expected_event
            assert result["type"] == "payment_intent.succeeded"
