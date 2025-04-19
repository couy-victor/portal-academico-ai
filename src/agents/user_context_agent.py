"""
User Context Agent for the Academic Agent system.
Responsible for retrieving and enriching user context information.
"""
from typing import Dict, Any

from src.models.state import AcademicAgentState
from src.database.supabase_client import supabase
from src.utils.logging import logger

def user_context_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Retrieves and enriches user context information.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with enriched user context
    """
    # Skip if we already have an error
    if state.get("error"):
        return state

    try:
        # Get user ID from state
        user_id = state["user_id"]

        # Check if we already have complete context
        if state.get("user_context", {}).get("complete", False):
            return state

        # Initialize user context if not present
        if "user_context" not in state:
            state["user_context"] = {}

        # Add user_id to context if not present
        if "user_id" not in state["user_context"]:
            state["user_context"]["user_id"] = user_id

        # Check if we have RA in the context and map it to matricula if needed
        if "RA" in state["user_context"] and "matricula" not in state["user_context"]:
            state["user_context"]["matricula"] = state["user_context"]["RA"]
            logger.info(f"Mapped RA to matricula: {state['user_context']['RA']}")

        # Try to fetch additional user context from database
        try:
            # This assumes you have a 'get_user_context' function in Supabase
            response = supabase.rpc(
                'get_user_context',
                {"user_id": user_id}
            ).execute()

            if hasattr(response, 'error') and response.error:
                raise Exception(f"Error fetching user context: {response.error.message}")

            # Extract user context
            user_context = response.data

            if user_context:
                # Update state with user context
                state["user_context"].update(user_context)

                # Mark context as complete
                state["user_context"]["complete"] = True

                logger.info(f"Retrieved user context for user {user_id}")
            else:
                # No user context found from database, but we might have context from the request
                logger.warning(f"No user context found in database for user {user_id}, using provided context")

                # Set default context values if not already present
                if "periodo_atual" not in state["user_context"]:
                    state["user_context"]["periodo_atual"] = "2023.2"  # Default to current period

                # Mark as complete since we're using the provided context
                state["user_context"]["complete"] = True
        except Exception as db_error:
            # Error fetching from database, but we can continue with provided context
            logger.warning(f"Error fetching user context from database: {str(db_error)}. Using provided context.")

            # Set default context values if not already present
            if "periodo_atual" not in state["user_context"]:
                state["user_context"]["periodo_atual"] = "2023.2"  # Default to current period

            # Mark as complete since we're using the provided context
            state["user_context"]["complete"] = True

    except Exception as e:
        error_msg = f"Error retrieving user context: {str(e)}"
        logger.error(error_msg)

        # Don't fail the entire flow for context issues
        # Just log the error and continue with limited context
        if "user_context" not in state:
            state["user_context"] = {}

        state["user_context"]["error"] = error_msg
        state["user_context"]["complete"] = False

    return state
