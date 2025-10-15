# agenticAI/backend/app/db/models.py

"""
SQLAlchemy Models for Database Tables

This module defines:
1. Conversation model - stores user conversations
2. AgentExecution model - stores agent execution history
3. Checkpoint model - LangGraph state checkpoints (handled by langgraph-checkpoint-postgres)

Database Schema Design:
- Conversations: Main conversation threads
- AgentExecutions: Individual agent task executions within conversations
- Relationship: One conversation has many agent executions
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import sqlalchemy

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


# Conversation Model
class Conversation(Base):
    """
    Stores conversation threads between users and the multi-agent system.
    
    Each conversation is a thread where:
    - User submits queries
    - Supervisor delegates to agents
    - Agents execute tasks and return results
    
    Attributes:
        id: Unique conversation identifier (UUID)
        title: Human-readable conversation title
        user_id: User who initiated the conversation (optional for Phase 1)
        created_at: Timestamp when conversation started
        updated_at: Timestamp of last activity
        metadata: Additional context (user preferences, session info, etc.)
        agent_executions: Related agent execution records
    """
    __tablename__ = "conversations"

    # Primary key using UUID for distributed systems compatibility
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Unique conversation identifier"
    )

    # Conversation metadata
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
        comment="Human-readable conversation title"
    )

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="User who owns this conversation (optional in phase 1)",
    )

    # Timestamps with automatic updates
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Conversation creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # JSON metadata for flexible storage
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional conversation context (preferences, tags, etc.)"
    )

    # Relationship: One conversation has many agent executions
    agent_executions: Mapped[list["AgentExecution"]] = relationship(
        "AgentExecution",
        back_populates="conversation",
        cascade="all, delete-orphan", # Delete executions when conversation is deleted
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


# Agent Execution Model
class AgentExecution(Base):
    """
    Stores individual agent task executions within a conversation.
    
    Each execution represents:
    - Which agent was invoked
    - Input provided to the agent
    - Output/result from the agent
    - Execution metadata (duration, tokens used, etc.)
    
    This enables:
    - Conversation history replay
    - Agent performance monitoring
    - Debugging agent behavior
    - Cost tracking (LLM token usage)
    """

    __tablename__ = "agent_executions"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,

        comment="Unique execution indentifier"
    )

    # Foreign key to conversation
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index for faster joins
        comment="Parent conversation ID",
    )

    # Agent information
    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # Index for querying by agent
        comment = "Name of the agent that executed this task"
    )

    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of agent (supervisor, worker, etc.)"
    )

    # Execution data
    input_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Input provided to the agent",
    )

    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Output/result from the agent",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Execution status: pending, running, completed, failed"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if execution failed"
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Execution start time"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Execution completion time"
    )
    
    # Performance metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Execution duration in milliseconds"
    )
    
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of LLM tokens consumed"
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional execution metadata (model used, temperature, etc.)"
    )
    
    # Relationship: Many executions belong to one conversation
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="agent_executions"
    )
    
    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, agent={self.agent_name}, status={self.status})>"



# =============================================================================
# NOTES ON LANGGRAPH CHECKPOINTING
# =============================================================================
"""
LangGraph Checkpointing Tables:

The langgraph-checkpoint-postgres package automatically creates these tables:
1. checkpoints - Stores graph execution state
2. checkpoint_blobs - Stores large binary data (embeddings, etc.)
3. checkpoint_writes - Stores pending writes

These tables enable:
- Agent state persistence across requests
- Conversation memory (agents remember previous interactions)
- Error recovery (resume from last checkpoint)
- Time-travel debugging (inspect state at any point)

We don't need to define these models manually - they're handled by:
    from langgraph.checkpoint.postgres import PostgresSaver
    
    checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
    await checkpointer.setup()  # Creates tables automatically

See implementation in app/graphs/supervisor_graph.py
"""