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
    # Skip if we already have an error, coming from cache, or if we should skip database query
    if state.get("error") or state.get("from_cache", False) or state.get("skip_database_query", False):
        # If we're skipping database query due to web search, set empty results
        if state.get("skip_database_query", False):
            logger.info("Skipping database query as requested by previous agent")
            # If we don't already have query results, set empty results
            if "query_results" not in state:
                state["query_results"] = []
        return state

    try:
        # Sanitize and parameterize SQL
        sanitized_sql, params = sanitize_and_parameterize_sql(
            state["generated_sql"],
            state["user_context"]
        )

        # Record start time for performance tracking
        start_time = time.time()

        # Log the sanitized SQL and parameters for debugging
        print(f"\nSQL SANITIZADO PARA EXECUÇÃO:\n{sanitized_sql}\n")
        print(f"PARÂMETROS:\n{params}\n")

        # Execute query
        results = execute_query(
            sanitized_sql,
            params,
            state["user_id"]
        )

        # Log the results for debugging
        print(f"RESULTADOS DA CONSULTA:\n{results}\n")

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
