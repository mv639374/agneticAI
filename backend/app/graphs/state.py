# agenticAI/backend/app/graphs/state.py

"""
LangGraph State Definitions

This module defines the state structure for the multi-agent workflow.

State in LangGraph:
- TypedDict defines the shape of data flowing through the graph
- Annotated fields specify how state updates are merged
- Messages accumulate (add_messages), other fields replace

DESIGN PRINCIPLES:
1. Keep state minimal - only what's needed across agents
2. Use messages for conversation history
3. Store metadata for debugging and monitoring
4. Enable checkpointing for conversation persistence
"""

from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State structure for the multi-agent system.
    
    This state flows through the LangGraph workflow and is accessible
    to all agents and nodes.
    
    PROMPT ENGINEERING NOTE:
    Messages are the primary way agents communicate. Each agent:
    1. Reads previous messages for context
    2. Executes its task
    3. Adds its output as a new message
    4. Supervisor reads all messages to make routing decisions
    
    Attributes:
        messages: Conversation history (accumulated with add_messages)
        next_agent: Which agent should execute next
        current_agent: Currently executing agent
        conversation_id: ID for conversation persistence
        user_id: User who initiated the conversation
        metadata: Additional context and execution metadata
    """
    
    # Messages accumulate (don't replace)
    # add_messages handles appending, deduplication, and ordering
    messages: Annotated[list, add_messages]
    
    # Routing information (replaces on each update)
    next_agent: Optional[str]
    current_agent: Optional[str]
    
    # Conversation tracking
    conversation_id: Optional[str]
    user_id: Optional[str]
    
    # Execution metadata
    metadata: dict
    
    # Agent execution tracking
    execution_count: int
    max_iterations: int


class SupervisorState(TypedDict):
    """
    Extended state for supervisor-specific information.
    
    Used when supervisor needs to make complex routing decisions
    or track multi-step delegations.
    """
    messages: Annotated[list, add_messages]
    next_agent: str
    task_queue: list[str]  # Queue of pending tasks
    completed_agents: list[str]  # Agents that have already executed
    metadata: dict


def create_initial_state(
    user_message: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AgentState:
    """
    Create initial state for a new conversation.
    
    Args:
        user_message: User's initial message
        conversation_id: Optional conversation ID for resuming
        user_id: Optional user identifier
    
    Returns:
        Initialized AgentState
    """
    from langchain_core.messages import HumanMessage
    
    return AgentState(
        messages=[HumanMessage(content=user_message)],
        next_agent="supervisor",  # Always start with supervisor
        current_agent=None,
        conversation_id=conversation_id,
        user_id=user_id,
        metadata={
            "started_at": None,  # Will be set by workflow
            "status": "initiated",
        },
        execution_count=0,
        max_iterations=10,  # Prevent infinite loops
    )