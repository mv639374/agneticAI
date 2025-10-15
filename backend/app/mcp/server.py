# agenticAI/backend/app/mcp/server.py

"""
FastMCP Server Implementation

This module creates an MCP server that exposes tools to LLM agents.

MCP (Model Context Protocol) enables:
- Standardized tool interface for LLMs
- Dynamic tool discovery
- Type-safe tool invocation
- Error handling and retries

ARCHITECTURE:
1. FastMCP server registers tools
2. LangChain agents discover available tools
3. LLM generates tool calls (function name + arguments)
4. MCP server validates arguments and executes tool
5. Tool result returned to LLM
6. LLM processes result and continues reasoning

PROMPT ENGINEERING FOR TOOL SELECTION:
The LLM needs clear descriptions to choose the right tool:
- Tool name: Descriptive and action-oriented
- Tool description: Explains when to use, inputs, outputs
- Parameter descriptions: Guide argument generation
"""

from fastmcp import FastMCP

from app.config import settings
from app.mcp.schemas import ApiCallInput, DatabaseQueryInput, FileReadInput
from app.mcp.tools.api_caller import call_api
from app.mcp.tools.database_connector import query_database, get_database_schema
from app.mcp.tools.file_reader import read_file
from app.utils.logger import get_logger

log = get_logger(__name__)


# =============================================================================
# FASTMCP SERVER INITIALIZATION
# =============================================================================
mcp_server = FastMCP("AgenticAI-Tools", dependencies=[])


# =============================================================================
# TOOL REGISTRATION
# =============================================================================

@mcp_server.tool()
async def read_file_tool(
    file_path: str,
    file_type: str = "text",
    encoding: str = "utf-8",
) -> dict:
    """
    Read and parse files from the filesystem.
    
    **When to use this tool:**
    - User uploads a document and asks questions about it
    - Need to read configuration files
    - Extract data from CSV or JSON files
    - Read text from PDF documents
    
    **Supported file types:**
    - text: Plain text files (.txt, .log)
    - json: JSON data files
    - csv: Comma-separated value files
    - pdf: PDF documents
    - markdown: Markdown files (.md)
    
    **Examples:**
    - Read uploaded report: read_file_tool(file_path="data/uploads/report.pdf", file_type="pdf")
    - Parse CSV data: read_file_tool(file_path="data/sales.csv", file_type="csv")
    - Read config: read_file_tool(file_path="config.json", file_type="json")
    
    Args:
        file_path: Path to file (absolute or relative to app root)
        file_type: Type of file (text/json/csv/pdf/markdown)
        encoding: File encoding (default: utf-8)
    
    Returns:
        Dictionary with 'success', 'content', 'metadata', and optional 'error'
    """
    input_data = FileReadInput(
        file_path=file_path,
        file_type=file_type,
        encoding=encoding,
    )
    result = await read_file(input_data)
    return result.model_dump()


@mcp_server.tool()
async def query_database_tool(
    query: str,
    limit: int = 100,
) -> dict:
    """
    Execute SQL queries to retrieve data from the PostgreSQL database.
    
    **When to use this tool:**
    - Find past conversation history
    - Analyze agent performance metrics
    - Generate usage statistics
    - Search for specific conversations or executions
    
    **Database Schema:**
    {}
    
    **Important Notes:**
    - Only SELECT queries allowed (read-only access)
    - Maximum 1000 rows returned
    - Results are automatically limited if LIMIT not specified
    - Use WHERE clauses to filter results
    - Use GROUP BY for aggregations
    
    **Examples:**
    - Recent conversations: query_database_tool(query="SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10")
    - Agent stats: query_database_tool(query="SELECT agent_name, COUNT(*) as count FROM agent_executions GROUP BY agent_name")
    - Failed tasks: query_database_tool(query="SELECT * FROM agent_executions WHERE status = 'failed'")
    
    Args:
        query: SQL SELECT query to execute
        limit: Maximum rows to return (default: 100, max: 1000)
    
    Returns:
        Dictionary with 'success', 'rows', 'row_count', 'columns', and optional 'error'
    """.format(get_database_schema())
    
    input_data = DatabaseQueryInput(query=query, limit=limit)
    result = await query_database(input_data)
    return result.model_dump()


@mcp_server.tool()
async def call_external_api_tool(
    url: str,
    method: str = "GET",
    headers: dict = None,
    body: dict = None,
    timeout: int = 30,
) -> dict:
    """
    Make HTTP requests to external APIs.
    
    **When to use this tool:**
    - Fetch real-time data (weather, stock prices, news)
    - Integrate with third-party services
    - Call REST APIs for additional context
    - Access public or authenticated APIs
    
    **Supported HTTP methods:**
    - GET: Retrieve data
    - POST: Create resources
    - PUT: Update resources
    - DELETE: Remove resources
    - PATCH: Partial updates
    
    **Authentication:**
    Include API keys in headers:
    ```
    headers = {{"Authorization": "Bearer YOUR_API_KEY"}}
    ```
    
    Or in URL parameters:
    ```
    url = "https://api.example.com/data?apikey=YOUR_KEY"
    ```
    
    **Examples:**
    - Weather data: call_external_api_tool(url="https://api.openweathermap.org/data/2.5/weather?q=London&appid=KEY")
    - Create item: call_external_api_tool(url="https://api.example.com/items", method="POST", body={{"name": "Item"}})
    - Fetch JSON: call_external_api_tool(url="https://jsonplaceholder.typicode.com/posts/1")
    
    Args:
        url: Full URL to call (must include http:// or https://)
        method: HTTP method (GET/POST/PUT/DELETE/PATCH)
        headers: Optional HTTP headers (dict)
        body: Optional request body for POST/PUT/PATCH (dict)
        timeout: Request timeout in seconds (default: 30, max: 300)
    
    Returns:
        Dictionary with 'success', 'status_code', 'response_data', 'headers', and optional 'error'
    """
    input_data = ApiCallInput(
        url=url,
        method=method,
        headers=headers,
        body=body,
        timeout=timeout,
    )
    result = await call_api(input_data)
    return result.model_dump()


# =============================================================================
# MCP SERVER MANAGEMENT
# =============================================================================
async def initialize_mcp_server() -> None:
    """
    Initialize MCP server.
    
    This is called at application startup to ensure all tools are registered.
    """
    log.info(
        "MCP server initialized",
        tool_count=3,
        tools=["read_file_tool", "query_database_tool", "call_external_api_tool"],
    )


def get_mcp_tools() -> list:
    """
    Get list of available MCP tools for LangChain integration.
    
    This converts FastMCP tools to LangChain-compatible format.
    
    Returns:
        List of tool definitions
    """
    # In Step 1.4, we'll integrate these with LangChain
    return [
        {
            "name": "read_file",
            "description": "Read and parse files (text, JSON, CSV, PDF)",
            "function": read_file_tool,
        },
        {
            "name": "query_database",
            "description": "Execute SQL queries on PostgreSQL database",
            "function": query_database_tool,
        },
        {
            "name": "call_api",
            "description": "Make HTTP requests to external APIs",
            "function": call_external_api_tool,
        },
    ]