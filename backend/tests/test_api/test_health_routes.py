# backend/tests/test_api/test_health_routes.py

"""
Tests for Health Check Endpoints

These tests verify that health endpoints return correct status.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.unit, pytest.mark.api]


class TestHealthEndpoints:
    """Tests for health check routes."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, async_client: AsyncClient):
        """
        Test /api/health returns 200 OK.
        
        This is the most basic API test.
        """
        # Act
        response = await async_client.get("/api/health")
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_liveness_probe(self, async_client: AsyncClient):
        """Test Kubernetes liveness probe endpoint."""
        # Act
        response = await async_client.get("/api/health/live")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    @pytest.mark.asyncio
    async def test_readiness_probe(self, async_client: AsyncClient):
        """Test Kubernetes readiness probe endpoint."""
        # Act
        response = await async_client.get("/api/health/ready")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
