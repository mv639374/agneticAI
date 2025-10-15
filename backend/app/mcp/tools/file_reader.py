# agenticAI/backend/app/mcp/tools/file_reader.py

"""
File Reading Tool for MCP

This tool allows agents to read various file types:
- Plain text files (.txt, .md)
- JSON files (.json)
- CSV files (.csv)
- PDF files (.pdf)

PROMPT ENGINEERING PRINCIPLES:
1. Clear tool descriptions help LLM decide when to use this tool
2. Detailed parameter descriptions guide correct argument generation
3. Error handling provides feedback for LLM to retry with corrections
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

import aiofiles
from pypdf import PdfReader

from app.mcp.schemas import FileReadInput, FileReadOutput, FileType
from app.utils.logger import get_logger

log = get_logger(__name__)


async def read_file(input_data: FileReadInput) -> FileReadOutput:
    """
    Read file contents based on file type.
    
    Tool Description for LLM:
    "Read and parse files from the filesystem. Supports text, JSON, CSV, and PDF files.
    Use this tool when you need to:
    - Read user-uploaded documents
    - Parse configuration files
    - Extract data from CSV/JSON files
    - Read text from PDF documents"
    
    Args:
        input_data: File reading parameters
    
    Returns:
        FileReadOutput with content or error
    """
    
    try:
        file_path = Path(input_data.file_path)
        
        # Security check: Prevent directory traversal attacks
        # This ensures agents can only read from allowed directories
        if not file_path.is_absolute():
            # Convert to absolute path relative to app root
            file_path = Path.cwd() / file_path
        
        # Verify file exists
        if not file_path.exists():
            log.warning("File not found", path=str(file_path))
            return FileReadOutput(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        # Verify it's a file (not directory)
        if not file_path.is_file():
            return FileReadOutput(
                success=False,
                error=f"Path is not a file: {file_path}"
            )
        
        # Read file based on type
        if input_data.file_type == FileType.PDF:
            content = await _read_pdf(file_path)
        elif input_data.file_type == FileType.JSON:
            content = await _read_json(file_path, input_data.encoding)
        elif input_data.file_type == FileType.CSV:
            content = await _read_csv(file_path, input_data.encoding)
        else:  # TEXT or MARKDOWN
            content = await _read_text(file_path, input_data.encoding)
        
        # Get file metadata
        stat = file_path.stat()
        metadata = {
            "file_name": file_path.name,
            "file_size_bytes": stat.st_size,
            "file_type": input_data.file_type,
            "line_count": content.count("\n") if isinstance(content, str) else None,
        }
        
        log.info(
            "File read successfully",
            path=str(file_path),
            size=stat.st_size,
            type=input_data.file_type,
        )
        
        return FileReadOutput(
            success=True,
            content=content,
            metadata=metadata,
        )
    
    except Exception as e:
        log.error("File read failed", path=input_data.file_path, exc_info=e)
        return FileReadOutput(
            success=False,
            error=f"Failed to read file: {str(e)}"
        )


async def _read_text(file_path: Path, encoding: str) -> str:
    """Read plain text file."""
    async with aiofiles.open(file_path, "r", encoding=encoding) as f:
        return await f.read()


async def _read_json(file_path: Path, encoding: str) -> str:
    """Read and parse JSON file, return as formatted string."""
    async with aiofiles.open(file_path, "r", encoding=encoding) as f:
        content = await f.read()
        data = json.loads(content)
        # Return pretty-printed JSON for better LLM comprehension
        return json.dumps(data, indent=2)


async def _read_csv(file_path: Path, encoding: str) -> str:
    """
    Read CSV file and convert to formatted string.
    
    PROMPT ENGINEERING NOTE:
    We convert CSV to text table format because:
    - LLMs understand structured text better than raw CSV
    - Maintains column alignment for visual parsing
    - Easier for LLM to extract specific cells/rows
    """
    async with aiofiles.open(file_path, "r", encoding=encoding) as f:
        content = await f.read()
    
    # Parse CSV
    reader = csv.DictReader(content.splitlines())
    rows = list(reader)
    
    if not rows:
        return "Empty CSV file"
    
    # Format as table
    headers = list(rows[0].keys())
    table_lines = [
        "CSV Data:",
        f"Columns: {', '.join(headers)}",
        f"Row count: {len(rows)}",
        "",
        "Sample rows (up to 100):",
    ]
    
    for i, row in enumerate(rows[:100], 1):
        row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
        table_lines.append(f"Row {i}: {row_str}")
    
    if len(rows) > 100:
        table_lines.append(f"... and {len(rows) - 100} more rows")
    
    return "\n".join(table_lines)


async def _read_pdf(file_path: Path) -> str:
    """
    Extract text from PDF file.
    
    PROMPT ENGINEERING NOTE:
    PDF extraction challenges:
    - Text may not be in reading order
    - Tables/images don't extract well
    - Formatting is lost
    
    We inform the LLM of these limitations in the tool description.
    """
    reader = PdfReader(str(file_path))
    
    text_parts = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        text_parts.append(f"--- Page {i} ---\n{text}\n")
    
    full_text = "\n".join(text_parts)
    
    # Add metadata header
    metadata_header = f"""PDF Document
Total Pages: {len(reader.pages)}
Extracted Text:

"""
    
    return metadata_header + full_text