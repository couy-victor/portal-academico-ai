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
        # ✅ VERSÃO CORRETA: Cliente simples
        langsmith_client = Client(api_key=LANGSMITH_API_KEY)
        logger.info(f"LangSmith client initialized for project: {LANGSMITH_PROJECT}")
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
            logger.info(f"🔍 Enviando para LangSmith projeto: {LANGSMITH_PROJECT}")
            
            # ✅ VERSÃO CORRETA: Usar create_run em vez de log_feedback
            result = langsmith_client.create_run(
                name="academic_agent_interaction",
                run_type="chain",
                project_name=LANGSMITH_PROJECT,
                inputs={
                    "user_query": state.get("user_query", ""),
                    "user_id": state.get("user_id", "unknown"),
                    "intent": state.get("intent", "unknown")
                },
                outputs={
                    "response": state.get("natural_response", ""),
                    "confidence": state.get("confidence", 0.0),
                    "from_cache": state.get("from_cache", False)
                },
                extra={
                    "metadata": {
                        "timestamp": log_data["timestamp"],
                        "run_id": run_id,
                        "has_error": bool(state.get("error"))
                    }
                },
                tags=["academic-agent", "interaction"]
            )
            logger.info(f"✅ Sucesso! Run ID: {result}")
            
        except Exception as e:
            logger.error(f"❌ Erro LangSmith: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    else:
        logger.info(f"🚫 LangSmith desabilitado: TRACING={TRACING_ENABLED}, client={langsmith_client is not None}")
    
    return run_id
