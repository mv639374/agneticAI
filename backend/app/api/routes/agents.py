# agenticAI/backend/app/api/routes/agents.py

"""
Agent Invocation Endpoints with Robust Error Handling
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.graphs.supervisor_graph import execute_agent_workflow
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentInvokeRequest(BaseModel):
    """Request model for agent invocation."""
    
    message: str = Field(
        ...,
        description="User message or task description",
        min_length=1,
        max_length=10000,
    )
    
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID to resume existing conversation",
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for tracking",
    )


class AgentInvokeResponse(BaseModel):
    """Response model for agent invocation."""
    
    success: bool = Field(description="Whether execution succeeded")
    conversation_id: str = Field(description="Conversation identifier")
    response: str = Field(description="Agent's response to the user")
    message_count: int = Field(description="Number of messages in conversation")
    error: Optional[str] = Field(default=None, description="Error message if failed")


@router.post(
    "/invoke",
    response_model=AgentInvokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke multi-agent workflow",
)
async def invoke_agents(request: AgentInvokeRequest):
    """
    Execute multi-agent workflow with intelligent routing.
    
    ALWAYS returns a response (even on error).
    """
    log.info(
        "Agent invocation requested",
        message_length=len(request.message),
        user_id=request.user_id,
    )
    
    try:
        # Execute workflow
        result = await execute_agent_workflow(
            user_message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        
        # Return result (success or failure with message)
        return AgentInvokeResponse(
            success=result["success"],
            conversation_id=result["conversation_id"],
            response=result.get("response", "No response generated"),  # Always have a response
            message_count=len(result.get("messages", [])),
            error=result.get("error"),
        )
    
    except Exception as e:
        # Last resort error handling
        log.error("Unexpected error in agent invocation", exc_info=e)
        
        return AgentInvokeResponse(
            success=False,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            response=f"❌ System error: {str(e)[:200]}",  # Always return something
            message_count=0,
            error=str(e),
        )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Get agent system status",
)
async def agent_status():
    """Get agent system status."""
    from app.graphs.supervisor_graph import (
        supervisor,
        data_ingestion_agent,
        analysis_agent,
        query_agent,
    )
    
    agents = [
        {"name": "supervisor", "status": "ready", "temperature": supervisor.temperature},
        {"name": "data_ingestion_agent", "status": "ready", "temperature": data_ingestion_agent.temperature},
        {"name": "analysis_agent", "status": "ready", "temperature": analysis_agent.temperature},
        {"name": "query_agent", "status": "ready", "temperature": query_agent.temperature},
    ]
    
    return {
        "status": "ready",
        "agent_count": len(agents),
        "agents": agents,
    }
