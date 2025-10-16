# agenticAI/backend/app/agents/notification_agent.py

"""
Notification Agent

Specializes in sending alerts and notifications.
Uses the call_api function for webhook delivery.
"""

from langchain_core.tools import StructuredTool

from app.agents.base_agent import BaseAgent
from app.mcp.tools.api_caller import call_api
from app.mcp.schemas import ApiCallInput
from app.utils.prompts import NOTIFICATION_AGENT_PROMPT


class NotificationAgent(BaseAgent):
    """
    Agent specialized in notifications and alerts.
    
    Capabilities:
    - Generate formatted notifications
    - Send alerts to external services
    - Handle different priority levels
    - Track notification delivery
    """
    
    def __init__(self):
        # Wrap async function as LangChain tool
        call_api_tool = StructuredTool.from_function(
            coroutine=call_api,
            name="call_api",
            description="Make HTTP requests to external APIs (webhooks, Slack, etc.). Supports GET, POST, PUT, DELETE, PATCH methods.",
            args_schema=ApiCallInput,
        )
        
        super().__init__(
            name="notification_agent",
            system_prompt=NOTIFICATION_AGENT_PROMPT,
            tools=[call_api_tool],
            temperature=0.5,
        )
