"""Integration tests for health and root endpoints"""

import pytest


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_root_endpoint(self, client):
        """Should return API information"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tana-Connector API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"

    def test_health_check_endpoint(self, client):
        """Should return health status"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
