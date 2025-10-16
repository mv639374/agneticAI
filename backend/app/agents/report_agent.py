# agenticAI/backend/app/agents/report_agent.py

"""
Report Agent

Specializes in generating formatted reports and summaries.
"""

from app.agents.base_agent import BaseAgent
from app.utils.prompts import REPORT_AGENT_PROMPT


class ReportAgent(BaseAgent):
    """
    Agent specialized in report generation and formatting.
    
    Capabilities:
    - Create executive summaries
    - Generate detailed reports
    - Format data in Markdown/tables
    - Highlight key insights
    - Structure information clearly
    """
    
    def __init__(self):
        super().__init__(
            name="report_agent",
            system_prompt=REPORT_AGENT_PROMPT,
            tools=[],
            temperature=0.7,  # Higher creativity for engaging report writing
        )