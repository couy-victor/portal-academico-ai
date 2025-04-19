"""
Cache Agent for the Academic Agent system.
Responsible for checking and updating the cache.
"""
from typing import Dict, Any

from src.models.state import AcademicAgentState
from src.utils.cache import get_cache_key, get_cache, set_cache
from src.utils.logging import logger

def cache_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Checks if there is a cached response for the query.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with cache information
    """
    # Skip cache for certain intents that need real-time data
    real_time_intents = ["presenca_hoje", "notas_recentes", "avisos_novos"]
    
    # We don't know the intent yet, but we can check if the query contains keywords
    query_lower = state["user_query"].lower()
    skip_cache_keywords = ["hoje", "agora", "atual", "recente", "último", "nova"]
    
    should_skip_cache = any(keyword in query_lower for keyword in skip_cache_keywords)
    
    if should_skip_cache:
        state["from_cache"] = False
        return state
    
    # Generate cache key
    cache_key = get_cache_key(state["user_query"], state["user_context"])
    
    # Check cache
    cached_data = get_cache(cache_key)
    
    if cached_data:
        # Update state with cached data
        state.update({
            "query_results": cached_data.get("query_results", []),
            "natural_response": cached_data.get("natural_response", ""),
            "from_cache": True
        })
        
        # Add metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["cache_hit"] = True
        
        logger.info(f"Cache hit for query: {state['user_query'][:50]}...")
    else:
        # No cache hit
        state["from_cache"] = False
        
        # Add metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["cache_hit"] = False
        
        logger.info(f"Cache miss for query: {state['user_query'][:50]}...")
    
    return state

def update_cache(state: AcademicAgentState) -> AcademicAgentState:
    """
    Updates the cache with the current response.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Unchanged state
    """
    # Don't update cache if there was an error or we're already from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    # Skip cache for real-time intents
    real_time_intents = ["presenca_hoje", "notas_recentes", "avisos_novos"]
    if state.get("intent") in real_time_intents:
        return state
    
    # Generate cache key
    cache_key = get_cache_key(state["user_query"], state["user_context"])
    
    # Prepare data for cache
    cache_data = {
        "query_results": state.get("query_results", []),
        "natural_response": state.get("natural_response", ""),
        "intent": state.get("intent", "unknown")
    }
    
    # Update cache
    set_cache(cache_key, cache_data)
    
    logger.info(f"Updated cache for query: {state['user_query'][:50]}...")
    
    return state
