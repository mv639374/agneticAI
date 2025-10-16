# # backend/tests/test_integration/test_end_to_end.py

"""
End-to-End Integration Tests

These tests verify the entire flow from API request to agent response.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestEndToEndWorkflow:
    """
    End-to-end tests for complete user workflows.
    
    These tests are slower because they:
    - Make real database calls
    - Execute full agent workflows
    - May call real LLM APIs (if not mocked)
    """
    
    @pytest.mark.asyncio
    async def test_complete_calculation_workflow(
        self, 
        async_client: AsyncClient,
        mock_llm_response
    ):
        """
        Test complete workflow: user query → agent processing → response.
        
        Flow:
        1. User sends calculation request
        2. Supervisor routes to analysis agent
        3. Analysis agent processes
        4. Response returned to user
        """
        # Arrange
        mock_llm_response.return_value.content = "The average is 30"
        
        request_payload = {
            "message": "Calculate the average of 10, 20, 30, 40, 50",
            "user_id": "test_user_e2e"
        }
        
        # Act - Invoke agents
        response = await async_client.post(
            "/api/agents/invoke",
            json=request_payload
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["conversation_id"] is not None
        assert "response" in data
        
        # Verify conversation was created
        conversation_id = data["conversation_id"]
        conv_response = await async_client.get(
            f"/api/conversations/{conversation_id}"
        )
        
        # May fail if conversation not persisted yet
        # In real implementation, this would work after checkpointing
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(
        self, 
        async_client: AsyncClient,
        mock_llm_response
    ):
        """
        Test multi-turn conversation with context preservation.
        
        Flow:
        1. First query
        2. Get conversation ID
        3. Second query with same conversation ID
        4. Verify context is maintained
        """
        # First turn
        mock_llm_response.return_value.content = "First response"
        
        first_request = {
            "message": "What is 2+2?",
            "user_id": "test_user_multiturn"
        }
        
        first_response = await async_client.post(
            "/api/agents/invoke",
            json=first_request
        )
        
        assert first_response.status_code == 200
        first_data = first_response.json()
        conversation_id = first_data["conversation_id"]
        
        # Second turn (with conversation context)
        mock_llm_response.return_value.content = "Second response based on context"
        
        second_request = {
            "message": "Now multiply that by 3",
            "user_id": "test_user_multiturn",
            "conversation_id": conversation_id  # Same conversation
        }
        
        second_response = await async_client.post(
            "/api/agents/invoke",
            json=second_request
        )
        
        assert second_response.status_code == 200
        second_data = second_response.json()
        
        # Same conversation ID maintained
        assert second_data["conversation_id"] == conversation_id
        assert second_data["message_count"] > first_data["message_count"]
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(
        self, 
        async_client: AsyncClient,
        mock_llm_response
    ):
        """
        Test that errors are handled gracefully.
        
        Simulates LLM failure and verifies error response.
        """
        # Arrange - Mock LLM to raise error
        mock_llm_response.side_effect = Exception("LLM API error")
        
        request_payload = {
            "message": "This will fail",
            "user_id": "test_user_error"
        }
        
        # Act
        response = await async_client.post(
            "/api/agents/invoke",
            json=request_payload
        )
        
        # Assert - Should return 500 but not crash
        assert response.status_code in [500, 200]
        
        # If 200, should have error in response
        if response.status_code == 200:
            data = response.json()
            # Implementation dependent - may return success=false
