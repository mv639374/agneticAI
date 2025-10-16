# backend/tests/test_agents/test_analysis_agent.py

"""Unit Tests for Analysis Agent."""

import pytest
from app.agents.analysis_agent import AnalysisAgent

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestAnalysisAgent:
    """Tests for analysis agent."""
    
    @pytest.mark.asyncio
    async def test_analysis_agent_initialization(self):
        """Test analysis agent initializes correctly."""
        # Act
        agent = AnalysisAgent()
        
        # Assert
        assert agent.name == "analysis_agent"
        assert agent.temperature == 0.3
        assert len(agent.tools) == 0  # No external tools
    
    @pytest.mark.asyncio
    async def test_calculation_request(self, mock_llm_response):
        """Test handling calculation requests."""
        # Arrange
        agent = AnalysisAgent()
        mock_llm_response.return_value.content = "The average is 30"
        
        # Act
        result = await agent.execute(
            "Calculate the average of 10, 20, 30, 40, 50"
        )
        
        # Assert
        assert result["success"] is True
        assert "average" in result["output"].lower()
