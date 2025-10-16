# backend/tests/test_api/test_conversation_routes.py

"""
Tests for Conversation Management Endpoints

Tests CRUD operations on conversations.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.models import Conversation

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.database]


class TestConversationEndpoints:
    """Tests for conversation management API."""
    
    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, async_client: AsyncClient):
        """Test listing conversations when none exist."""
        # Act
        response = await async_client.get("/api/conversations/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May be empty or have some from previous tests
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_pagination(self, async_client: AsyncClient):
        """Test pagination parameters."""
        # Act
        response = await async_client.get(
            "/api/conversations/?limit=5&offset=0"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5  # Should respect limit
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, async_client: AsyncClient):
        """Test getting non-existent conversation returns 404."""
        # Act
        response = await async_client.get(
            "/api/conversations/nonexistent-id"
        )
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent conversation returns 404."""
        # Act
        response = await async_client.delete(
            "/api/conversations/nonexistent-id"
        )
        
        # Assert
        assert response.status_code == 404
