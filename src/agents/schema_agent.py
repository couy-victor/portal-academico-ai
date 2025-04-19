"""
Schema Retriever Agent for the Academic Agent system.
Responsible for retrieving database schema information.
"""
from typing import Dict, Any

from src.models.state import AcademicAgentState
from src.database.supabase_client import get_schema_info
from src.utils.logging import logger

def schema_retriever(state: AcademicAgentState) -> AcademicAgentState:
    """
    Retrieves database schema information to guide SQL generation.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with schema information
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    try:
        # Get schema information from Supabase
        schema_info = get_schema_info()
        
        # Update state with schema information
        state["schema_info"] = schema_info
        
        # Log success
        logger.info(f"Retrieved schema information with {len(schema_info.get('tables', []))} tables")
        
    except Exception as e:
        error_msg = f"Error retrieving schema information: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
    
    return state
