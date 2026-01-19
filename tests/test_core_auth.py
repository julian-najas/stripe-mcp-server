"""Tests for authentication module - covers production mode branches.

Target: app/core/auth.py lines 20-31 (production mode with API_KEY configured)
Current coverage: 35% → Target: 100%
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.core.auth import verify_api_key


class TestAuthProductionMode:
    """Test auth in production mode (DEBUG=false, API_KEY configured).
    
    These tests cover lines 20-31 in auth.py which are never executed
    when DEBUG=true (current test suite default).
    """

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self):
        """Missing X-API-Key header should return 401 Unauthorized.
        
        Covers: lines 21-24
            if not x_api_key:
                logger.warning("Missing API key header")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header"
                )
        """
        mock_settings = MagicMock()
        mock_settings.DEBUG = False
        mock_settings.API_KEY = "production-secret-key"

        with patch("app.core.auth.settings", mock_settings):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Missing X-API-Key header"

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_403(self):
        """Invalid API key should return 403 Forbidden.
        
        Covers: lines 26-29
            if x_api_key != settings.API_KEY:
                logger.warning(f"Invalid API key: {x_api_key[:10]}...")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
        """
        mock_settings = MagicMock()
        mock_settings.DEBUG = False
        mock_settings.API_KEY = "production-secret-key"

        with patch("app.core.auth.settings", mock_settings):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong-key-value")

            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Invalid API key"

    @pytest.mark.asyncio
    async def test_valid_api_key_passes(self):
        """Valid API key should pass authentication.
        
        Covers: line 31 (return statement after all checks pass)
            return x_api_key or "authenticated"
        """
        mock_settings = MagicMock()
        mock_settings.DEBUG = False
        mock_settings.API_KEY = "production-secret-key"

        with patch("app.core.auth.settings", mock_settings):
            result = await verify_api_key(x_api_key="production-secret-key")

            assert result == "production-secret-key"

    @pytest.mark.asyncio
    async def test_no_api_key_configured_allows_any(self):
        """When API_KEY is None, any request passes (no validation).
        
        Covers: branch where settings.API_KEY is falsy (line 20 condition false)
            if settings.API_KEY:  # This branch is False when API_KEY is None
        """
        mock_settings = MagicMock()
        mock_settings.DEBUG = False
        mock_settings.API_KEY = None  # No API key configured

        with patch("app.core.auth.settings", mock_settings):
            # Should pass without any key
            result = await verify_api_key(x_api_key=None)
            assert result == "authenticated"

            # Should also pass with any key
            result = await verify_api_key(x_api_key="any-random-key")
            assert result == "any-random-key"


class TestAuthDebugMode:
    """Test auth in debug mode (DEBUG=true) - verifies existing behavior.
    
    Covers: lines 14-16
        if settings.DEBUG:
            logger.debug("Debug mode: skipping API key validation")
            return "debug-mode"
    """

    @pytest.mark.asyncio
    async def test_debug_mode_skips_validation(self):
        """Debug mode should skip all validation and return 'debug-mode'.
        
        Covers: lines 14-16 (early return in debug mode)
        """
        mock_settings = MagicMock()
        mock_settings.DEBUG = True
        mock_settings.API_KEY = "should-be-ignored"

        with patch("app.core.auth.settings", mock_settings):
            # No key provided - should still pass
            result = await verify_api_key(x_api_key=None)
            assert result == "debug-mode"

            # Wrong key provided - should still pass
            result = await verify_api_key(x_api_key="wrong-key")
            assert result == "debug-mode"
