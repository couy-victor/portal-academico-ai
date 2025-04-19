"""
DBA Guard Agent for the Academic Agent system.
Responsible for ensuring SQL queries are efficient and secure.
"""
import re
from typing import Dict, Any, List

from src.models.state import AcademicAgentState
from src.utils.logging import logger

def dba_guard(state: AcademicAgentState) -> AcademicAgentState:
    """
    Analyzes and optimizes SQL queries for performance and security.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with optimized SQL
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    try:
        sql = state["generated_sql"]
        original_sql = sql
        
        # Check and add LIMIT if not present
        if "limit" not in sql.lower() and "select" in sql.lower():
            # Don't add LIMIT to COUNT queries
            if not re.search(r"select\s+count\s*\(", sql.lower(), re.IGNORECASE):
                sql = sql.rstrip(";")
                sql += " LIMIT 100;"
        
        # Ensure all queries end with a semicolon
        if not sql.rstrip().endswith(";"):
            sql += ";"
        
        # Prevent SELECT * queries
        if re.search(r"select\s+\*\s+from", sql.lower(), re.IGNORECASE):
            # Log warning but don't modify - the validator should have caught this
            logger.warning("Query contains SELECT * - this should be avoided")
        
        # Check for potential full table scans on large tables
        large_tables = ["notas", "presencas", "matriculas", "historico"]
        for table in large_tables:
            pattern = rf"from\s+{table}(?!\s+where)"
            if re.search(pattern, sql.lower(), re.IGNORECASE):
                logger.warning(f"Query may perform full table scan on large table: {table}")
        
        # Update state with optimized SQL if changes were made
        if sql != original_sql:
            state["generated_sql"] = sql
            logger.info("SQL optimized by DBA Guard")
            
            # Store original SQL in metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["original_sql"] = original_sql
        
    except Exception as e:
        error_msg = f"Error in DBA Guard: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
    
    return state
