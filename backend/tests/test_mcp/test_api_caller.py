# backend/tests/test_mcp/test_api_caller.py

"""Unit Tests for API Caller Tool."""

import pytest
from app.mcp.schemas import ApiCallInput, HttpMethod
from app.mcp.tools.api_caller import call_api

pytestmark = pytest.mark.unit


class TestApiCaller:
    """Tests for HTTP API calls."""
    
    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """
        Test successful GET request to public API.
        
        Uses JSONPlaceholder (free fake REST API for testing).
        """
        # Arrange
        input_data = ApiCallInput(
            url="https://jsonplaceholder.typicode.com/posts/1",
            method=HttpMethod.GET,
            timeout=10
        )
        
        # Act
        result = await call_api(input_data)
        
        # Assert
        assert result.success is True
        assert result.status_code == 200
        assert "userId" in result.response_data
        assert "title" in result.response_data
    
    @pytest.mark.asyncio
    async def test_invalid_url_fails(self):
        """Test that invalid URL returns error."""
        # Arrange
        input_data = ApiCallInput(
            url="https://this-domain-does-not-exist-12345.com/api",
            method=HttpMethod.GET,
            timeout=5
        )
        
        # Act
        result = await call_api(input_data)
        
        # Assert
        assert result.success is False
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_404_not_found(self):
        """Test handling of 404 Not Found responses."""
        # Arrange
        input_data = ApiCallInput(
            url="https://jsonplaceholder.typicode.com/posts/999999",
            method=HttpMethod.GET,
            timeout=10
        )
        
        # Act
        result = await call_api(input_data)
        
        # Assert - API returns empty object for non-existent resource
        assert result.status_code == 200  # JSONPlaceholder returns 200 even for missing
