# agenticAI/backend/app/agents/analysis_agent.py

"""
Analysis Agent

Specializes in data analysis, calculations, and statistical processing.
"""

from app.agents.base_agent import BaseAgent
from app.utils.prompts import ANALYSIS_AGENT_PROMPT


class AnalysisAgent(BaseAgent):
    """
    Agent specialized in data analysis and calculations.
    
    Capabilities:
    - Statistical analysis (mean, median, std dev)
    - Mathematical calculations
    - Data aggregations
    - Trend analysis
    - Pattern recognition
    """
    
    def __init__(self):
        # Analysis agent uses LLM's built-in calculation capabilities
        # No external tools needed for Phase 1
        super().__init__(
            name="analysis_agent",
            system_prompt=ANALYSIS_AGENT_PROMPT,
            tools=[],
            temperature=0.3,  # Moderate for balanced analytical reasoning
        )