# agenticAI/backend/app/agents/data_ingestion_agent.py

"""
Data Ingestion Agent

Specializes in reading and processing files of various formats.
Uses the read_file function from MCP server.
"""

from langchain_core.tools import StructuredTool

from app.agents.base_agent import BaseAgent
from app.mcp.tools.file_reader import read_file
from app.mcp.schemas import FileReadInput
from app.utils.prompts import DATA_INGESTION_AGENT_PROMPT


class DataIngestionAgent(BaseAgent):
    """
    Agent specialized in file reading and data extraction.
    
    Capabilities:
    - Read text, JSON, CSV, PDF, Markdown files
    - Extract structured data
    - Summarize file contents
    - Handle large files efficiently
    """
    
    def __init__(self):
        # Wrap async function as LangChain tool
        read_file_tool = StructuredTool.from_function(
            coroutine=read_file,
            name="read_file",
            description="Read and parse files (text, JSON, CSV, PDF, Markdown). Returns file contents with metadata.",
            args_schema=FileReadInput,
        )
        
        super().__init__(
            name="data_ingestion_agent",
            system_prompt=DATA_INGESTION_AGENT_PROMPT,
            tools=[read_file_tool],
            temperature=0.2,
        )
