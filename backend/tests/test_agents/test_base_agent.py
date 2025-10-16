# backend/tests/test_agents/test_base_agent.py

"""Unit Tests for Base Agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from app.agents.base_agent import BaseAgent

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestBaseAgent:
    """Tests for base agent functionality."""
    
    def test_agent_initialization(self):
        """Test that agent initializes with correct properties."""
        # Arrange & Act
        agent = BaseAgent(
            name="test_agent",
            system_prompt="You are a test agent",
            tools=[],
            temperature=0.5
        )
        
        # Assert
        assert agent.name == "test_agent"
        assert agent.system_prompt == "You are a test agent"
        assert agent.temperature == 0.5
        assert agent.llm is not None
    
    @pytest.mark.asyncio
    async def test_agent_execute_success(self, mock_llm_response):
        """Test successful agent execution."""
        # Arrange
        agent = BaseAgent(
            name="test_agent",
            system_prompt="Test prompt",
            tools=[],
            temperature=0.0
        )
        
        # Mock LLM to return specific response
        mock_llm_response.return_value.content = "Test response from LLM"
        
        # Act
        result = await agent.execute("What is 2+2?")
        
        # Assert
        assert result["success"] is True
        assert result["agent_name"] == "test_agent"
        assert "Test response" in result["output"]
        assert result["metadata"] is not None
    
    @pytest.mark.asyncio
    async def test_agent_execute_with_context(self, mock_llm_response):
        """Test agent execution with additional context."""
        # Arrange
        agent = BaseAgent(
            name="test_agent",
            system_prompt="Test prompt",
            tools=[],
        )
        
        context = {
            "previous_result": "42",
            "user_preference": "detailed",
        }
        
        # Act
        result = await agent.execute(
            "Continue analysis",
            context=context
        )
        
        # Assert
        assert result["success"] is True
        # Verify LLM was called (mocked function was invoked)
        assert mock_llm_response.called
