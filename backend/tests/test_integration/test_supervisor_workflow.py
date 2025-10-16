# backend/tests/test_integration/test_supervisor_workflow.py


"""
Integration Tests for Supervisor Workflow

Tests LangGraph supervisor orchestration.
"""

import pytest
from app.graphs.supervisor_graph import execute_agent_workflow

pytestmark = [pytest.mark.integration, pytest.mark.agents]


class TestSupervisorWorkflow:
    """Tests for supervisor agent orchestration."""
    
    @pytest.mark.asyncio
    async def test_supervisor_routes_to_analysis_agent(self, mock_llm_response):
        """Test that supervisor correctly routes calculation requests."""
        # Arrange
        mock_llm_response.return_value.content = "30"
        
        # Act
        result = await execute_agent_workflow(
            user_message="What is the average of 10, 20, 30, 40, 50?",
            user_id="test_user_supervisor"
        )
        
        # Assert
        assert result["success"] is True
        assert result["conversation_id"] is not None
        assert "response" in result
    
    @pytest.mark.asyncio
    async def test_supervisor_handles_file_request(
        self, 
        mock_llm_response,
        temp_test_file
    ):
        """Test supervisor routes file reading to data ingestion agent."""
        # Arrange
        mock_llm_response.return_value.content = f"File content from {temp_test_file}"
        
        # Act
        result = await execute_agent_workflow(
            user_message=f"Read the file {temp_test_file}",
            user_id="test_user_file"
        )
        
        # Assert
        assert result["success"] is True
