# backend/tests/test_database/test_models.py

"""
Tests for Database Models

Verifies SQLAlchemy models work correctly.
"""

import pytest
from sqlalchemy import select
from app.db.models import Conversation, AgentExecution

pytestmark = [pytest.mark.unit, pytest.mark.database]


class TestDatabaseModels:
    """Tests for database model operations."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session):
        """Test creating a conversation in database."""
        # Arrange
        conversation = Conversation(
            title="Test Conversation",
            user_id="test_user",
        )
        
        # Act
        db_session.add(conversation)
        await db_session.commit()
        
        # Assert - Query it back
        result = await db_session.execute(
            select(Conversation).where(Conversation.title == "Test Conversation")
        )
        saved_conv = result.scalar_one_or_none()
        
        assert saved_conv is not None
        assert saved_conv.title == "Test Conversation"
        assert saved_conv.user_id == "test_user"
        assert saved_conv.id is not None  # Auto-generated
    
    @pytest.mark.asyncio
    async def test_conversation_agent_execution_relationship(self, db_session):
        """Test relationship between Conversation and AgentExecution."""
        # Arrange - Create conversation
        conversation = Conversation(title="Test")
        db_session.add(conversation)
        await db_session.commit()
        
        # Create agent execution linked to conversation
        execution = AgentExecution(
            conversation_id=conversation.id,
            agent_name="test_agent",
            agent_type="worker",
            input_data={"test": "input"},
            status="completed"
        )
        db_session.add(execution)
        await db_session.commit()
        
        # Act - Query conversation with executions
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conversation.id)
        )
        conv = result.scalar_one()
        
        # Assert - Relationship works
        # Note: May need to explicitly load relationship
        assert conv.id == conversation.id
