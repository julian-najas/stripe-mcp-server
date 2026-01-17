"""Smoke and E2E tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def api_server():
    """Provide test client for E2E testing."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint(self, api_server):
        """Test /health endpoint."""
        response = api_server.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "debug" in data

    def test_ready_endpoint(self, api_server):
        """Test /ready endpoint."""
        response = api_server.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    def test_root_endpoint(self, api_server):
        """Test root endpoint."""
        response = api_server.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestToolsEndpoints:
    """Test protected tools endpoints."""

    def test_add_with_valid_key(self, api_server):
        """Test /tools/add with valid API key."""
        response = api_server.post(
            "/api/v1/tools/add", json={"a": 2, "b": 3}, headers={"X-API-Key": "demo-key-12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 5
        assert data["a"] == 2
        assert data["b"] == 3

    def test_add_debug_mode(self, api_server):
        """Test /tools/add in debug mode (DEBUG=true)."""
        response = api_server.post(
            "/api/v1/tools/add",
            json={"a": 5, "b": 7},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 12

    def test_multiply_with_valid_key(self, api_server):
        """Test /tools/multiply with valid API key."""
        response = api_server.post(
            "/api/v1/tools/multiply", json={"a": 3, "b": 4}, headers={"X-API-Key": "demo-key-12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 12

    def test_add_without_key_in_debug(self, api_server):
        """Test /tools/add without key in debug mode."""
        response = api_server.post(
            "/api/v1/tools/add",
            json={"a": 1, "b": 1},
        )
        assert response.status_code == 200

    def test_request_id_header(self, api_server):
        """Test that X-Request-ID header is returned."""
        response = api_server.get("/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 36  # UUID4 length
