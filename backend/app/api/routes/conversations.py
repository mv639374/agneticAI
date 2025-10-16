# agenticAI/backend/app/api/routes/conversations.py

"""
Conversation Management Endpoints

Provides REST API for managing conversation history.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from app.db.models import Conversation, AgentExecution
from app.db.postgres import get_db_session
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================
class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    
    id: str
    title: str
    user_id: Optional[str]
    created_at: str
    updated_at: str
    message_count: int


class ConversationDetail(BaseModel):
    """Detailed conversation with execution history."""
    
    id: str
    title: str
    user_id: Optional[str]
    created_at: str
    updated_at: str
    metadata: Optional[dict]
    executions: list[dict]


# =============================================================================
# ENDPOINTS
# =============================================================================
@router.get(
    "/",
    response_model=list[ConversationSummary],
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="Get list of recent conversations",
)
async def list_conversations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List conversations with pagination.
    
    Args:
        user_id: Optional user ID filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List of conversation summaries
    """
    async with get_db_session() as db:
        # Build query
        query = select(Conversation)
        
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        query = query.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Get execution counts
        summaries = []
        for conv in conversations:
            count_query = select(AgentExecution).where(
                AgentExecution.conversation_id == conv.id
            )
            count_result = await db.execute(count_query)
            execution_count = len(count_result.scalars().all())
            
            summaries.append(
                ConversationSummary(
                    id=conv.id,
                    title=conv.title,
                    user_id=conv.user_id,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                    message_count=execution_count,
                )
            )
        
        log.info(
            "Listed conversations",
            count=len(summaries),
            user_id=user_id,
        )
        
        return summaries


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details",
    description="Get detailed conversation with execution history",
)
async def get_conversation(conversation_id: str):
    """
    Get conversation details.
    
    Args:
        conversation_id: Conversation identifier
    
    Returns:
        Detailed conversation information
    
    Raises:
        HTTPException: If conversation not found
    """
    async with get_db_session() as db:
        # Get conversation
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
        
        # Get executions
        exec_query = select(AgentExecution).where(
            AgentExecution.conversation_id == conversation_id
        ).order_by(AgentExecution.started_at)
        exec_result = await db.execute(exec_query)
        executions = exec_result.scalars().all()
        
        # Format executions
        execution_list = [
            {
                "id": exec.id,
                "agent_name": exec.agent_name,
                "agent_type": exec.agent_type,
                "status": exec.status,
                "started_at": exec.started_at.isoformat(),
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "duration_ms": exec.duration_ms,
                "tokens_used": exec.tokens_used,
            }
            for exec in executions
        ]
        
        log.info(
            "Retrieved conversation",
            conversation_id=conversation_id,
            execution_count=len(execution_list),
        )
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            metadata=conversation.metadata,
            executions=execution_list,
        )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation and all associated data",
)
async def delete_conversation(conversation_id: str):
    """
    Delete conversation.
    
    Args:
        conversation_id: Conversation identifier
    
    Raises:
        HTTPException: If conversation not found
    """
    async with get_db_session() as db:
        # Get conversation
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
        
        # Delete (cascade will delete executions)
        await db.delete(conversation)
        await db.commit()
        
        log.info("Deleted conversation", conversation_id=conversation_id)