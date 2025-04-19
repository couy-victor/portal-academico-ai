"""
Executor Agent for the Academic Agent system.
Responsible for executing SQL queries on the database.
"""
import time
from typing import Dict, Any, List

from src.models.state import AcademicAgentState
from src.database.supabase_client import sanitize_and_parameterize_sql, execute_query
from src.utils.logging import logger

def executor_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Executes the validated SQL query on the database.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with query results
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    try:
        # Sanitize and parameterize SQL
        sanitized_sql, params = sanitize_and_parameterize_sql(
            state["generated_sql"], 
            state["user_context"]
        )
        
        # Record start time for performance tracking
        start_time = time.time()
        
        # Execute query
        results = execute_query(
            sanitized_sql,
            params,
            state["user_id"]
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update state with query results
        state["query_results"] = results
        
        # Store execution metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["query_execution_time"] = execution_time
        state["metadata"]["rows_returned"] = len(results)
        
        # Log success
        logger.info(f"Query executed successfully. Returned {len(results)} rows in {execution_time:.2f}s")
        
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
    
    return state
