# # agenticAI/backend/app/graphs/supervisor_graph.py

"""
Optimized Supervisor Workflow with Intelligent Routing

KEY IMPROVEMENTS:
1. Supervisor tries to answer simple questions directly
2. Only delegates when necessary
3. Strict iteration limits (max 2 agent calls)
4. Better error handling with user-friendly messages
"""

import uuid
from typing import Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph

from app.agents.analysis_agent import AnalysisAgent
from app.agents.data_ingestion_agent import DataIngestionAgent
from app.agents.notification_agent import NotificationAgent
from app.agents.query_agent import QueryAgent
from app.agents.report_agent import ReportAgent
from app.agents.supervisor import SupervisorAgent
from app.config import settings
from app.graphs.state import AgentState
from app.utils.logger import get_logger

log = get_logger(__name__)

# Initialize agents
supervisor = SupervisorAgent()
data_ingestion_agent = DataIngestionAgent()
analysis_agent = AnalysisAgent()
query_agent = QueryAgent()
report_agent = ReportAgent()
notification_agent = NotificationAgent()


# =============================================================================
# SUPERVISOR NODE WITH INTELLIGENT ROUTING
# =============================================================================
async def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor decides: answer directly or delegate?
    """
    log.info("Supervisor analyzing request")
    
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Check if we've already executed agents
    execution_count = state.get("execution_count", 0)
    
    # If this is a return from a worker agent, finish
    current_agent = state.get("current_agent")
    if current_agent and current_agent != "supervisor":
        log.info("Received response from worker, finishing")
        state["next_agent"] = END
        return state
    
    # Make routing decision
    try:
        decision = await supervisor.make_routing_decision(
            user_message=last_message,
            conversation_history=messages[:-1] if len(messages) > 1 else None
        )
        
        log.info(
            "Routing decision made",
            can_answer_directly=decision.can_answer_directly,
            delegate_to=decision.delegate_to
        )
        
        # If can answer directly
        if decision.can_answer_directly and decision.direct_answer:
            # Add supervisor's answer to messages
            answer_message = AIMessage(
                content=decision.direct_answer,
                name="supervisor"
            )
            state["messages"].append(answer_message)
            state["next_agent"] = END
            state["current_agent"] = "supervisor"
            
            log.info("Supervisor answered directly")
            return state
        
        # Otherwise delegate
        state["next_agent"] = decision.delegate_to
        state["current_agent"] = "supervisor"
        state["execution_count"] = execution_count + 1
        
        return state
        
    except Exception as e:
        log.error(f"Supervisor decision failed: {e}", exc_info=True)
        
        # Fallback: delegate to analysis agent
        state["next_agent"] = "analysis_agent"
        state["execution_count"] = execution_count + 1
        return state


# =============================================================================
# WORKER AGENT NODES (Simplified)
# =============================================================================
async def analysis_node(state: AgentState) -> AgentState:
    """Analysis agent execution."""
    log.info("Analysis agent executing")
    
    messages = state["messages"]
    task = messages[-1].content if messages else ""
    
    result = await analysis_agent.execute(task)
    
    output_message = AIMessage(
        content=result["output"] if result["success"] else f"Error: {result.get('error')}",
        name="analysis_agent"
    )
    
    state["messages"].append(output_message)
    state["current_agent"] = "analysis_agent"
    state["next_agent"] = END  # Always end after worker completes
    
    return state


async def data_ingestion_node(state: AgentState) -> AgentState:
    """Data ingestion agent execution."""
    log.info("Data ingestion agent executing")
    
    messages = state["messages"]
    task = messages[-1].content if messages else ""
    
    result = await data_ingestion_agent.execute(task)
    
    output_message = AIMessage(
        content=result["output"] if result["success"] else f"Error: {result.get('error')}",
        name="data_ingestion_agent"
    )
    
    state["messages"].append(output_message)
    state["current_agent"] = "data_ingestion_agent"
    state["next_agent"] = END
    
    return state


async def query_node(state: AgentState) -> AgentState:
    """Query agent execution."""
    log.info("Query agent executing")
    
    messages = state["messages"]
    task = messages[-1].content if messages else ""
    
    result = await query_agent.execute(task)
    
    output_message = AIMessage(
        content=result["output"] if result["success"] else f"Error: {result.get('error')}",
        name="query_agent"
    )
    
    state["messages"].append(output_message)
    state["current_agent"] = "query_agent"
    state["next_agent"] = END
    
    return state


# =============================================================================
# ROUTING FUNCTION
# =============================================================================
def router(
    state: AgentState,
) -> Literal["data_ingestion_agent", "analysis_agent", "query_agent", END]:
    """Route based on supervisor decision."""
    
    next_agent = state.get("next_agent", END)
    execution_count = state.get("execution_count", 0)
    
    # Safety: max 3 iterations total
    if execution_count >= 3:
        log.warning("Max iterations reached")
        return END
    
    # Check valid agent names
    valid_agents = ["data_ingestion_agent", "analysis_agent", "query_agent"]
    
    if next_agent == END or next_agent == "FINISH" or next_agent not in valid_agents:
        return END
    
    log.info(f"Routing to {next_agent}")
    return next_agent


# =============================================================================
# BUILD WORKFLOW
# =============================================================================
def create_supervisor_workflow() -> StateGraph:
    """Create optimized workflow graph."""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("analysis_agent", analysis_node)
    workflow.add_node("data_ingestion_agent", data_ingestion_node)
    workflow.add_node("query_agent", query_node)
    
    # Start with supervisor
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes to agents or END
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "analysis_agent": "analysis_agent",
            "data_ingestion_agent": "data_ingestion_agent",
            "query_agent": "query_agent",
            END: END,
        },
    )
    
    # All agents end immediately (no loops)
    workflow.add_edge("analysis_agent", END)
    workflow.add_edge("data_ingestion_agent", END)
    workflow.add_edge("query_agent", END)
    
    log.info("Optimized workflow graph created")
    
    return workflow


# =============================================================================
# CHECKPOINTER SETUP
# =============================================================================
_checkpointer_cm = None
_checkpointer_instance = None


def convert_database_url_for_psycopg(url: str) -> str:
    """Convert SQLAlchemy URL to psycopg format."""
    url = url.replace('+asyncpg', '')
    url = url.replace('?ssl=require', '?sslmode=require')
    return url


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get or create checkpointer."""
    global _checkpointer_cm, _checkpointer_instance
    
    if _checkpointer_instance is not None:
        try:
            conn = _checkpointer_instance.conn
            if conn and not conn.closed:
                return _checkpointer_instance
        except:
            pass
    
    psycopg_url = convert_database_url_for_psycopg(settings.DATABASE_URL)
    _checkpointer_cm = AsyncPostgresSaver.from_conn_string(psycopg_url)
    _checkpointer_instance = await _checkpointer_cm.__aenter__()
    await _checkpointer_instance.setup()
    
    log.info("Checkpointer initialized")
    
    return _checkpointer_instance


async def get_supervisor_graph():
    """Get compiled graph with checkpointing."""
    workflow = create_supervisor_workflow()
    checkpointer = await get_checkpointer()
    graph = workflow.compile(checkpointer=checkpointer)
    return graph


# =============================================================================
# MAIN EXECUTION FUNCTION WITH ROBUST ERROR HANDLING
# =============================================================================
async def execute_agent_workflow(
    user_message: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """
    Execute workflow with intelligent routing and error handling.
    """
    from app.graphs.state import create_initial_state
    import traceback
    
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    initial_state = create_initial_state(
        user_message=user_message,
        conversation_id=conversation_id,
        user_id=user_id,
    )
    
    try:
        graph = await get_supervisor_graph()
        config = {"configurable": {"thread_id": conversation_id}}
        
        log.info("Executing workflow", conversation_id=conversation_id)
        
        final_state = await graph.ainvoke(initial_state, config)
        
        messages = final_state.get("messages", [])
        
        # Validate response
        if not messages or len(messages) <= 1:
            return {
                "success": False,
                "conversation_id": conversation_id,
                "response": "⚠️ I couldn't generate a response. Please try rephrasing your question.",
                "messages": [],
                "metadata": {},
            }
        
        final_message = messages[-1].content
        
        # Check for empty or error responses
        if not final_message or final_message.strip() == "":
            return {
                "success": False,
                "conversation_id": conversation_id,
                "response": "⚠️ I encountered an issue. Please try again or contact support.",
                "messages": [{"role": getattr(m, 'type', 'assistant'), "content": m.content} for m in messages],
                "metadata": {},
            }
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "response": final_message,
            "messages": [{"role": getattr(m, 'type', 'assistant'), "content": m.content} for m in messages],
            "metadata": final_state.get("metadata", {}),
        }
    
    except Exception as e:
        error_msg = str(e)
        
        # User-friendly error messages
        if "429" in error_msg or "rate_limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            user_error = "⚠️ **API Rate Limit Reached**\n\nPlease wait a moment and try again. Our system is temporarily at capacity."
        elif "timeout" in error_msg.lower():
            user_error = "⏱️ **Request Timed Out**\n\nThe request took too long. Please try a simpler question or try again."
        elif "connection" in error_msg.lower():
            user_error = "🔌 **Connection Error**\n\nCouldn't connect to required services. Please check your connection and try again."
        else:
            user_error = f"❌ **Error Occurred**\n\n{error_msg[:150]}"
        
        log.error(
            "Workflow execution failed",
            conversation_id=conversation_id,
            error=error_msg,
            traceback=traceback.format_exc()
        )
        
        return {
            "success": False,
            "conversation_id": conversation_id,
            "response": user_error,
            "error": error_msg,
            "messages": [],
            "metadata": {},
        }


async def close_checkpointer():
    """Close checkpointer connection."""
    global _checkpointer_cm, _checkpointer_instance
    
    if _checkpointer_cm and _checkpointer_instance:
        await _checkpointer_cm.__aexit__(None, None, None)
        _checkpointer_cm = None
        _checkpointer_instance = None
