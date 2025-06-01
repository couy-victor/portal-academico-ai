"""
Base Agent class for the Academic Agent system.
Provides common functionality and interface for all agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import time
import uuid

from src.models.state import AcademicAgentState
from src.utils.logging import logger


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result of agent execution."""
    status: AgentStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides common functionality like:
    - Error handling
    - Logging
    - Execution timing
    - State validation
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base agent.
        
        Args:
            name (str): Agent name
            description (str): Agent description
        """
        self.name = name
        self.description = description
        self.agent_id = str(uuid.uuid4())
        
    def __call__(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Execute the agent with proper error handling and logging.
        
        Args:
            state (AcademicAgentState): Current state
            
        Returns:
            AcademicAgentState: Updated state
        """
        start_time = time.time()
        
        try:
            # Pre-execution validation
            if not self._validate_input(state):
                logger.warning(f"{self.name}: Input validation failed, skipping")
                return self._mark_skipped(state)
            
            # Check if should skip execution
            if self._should_skip(state):
                logger.info(f"{self.name}: Skipping execution based on state")
                return self._mark_skipped(state)
            
            logger.info(f"{self.name}: Starting execution")
            
            # Execute the agent logic
            result_state = self._execute(state)
            
            # Post-execution validation
            if not self._validate_output(result_state):
                logger.error(f"{self.name}: Output validation failed")
                return self._mark_error(state, "Output validation failed")
            
            execution_time = time.time() - start_time
            logger.info(f"{self.name}: Completed successfully in {execution_time:.2f}s")
            
            # Add execution metadata
            self._add_execution_metadata(result_state, AgentStatus.SUCCESS, execution_time)
            
            return result_state
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error in {self.name}: {str(e)}"
            logger.error(error_msg)
            
            # Add error metadata
            error_state = self._mark_error(state, error_msg)
            self._add_execution_metadata(error_state, AgentStatus.ERROR, execution_time, error_msg)
            
            return error_state
    
    @abstractmethod
    def _execute(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Execute the agent's main logic.
        
        Args:
            state (AcademicAgentState): Current state
            
        Returns:
            AcademicAgentState: Updated state
        """
        pass
    
    def _validate_input(self, state: AcademicAgentState) -> bool:
        """
        Validate input state.
        
        Args:
            state (AcademicAgentState): Input state
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        return (
            isinstance(state, dict) and
            "user_query" in state and
            "user_id" in state
        )
    
    def _validate_output(self, state: AcademicAgentState) -> bool:
        """
        Validate output state.
        
        Args:
            state (AcademicAgentState): Output state
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        return isinstance(state, dict)
    
    def _should_skip(self, state: AcademicAgentState) -> bool:
        """
        Determine if agent execution should be skipped.
        
        Args:
            state (AcademicAgentState): Current state
            
        Returns:
            bool: True if should skip, False otherwise
        """
        # Skip if there's already an error or if coming from cache
        return state.get("error") is not None or state.get("from_cache", False)
    
    def _mark_error(self, state: AcademicAgentState, error_msg: str) -> AcademicAgentState:
        """
        Mark state with error.
        
        Args:
            state (AcademicAgentState): Current state
            error_msg (str): Error message
            
        Returns:
            AcademicAgentState: State with error marked
        """
        state["error"] = error_msg
        return state
    
    def _mark_skipped(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Mark agent as skipped.
        
        Args:
            state (AcademicAgentState): Current state
            
        Returns:
            AcademicAgentState: Unchanged state
        """
        return state
    
    def _add_execution_metadata(
        self, 
        state: AcademicAgentState, 
        status: AgentStatus, 
        execution_time: float,
        error: Optional[str] = None
    ) -> None:
        """
        Add execution metadata to state.
        
        Args:
            state (AcademicAgentState): Current state
            status (AgentStatus): Execution status
            execution_time (float): Execution time in seconds
            error (Optional[str]): Error message if any
        """
        if "metadata" not in state:
            state["metadata"] = {}
        
        if "agent_executions" not in state["metadata"]:
            state["metadata"]["agent_executions"] = []
        
        state["metadata"]["agent_executions"].append({
            "agent_name": self.name,
            "agent_id": self.agent_id,
            "status": status.value,
            "execution_time": execution_time,
            "error": error,
            "timestamp": time.time()
        })


class LLMAgent(BaseAgent):
    """
    Base class for agents that use LLM.
    
    Provides common LLM functionality like:
    - Model configuration
    - Prompt management
    - Response parsing
    """
    
    def __init__(self, name: str, description: str = "", model: str = None, temperature: float = None):
        """
        Initialize the LLM agent.
        
        Args:
            name (str): Agent name
            description (str): Agent description
            model (str): LLM model to use
            temperature (float): LLM temperature
        """
        super().__init__(name, description)
        self.model = model
        self.temperature = temperature
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration.
        
        Returns:
            Dict[str, Any]: LLM configuration
        """
        from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
        
        return {
            "model": self.model or LLM_MODEL,
            "temperature": self.temperature or LLM_TEMPERATURE
        }
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        
        Args:
            response_text (str): Raw response text
            
        Returns:
            Dict[str, Any]: Parsed JSON
            
        Raises:
            ValueError: If JSON parsing fails
        """
        import json
        
        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
        else:
            json_str = response_text.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:200]}...")
            raise ValueError(f"Invalid JSON response: {e}")
