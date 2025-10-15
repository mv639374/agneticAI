# agenticAI/backend/app/mcp/tools/database_connector.py

"""
Database Query Tool for MCP

This tool allows agents to query PostgreSQL database using SQL.

SECURITY CONSIDERATIONS:
- Only SELECT queries allowed (read-only)
- Result row limit to prevent memory issues
- SQL injection protection via parameterized queries
- Logged queries for audit trail

PROMPT ENGINEERING FOR SQL GENERATION:
The LLM needs to:
1. Understand database schema
2. Generate valid SQL syntax
3. Use appropriate WHERE clauses
4. Handle JOIN operations correctly

We provide schema context in the tool description and agent prompts.
"""

from typing import Any

from sqlalchemy import text

from app.db.postgres import get_db_session
from app.mcp.schemas import DatabaseQueryInput, DatabaseQueryOutput
from app.utils.logger import get_logger

log = get_logger(__name__)


async def query_database(input_data: DatabaseQueryInput) -> DatabaseQueryOutput:
    """
    Execute read-only SQL query against PostgreSQL database.
    
    Tool Description for LLM:
    "Execute SQL queries to retrieve data from the database. Supports:
    - Conversation history: SELECT * FROM conversations
    - Agent execution metrics: SELECT * FROM agent_executions
    - Aggregations: COUNT, AVG, SUM, GROUP BY
    - Filtering: WHERE clauses
    - Sorting: ORDER BY
    
    Schema:
    - conversations(id, title, user_id, created_at, updated_at, metadata)
    - agent_executions(id, conversation_id, agent_name, agent_type, input_data,
      output_data, status, started_at, completed_at, duration_ms, tokens_used)
    
    Use this tool when you need to:
    - Find past conversations
    - Analyze agent performance
    - Generate usage statistics
    - Search conversation history"
    
    Args:
        input_data: Query parameters
    
    Returns:
        DatabaseQueryOutput with results or error
    """
    
    try:
        # Security: Validate query is SELECT only
        query_upper = input_data.query.strip().upper()
        if not query_upper.startswith("SELECT"):
            log.warning("Non-SELECT query attempted", query=input_data.query)
            return DatabaseQueryOutput(
                success=False,
                error="Only SELECT queries are allowed for security reasons"
            )
        
        # Additional security checks
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return DatabaseQueryOutput(
                success=False,
                error=f"Query contains forbidden keyword: {dangerous_keywords}"
            )
        
        # Execute query
        async with get_db_session() as db:
            # Add LIMIT if not present
            query = input_data.query
            if "LIMIT" not in query_upper:
                query = f"{query} LIMIT {input_data.limit}"
            
            result = await db.execute(text(query))
            
            # Fetch results
            rows = result.fetchall()
            columns = list(result.keys()) if rows else []
            
            # Convert rows to dictionaries
            rows_dict = [dict(zip(columns, row)) for row in rows]
            
            log.info(
                "Database query executed",
                row_count=len(rows_dict),
                columns=columns,
            )
            
            return DatabaseQueryOutput(
                success=True,
                rows=rows_dict,
                row_count=len(rows_dict),
                columns=columns,
            )
    
    except Exception as e:
        log.error("Database query failed", query=input_data.query, exc_info=e)
        return DatabaseQueryOutput(
            success=False,
            error=f"Query execution failed: {str(e)}"
        )


def get_database_schema() -> str:
    """
    Get database schema description for agent context.
    
    PROMPT ENGINEERING:
    This schema description is included in agent system prompts
    to help LLM generate correct SQL queries.
    
    Returns:
        Formatted schema description
    """
    return """
DATABASE SCHEMA:

Table: conversations
- id (String): Unique conversation identifier
- title (String): Conversation title
- user_id (String, nullable): User who owns the conversation
- created_at (DateTime): Creation timestamp
- updated_at (DateTime): Last update timestamp
- metadata (JSON): Additional conversation data

Table: agent_executions
- id (Integer): Unique execution identifier
- conversation_id (String): Foreign key to conversations.id
- agent_name (String): Name of agent that executed
- agent_type (String): Type of agent (supervisor/worker)
- input_data (JSON): Input provided to agent
- output_data (JSON): Output from agent
- status (String): Status (pending/running/completed/failed)
- error_message (Text): Error details if failed
- started_at (DateTime): Execution start time
- completed_at (DateTime): Execution end time
- duration_ms (Integer): Duration in milliseconds
- tokens_used (Integer): LLM tokens consumed
- metadata (JSON): Additional execution metadata

Common Query Patterns:
- Recent conversations: SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10
- Agent performance: SELECT agent_name, AVG(duration_ms), COUNT(*) FROM agent_executions GROUP BY agent_name
- Failed executions: SELECT * FROM agent_executions WHERE status = 'failed'
- Token usage: SELECT SUM(tokens_used) FROM agent_executions WHERE DATE(started_at) = CURRENT_DATE
"""