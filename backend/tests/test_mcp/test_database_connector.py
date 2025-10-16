# backend/tests/test_mcp/test_database_connector.py

"""Unit Tests for Database Query Tool."""

import pytest
from app.mcp.schemas import DatabaseQueryInput
from app.mcp.tools.database_connector import query_database

pytestmark = pytest.mark.unit


class TestDatabaseConnector:
    """Tests for SQL query execution."""
    
    @pytest.mark.asyncio
    @pytest.mark.database  # Custom marker for database tests
    async def test_simple_select_query_success(self):
        """Test executing simple SELECT query."""
        # Arrange
        input_data = DatabaseQueryInput(
            query="SELECT 1 as test_col, 'test' as text_col",
            limit=10
        )
        
        # Act
        result = await query_database(input_data)
        
        # Assert
        assert result.success is True
        assert result.row_count == 1
        assert result.rows[0]["test_col"] == 1
        assert result.rows[0]["text_col"] == "test"
        assert result.columns == ["test_col", "text_col"]
    
    @pytest.mark.asyncio
    async def test_non_select_query_rejected(self):
        """Test that non-SELECT queries are blocked for security."""
        # Arrange - Try to run DELETE query
        input_data = DatabaseQueryInput(
            query="DELETE FROM conversations WHERE id = '123'",
            limit=10
        )
        
        # Act
        result = await query_database(input_data)
        
        # Assert
        assert result.success is False
        assert "only select" in result.error.lower()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dangerous_query",
        [
            "DROP TABLE conversations",
            "UPDATE conversations SET title = 'hacked'",
            "INSERT INTO conversations VALUES (1, 'test')",
            "ALTER TABLE conversations ADD COLUMN hack TEXT",
        ]
    )
    async def test_dangerous_queries_rejected(self, dangerous_query):
        """Test that dangerous SQL operations are blocked."""
        # Arrange
        input_data = DatabaseQueryInput(
            query=dangerous_query,
            limit=10
        )
        
        # Act
        result = await query_database(input_data)
        
        # Assert
        assert result.success is False
        assert result.error is not None
