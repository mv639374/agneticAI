# agenticAI/backend/app/agents/base_agent.py

"""
Base Agent Class

This provides a foundation for all specialized agents with:
- LLM initialization
- Tool binding
- Common execution patterns
- Error handling
- Logging and telemetry
"""

from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


class BaseAgent:
    """
    Base class for all agents in the multi-agent system.
    
    Provides common functionality:
    - LLM initialization based on provider
    - System prompt management
    - Tool binding
    - Execution wrapper with error handling
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: Optional[list] = None,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (for logging and identification)
            system_prompt: System prompt defining agent behavior
            tools: List of tools available to this agent
            llm_provider: LLM provider (groq/google, defaults to settings)
            model_name: Model to use (defaults to settings)
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = self._initialize_llm(llm_provider, model_name, temperature)
        
        # Bind tools if provided
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)
        
        log.info(
            "Agent initialized",
            agent_name=name,
            llm_provider=llm_provider or settings.DEFAULT_LLM_PROVIDER,
            model=model_name,
            tools_count=len(self.tools),
        )
    
    def _initialize_llm(
        self,
        provider: Optional[str],
        model_name: Optional[str],
        temperature: float,
    ):
        """
        Initialize LLM based on provider.
        
        PROMPT ENGINEERING NOTE:
        - Temperature 0.0: Best for consistent, deterministic outputs (supervisor, query)
        - Temperature 0.3-0.5: Balanced (analysis, data ingestion)
        - Temperature 0.7-1.0: Creative outputs (report generation)
        
        Args:
            provider: LLM provider name
            model_name: Model identifier
            temperature: Sampling temperature
        
        Returns:
            Initialized LLM instance
        """
        provider = provider or settings.DEFAULT_LLM_PROVIDER
        
        if provider == "groq":
            model = model_name or settings.GROQ_MODEL_NAME
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=model,
                temperature=temperature,
                max_tokens=4096,  # Sufficient for most responses
            )
        
        elif provider == "google":
            model = model_name or settings.GOOGLE_MODEL_NAME
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY,
                model=model,
                temperature=temperature,
                max_output_tokens=4096,
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def execute(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        config: Optional[RunnableConfig] = None,
    ) -> dict[str, Any]:
        """
        Execute agent with given message and context.
        
        This is the main entry point for agent invocation.
        
        Args:
            message: User message or task description
            context: Additional context (previous outputs, metadata)
            config: LangChain runnable config (for callbacks, tags)
        
        Returns:
            Agent execution result with output and metadata
        """
        try:
            log.info(
                "Agent execution started",
                agent_name=self.name,
                message_length=len(message),
                has_context=bool(context),
            )
            
            # Build messages for LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=message),
            ]
            
            # Add context if provided
            if context:
                context_str = self._format_context(context)
                messages.append(
                    HumanMessage(content=f"Additional context:\n{context_str}")
                )
            
            # Invoke LLM
            response = await self.llm.ainvoke(messages, config=config)
            
            # Extract output
            output = response.content if hasattr(response, 'content') else str(response)
            
            log.info(
                "Agent execution completed",
                agent_name=self.name,
                output_length=len(output),
            )
            
            return {
                "agent_name": self.name,
                "success": True,
                "output": output,
                "metadata": {
                    "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
                    "temperature": self.temperature,
                },
            }
        
        except Exception as e:
            log.error(
                "Agent execution failed",
                agent_name=self.name,
                exc_info=e,
            )
            
            return {
                "agent_name": self.name,
                "success": False,
                "output": None,
                "error": str(e),
            }
    
    def _format_context(self, context: dict[str, Any]) -> str:
        """
        Format context dictionary into readable string for LLM.
        
        PROMPT ENGINEERING NOTE:
        Context formatting matters for LLM comprehension:
        - Use clear labels and structure
        - Separate sections with newlines
        - Highlight important values
        
        Args:
            context: Context dictionary
        
        Returns:
            Formatted context string
        """
        lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                import json
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            lines.append(f"**{key}:**\n{value_str}")
        
        return "\n\n".join(lines)