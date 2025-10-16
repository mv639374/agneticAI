# backend/tests/test_api/test_agent_routes.py

"""
Tests for Agent API Endpoints

Tests the /api/agents/* endpoints.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestAgentEndpoints:
    """Tests for agent invocation API."""
    
    @pytest.mark.asyncio
    async def test_agent_status_endpoint(self, async_client: AsyncClient):
        """Test /api/agents/status returns agent information."""
        # Act
        response = await async_client.get("/api/agents/status")
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "agent_count" in data
        assert data["agent_count"] == 6  # 1 supervisor + 5 workers
        assert "agents" in data
        
        # Verify agent names
        agent_names = [agent["name"] for agent in data["agents"]]
        assert "supervisor" in agent_names
        assert "data_ingestion_agent" in agent_names
        assert "analysis_agent" in agent_names
    
    @pytest.mark.asyncio
    async def test_invoke_agents_success(
        self, 
        async_client: AsyncClient,
        sample_agent_invoke_request,
        mock_llm_response
    ):
        """
        Test successful agent invocation.
        
        This mocks LLM responses to avoid real API calls.
        """
        # Arrange
        mock_llm_response.return_value.content = "The average is 30"
        
        # Act
        response = await async_client.post(
            "/api/agents/invoke",
            json=sample_agent_invoke_request
        )
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "conversation_id" in data
        assert "response" in data
        assert data["message_count"] > 0
    
    @pytest.mark.asyncio
    async def test_invoke_agents_empty_message_fails(self, async_client: AsyncClient):
        """Test that empty message returns validation error."""
        # Arrange
        invalid_request = {
            "message": "",  # Empty message
            "user_id": "test_user"
        }
        
        # Act
        response = await async_client.post(
            "/api/agents/invoke",
            json=invalid_request
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invoke_agents_missing_message_fails(self, async_client: AsyncClient):
        """Test that missing required field returns error."""
        # Arrange
        invalid_request = {
            "user_id": "test_user"
            # Missing 'message' field
        }
        
        # Act
        response = await async_client.post(
            "/api/agents/invoke",
            json=invalid_request
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
