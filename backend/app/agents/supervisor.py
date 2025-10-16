# agenticAI/backend/app/agents/supervisor.py

"""
Supervisor Agent with Intelligent Routing

STRATEGY:
1. Try to answer simple questions directly (one LLM call)
2. Only delegate complex tasks to specialist agents
3. Avoid infinite loops with strict iteration limits
"""

from typing import Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.logger import get_logger
from app.utils.prompts import SUPERVISOR_SYSTEM_PROMPT

log = get_logger(__name__)

# Worker agent names
WORKER_AGENTS = [
    "data_ingestion_agent",
    "analysis_agent", 
    "query_agent",
    "report_agent",
    "notification_agent",
]


class RoutingDecision(BaseModel):
    """Structured routing decision from supervisor."""
    
    can_answer_directly: bool = Field(
        description="Whether supervisor can answer without delegating"
    )
    
    direct_answer: Optional[str] = Field(
        default=None,
        description="Direct answer if can_answer_directly is True"
    )
    
    delegate_to: Optional[str] = Field(
        default=None,
        description="Agent to delegate to, or 'FINISH' if done"
    )
    
    reasoning: str = Field(
        description="Explanation of the decision"
    )


# Updated supervisor prompt for intelligent routing
INTELLIGENT_SUPERVISOR_PROMPT = """You are an **Intelligent Supervisor** in a multi-agent system.

**YOUR STRATEGY:**

1. **Try to answer directly** if the question is:
   - Simple calculation (2+2, percentages, averages)
   - General knowledge (What is X?, Who is Y?, When did Z happen?)
   - Simple definitions or explanations
   - Basic reasoning or comparisons

2. **Delegate to specialists** only if the question requires:
   - File reading (PDF, CSV, JSON) → data_ingestion_agent
   - Database queries (past conversations, agent metrics) → query_agent
   - Complex data analysis with multiple steps → analysis_agent
   - Report generation with specific formatting → report_agent
   - External notifications or alerts → notification_agent

3. **ALWAYS prefer direct answers** when possible to be efficient.

**EXAMPLES:**

User: "What is 2+2?"
Decision: Answer directly = "4"

User: "Calculate the average of 10, 20, 30"
Decision: Answer directly = "The average is 20"

User: "Read the file data.csv and analyze sales trends"
Decision: Delegate to data_ingestion_agent (requires file access)

User: "Show me my last 5 conversations"
Decision: Delegate to query_agent (requires database)

User: "What is machine learning?"
Decision: Answer directly (general knowledge)

**OUTPUT FORMAT:**
- can_answer_directly: true/false
- direct_answer: your answer (if answering directly)
- delegate_to: agent name or "FINISH"
- reasoning: why you made this decision
"""


class SupervisorAgent(BaseAgent):
    """
    Intelligent supervisor that answers simple questions directly
    and only delegates complex tasks.
    """
    
    def __init__(self):
        super().__init__(
            name="supervisor",
            system_prompt=INTELLIGENT_SUPERVISOR_PROMPT,
            tools=[],
            temperature=0.0,  # Deterministic decisions
        )
    
    async def make_routing_decision(
        self, 
        user_message: str,
        conversation_history: list = None
    ) -> RoutingDecision:
        """
        Decide whether to answer directly or delegate.
        
        Returns structured decision with reasoning.
        """
        
        # Build prompt
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                messages.append(msg)
        
        # Add current query
        decision_prompt = f"""Analyze this user request and decide:

User request: "{user_message}"

Respond with:
1. can_answer_directly (true/false)
2. direct_answer (if true)
3. delegate_to (agent name if delegating, or "FINISH")
4. reasoning (your explanation)

Remember: Answer directly if it's simple. Only delegate if truly necessary.
"""
        
        messages.append(HumanMessage(content=decision_prompt))
        
        try:
            # Get LLM decision
            response = await self.llm.ainvoke(messages)
            content = response.content
            
            # Parse response (simple parsing - in production use structured output)
            can_answer = "can_answer_directly: true" in content.lower() or \
                        "answer directly" in content.lower() and "yes" in content.lower()
            
            # Extract direct answer if present
            direct_answer = None
            if can_answer:
                # Look for answer in response
                lines = content.split('\n')
                for line in lines:
                    if 'direct_answer' in line.lower() or 'answer:' in line.lower():
                        direct_answer = line.split(':', 1)[-1].strip()
                        break
                
                # If no explicit answer found, use whole response
                if not direct_answer:
                    direct_answer = content
            
            # Determine delegation
            delegate_to = None
            if not can_answer:
                content_lower = content.lower()
                if 'data_ingestion' in content_lower or 'file' in content_lower:
                    delegate_to = 'data_ingestion_agent'
                elif 'query' in content_lower or 'database' in content_lower:
                    delegate_to = 'query_agent'
                elif 'analysis' in content_lower:
                    delegate_to = 'analysis_agent'
                elif 'report' in content_lower:
                    delegate_to = 'report_agent'
                elif 'notif' in content_lower:
                    delegate_to = 'notification_agent'
                else:
                    # Default: try to answer with analysis agent
                    delegate_to = 'analysis_agent'
            
            return RoutingDecision(
                can_answer_directly=can_answer,
                direct_answer=direct_answer,
                delegate_to=delegate_to or "FINISH",
                reasoning=content
            )
            
        except Exception as e:
            log.error(f"Routing decision failed: {e}")
            
            # Fallback: try to answer directly
            try:
                simple_response = await self.execute(user_message)
                return RoutingDecision(
                    can_answer_directly=True,
                    direct_answer=simple_response.get("output", "I couldn't process that request."),
                    delegate_to="FINISH",
                    reasoning="Fallback to direct answer"
                )
            except:
                return RoutingDecision(
                    can_answer_directly=False,
                    direct_answer=None,
                    delegate_to="analysis_agent",
                    reasoning="Fallback to analysis agent"
                )
