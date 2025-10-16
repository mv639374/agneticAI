# backend/tests/test_mcp/test_file_reader.py

"""
Unit Tests for File Reader Tool

TESTING PHILOSOPHY:
- Test one thing at a time
- Test both success and failure cases
- Use descriptive test names
- Arrange-Act-Assert pattern
"""

import pytest
from app.mcp.schemas import FileReadInput, FileType
from app.mcp.tools.file_reader import read_file

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestFileReader:
    """
    Group related tests in a class.
    
    NAMING CONVENTION:
    - Class: Test<ComponentName>
    - Method: test_<what_it_tests>_<expected_outcome>
    """
    
    # =========================================================================
    # TEXT FILE TESTS
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_read_text_file_success(self, temp_test_file):
        """
        Test reading a text file successfully.
        
        ARRANGE-ACT-ASSERT PATTERN:
        1. Arrange: Set up test data (temp_test_file fixture)
        2. Act: Call the function being tested
        3. Assert: Verify the result
        """
        # Arrange
        input_data = FileReadInput(
            file_path=temp_test_file,
            file_type=FileType.TEXT
        )
        
        # Act
        result = await read_file(input_data)
        
        # Assert
        assert result.success is True
        assert result.error is None
        assert "Test file content" in result.content
        assert result.metadata is not None
        assert result.metadata["file_name"] == "test_data.txt"
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file_fails(self):
        """Test that reading non-existent file returns error."""
        # Arrange
        input_data = FileReadInput(
            file_path="/nonexistent/file.txt",
            file_type=FileType.TEXT
        )
        
        # Act
        result = await read_file(input_data)
        
        # Assert
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()
    
    # =========================================================================
    # CSV FILE TESTS
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_read_csv_file_success(self, temp_csv_file):
        """Test reading CSV file and formatting."""
        # Arrange
        input_data = FileReadInput(
            file_path=temp_csv_file,
            file_type=FileType.CSV
        )
        
        # Act
        result = await read_file(input_data)
        
        # Assert
        assert result.success is True
        assert "CSV Data" in result.content
        assert "Alice" in result.content
        assert "Bob" in result.content
        assert "Row count: 3" in result.content
    
    # =========================================================================
    # JSON FILE TESTS
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_read_json_file_success(self, temp_json_file):
        """Test reading JSON file and parsing."""
        # Arrange
        input_data = FileReadInput(
            file_path=temp_json_file,
            file_type=FileType.JSON
        )
        
        # Act
        result = await read_file(input_data)
        
        # Assert
        assert result.success is True
        assert "users" in result.content
        assert "Alice" in result.content
    
    # =========================================================================
    # PARAMETRIZED TESTS (Test multiple inputs with same logic)
    # =========================================================================
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "file_type,expected_in_metadata",
        [
            (FileType.TEXT, "text"),
            (FileType.JSON, "json"),
            (FileType.CSV, "csv"),
        ]
    )
    async def test_metadata_contains_file_type(
        self, 
        temp_test_file, 
        file_type, 
        expected_in_metadata
    ):
        """
        Test that metadata contains correct file type.
        
        PARAMETRIZE allows testing same logic with different inputs.
        This runs 3 times with different file_type values.
        """
        # Arrange
        input_data = FileReadInput(
            file_path=temp_test_file,
            file_type=file_type
        )
        
        # Act
        result = await read_file(input_data)
        
        # Assert
        assert result.metadata["file_type"] == file_type
