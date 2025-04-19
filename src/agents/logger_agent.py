"""
Logger Agent for the Academic Agent system.
Responsible for logging interactions and tracking with LangSmith.
"""
import uuid
from typing import Dict, Any

from src.models.state import AcademicAgentState
from src.utils.logging import log_interaction, logger

def logger_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Logs the interaction and tracks with LangSmith.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Unchanged state
    """
    # Generate run ID if not present
    run_id = state.get("metadata", {}).get("run_id")
    if not run_id:
        run_id = str(uuid.uuid4())
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["run_id"] = run_id
    
    # Log the interaction
    log_interaction(state, run_id)
    
    # Log summary
    if state.get("error"):
        logger.error(f"Interaction {run_id} completed with error: {state['error']}")
    else:
        logger.info(f"Interaction {run_id} completed successfully")
    
    return state
