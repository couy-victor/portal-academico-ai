"""
Logging utilities for the Academic Agent system.
"""
import os
import json
import logging
import datetime
import uuid
from typing import Dict, Any, Optional

from langsmith import Client
from src.config.settings import LOG_LEVEL, TRACING_ENABLED, LANGSMITH_API_KEY, LANGSMITH_PROJECT

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("academic_agent")

# Initialize LangSmith client if enabled
langsmith_client = None
if TRACING_ENABLED and LANGSMITH_API_KEY:
    try:
        langsmith_client = Client(
            api_key=LANGSMITH_API_KEY,
            project_name=LANGSMITH_PROJECT
        )
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith client: {str(e)}")

def log_interaction(state: Dict[str, Any], run_id: Optional[str] = None) -> str:
    """
    Logs an interaction to both local logs and LangSmith if enabled.
    
    Args:
        state (Dict[str, Any]): The current state
        run_id (Optional[str]): Existing run ID for updates
        
    Returns:
        str: The run ID
    """
    # Generate a new run ID if not provided
    if not run_id:
        run_id = str(uuid.uuid4())
    
    # Extract key information for logging
    log_data = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": state.get("user_id", "unknown"),
        "user_query": state.get("user_query", ""),
        "intent": state.get("intent", "unknown"),
        "confidence": state.get("confidence", 0.0),
        "error": state.get("error"),
        "from_cache": state.get("from_cache", False),
        "response": state.get("natural_response", "")
    }
    
    # Log locally
    if state.get("error"):
        logger.error(f"Interaction {run_id}: Error - {state['error']}")
    else:
        logger.info(f"Interaction {run_id}: {state.get('user_query', '')} -> {state.get('intent', 'unknown')}")
    
    # Log to LangSmith if enabled
    if TRACING_ENABLED and langsmith_client:
        try:
            # For simplicity, we're just logging the state
            # In a real implementation, you would use the proper tracing API
            langsmith_client.log_feedback(
                run_id=run_id,
                key="state_snapshot",
                value=json.dumps(log_data),
                comment="State snapshot"
            )
        except Exception as e:
            logger.error(f"Failed to log to LangSmith: {str(e)}")
    
    return run_id
