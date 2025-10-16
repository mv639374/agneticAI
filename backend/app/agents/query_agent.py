# agenticAI/backend/app/agents/query_agent.py

"""
Query Agent

Specializes in database queries and data retrieval.
Uses the query_database function from MCP server.
"""

from langchain_core.tools import StructuredTool

from app.agents.base_agent import BaseAgent
from app.mcp.tools.database_connector import query_database
from app.mcp.schemas import DatabaseQueryInput
from app.utils.prompts import QUERY_AGENT_PROMPT


class QueryAgent(BaseAgent):
    """
    Agent specialized in SQL query generation and database access.
    
    Capabilities:
    - Generate SQL queries
    - Retrieve conversation history
    - Fetch agent performance metrics
    - Search and filter data
    """
    
    def __init__(self):
        # Wrap async function as LangChain tool
        query_database_tool = StructuredTool.from_function(
            coroutine=query_database,
            name="query_database",
            description="Execute SQL queries on PostgreSQL database. Returns query results with row count and columns.",
            args_schema=DatabaseQueryInput,
        )
        
        super().__init__(
            name="query_agent",
            system_prompt=QUERY_AGENT_PROMPT,
            tools=[query_database_tool],
            temperature=0.0,
        )
