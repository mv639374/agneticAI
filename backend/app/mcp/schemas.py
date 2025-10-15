# agenticAI/backend/app/mcp/schemas.py

"""
Pydantic Schemas for MCP Tool Inputs and Outputs

These schemas define the structure of data passed to and from MCP tools.
They provide:
1. Type validation
2. Auto-generated JSON schemas for LLMs
3. Documentation for each field
4. Default values where appropriate

Why strict schemas matter for LLM tools:
- LLMs generate JSON arguments based on schema
- Clear field descriptions help LLM choose correct values
- Validation prevents runtime errors from malformed LLM output
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# FILE READER TOOL SCHEMAS
# =============================================================================
class FileType(str, Enum):
    """Supported file types for reading."""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    MARKDOWN = "markdown"


class FileReadInput(BaseModel):
    """
    Input schema for file reading tool.
    
    PROMPT ENGINEERING NOTE:
    - Field descriptions are crucial - LLM uses them to decide arguments
    - Use action verbs: "Path to the file" vs "File path"
    - Include examples in description for complex fields
    - Specify constraints: "Must be absolute path" vs "Path"
    """
    
    file_path: str = Field(
        ...,
        description=(
            "Absolute or relative path to the file to read. "
            "Examples: '/app/data/uploads/report.pdf', './data/sample.csv'"
        ),
        min_length=1,
    )
    
    file_type: FileType = Field(
        default=FileType.TEXT,
        description=(
            "Type of file to read. Determines parsing strategy. "
            "Use 'pdf' for PDF documents, 'csv' for tabular data, "
            "'json' for structured data, 'text' for plain text."
        )
    )
    
    encoding: str = Field(
        default="utf-8",
        description="File encoding. Usually 'utf-8' for modern files."
    )


class FileReadOutput(BaseModel):
    """Output schema for file reading tool."""
    
    success: bool = Field(description="Whether file was read successfully")
    content: Optional[str] = Field(default=None, description="File contents")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="File metadata (size, type, line count, etc.)"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# DATABASE CONNECTOR TOOL SCHEMAS
# =============================================================================
class DatabaseQueryInput(BaseModel):
    """
    Input schema for database query tool.
    
    PROMPT ENGINEERING NOTE:
    - Security: Emphasize read-only nature in description
    - Examples: Include sample queries to guide LLM
    - Constraints: Specify allowed operations (SELECT only)
    """
    
    query: str = Field(
        ...,
        description=(
            "SQL query to execute. MUST be a SELECT statement (read-only). "
            "Examples: "
            "'SELECT * FROM conversations LIMIT 10', "
            "'SELECT COUNT(*) FROM agent_executions WHERE status = \\'completed\\'', "
            "'SELECT agent_name, AVG(duration_ms) FROM agent_executions GROUP BY agent_name'"
        ),
        min_length=1,
    )
    
    limit: int = Field(
        default=100,
        description="Maximum number of rows to return. Prevents overwhelming the LLM.",
        ge=1,
        le=1000,
    )


class DatabaseQueryOutput(BaseModel):
    """Output schema for database query tool."""
    
    success: bool = Field(description="Whether query executed successfully")
    rows: Optional[list[dict]] = Field(
        default=None,
        description="Query results as list of row dictionaries"
    )
    row_count: int = Field(default=0, description="Number of rows returned")
    columns: Optional[list[str]] = Field(
        default=None,
        description="Column names in result set"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# API CALLER TOOL SCHEMAS
# =============================================================================
class HttpMethod(str, Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ApiCallInput(BaseModel):
    """
    Input schema for API calling tool.
    
    PROMPT ENGINEERING NOTE:
    - Flexibility: Support multiple HTTP methods and headers
    - Guidance: Provide examples for common APIs
    - Safety: Warn about sensitive data in description
    """
    
    url: str = Field(
        ...,
        description=(
            "Full URL to call. Must include protocol (http:// or https://). "
            "Examples: "
            "'https://api.openweathermap.org/data/2.5/weather?q=London', "
            "'https://jsonplaceholder.typicode.com/posts/1'"
        ),
        min_length=1,
    )
    
    method: HttpMethod = Field(
        default=HttpMethod.GET,
        description="HTTP method to use. GET for fetching data, POST for creating."
    )
    
    headers: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "HTTP headers to include. "
            "Example: {'Authorization': 'Bearer token', 'Content-Type': 'application/json'}"
        )
    )
    
    body: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Request body for POST/PUT/PATCH requests. "
            "Must be JSON-serializable dictionary."
        )
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300,
    )


class ApiCallOutput(BaseModel):
    """Output schema for API calling tool."""
    
    success: bool = Field(description="Whether API call succeeded")
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code (200, 404, 500, etc.)"
    )
    response_data: Optional[Any] = Field(
        default=None,
        description="Response body (parsed JSON or text)"
    )
    headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Response headers"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")