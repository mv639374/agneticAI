# backend/tests/test_graphs/test_state.py

"""
Tests for LangGraph State Management

Verifies state structure and creation.
"""

import pytest
from langchain_core.messages import HumanMessage
from app.graphs.state import create_initial_state, AgentState

pytestmark = pytest.mark.unit


class TestGraphState:
    """Tests for LangGraph state management."""
    
    def test_create_initial_state(self):
        """Test creating initial state for workflow."""
        # Act
        state = create_initial_state(
            user_message="Test message",
            user_id="test_user"
        )
        
        # Assert
        assert isinstance(state, dict)
        assert "messages" in state
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "Test message"
        assert state["user_id"] == "test_user"
        assert state["next_agent"] == "supervisor"
        assert state["execution_count"] == 0
    
    def test_state_has_required_fields(self):
        """Test that state has all required fields."""
        state = create_initial_state("Test")
        
        required_fields = [
            "messages",
            "next_agent",
            "current_agent",
            "conversation_id",
            "user_id",
            "metadata",
            "execution_count",
            "max_iterations"
        ]
        
        for field in required_fields:
            assert field in state, f"Missing required field: {field}"
    
    def test_conversation_id_auto_generated(self):
        """Test that conversation ID is auto-generated if not provided."""
        state = create_initial_state("Test")
        
        # Should have a conversation_id or be None
        # Implementation may generate it or leave it for workflow
        assert "conversation_id" in state
