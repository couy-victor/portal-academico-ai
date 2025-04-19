"""
Academic Agent Graph for the Academic Agent system.
Defines the main graph structure and flow.
"""
from typing import Dict, Any, Callable, List

from langgraph.graph import StateGraph, END, START

from src.models.state import AcademicAgentState
from src.agents.user_context_agent import user_context_agent
from src.agents.cache_agent import cache_agent, update_cache
from src.agents.router_agent import intent_router
from src.agents.schema_agent import schema_retriever
from src.agents.sql_generator_agent import sql_generator
from src.agents.validator_agent import query_validator
from src.agents.dba_guard_agent import dba_guard
from src.agents.executor_agent import executor_agent
from src.agents.response_agent import response_generator
from src.agents.fallback_agent import fallback_handler
from src.agents.logger_agent import logger_agent
# Agentes adicionais para funcionalidades expandidas (não utilizados na versão atual)
# from src.agents.tavily_agent import tavily_search_agent
# from src.agents.rag_agent import rag_agent
# from src.agents.augmented_response_agent import augmented_response_agent
# from src.agents.main_router_agent import main_router_agent
# from src.agents.emotional_support_agent import emotional_support_agent
# from src.agents.tutor_agent import tutor_agent
# from src.agents.planning_agent import planning_agent
from src.utils.logging import logger

def create_academic_graph() -> Callable:
    """
    Creates the academic agent graph.

    Returns:
        Callable: Compiled academic agent graph
    """
    # Create the graph
    academic_graph = StateGraph(AcademicAgentState)

    # Add nodes - simplified version
    academic_graph.add_node("user_context_node", user_context_agent)
    academic_graph.add_node("cache_check", cache_agent)
    academic_graph.add_node("intent_router", intent_router)
    academic_graph.add_node("schema_retriever", schema_retriever)
    academic_graph.add_node("sql_generator", sql_generator)
    academic_graph.add_node("query_validator", query_validator)
    academic_graph.add_node("dba_guard", dba_guard)
    academic_graph.add_node("executor", executor_agent)
    academic_graph.add_node("response_generator", response_generator)
    academic_graph.add_node("fallback_handler", fallback_handler)
    academic_graph.add_node("cache_update", update_cache)
    academic_graph.add_node("logger", logger_agent)

    # Define routing function
    def route_from_cache(state: AcademicAgentState) -> str:
        """Routes based on cache hit."""
        if state.get("from_cache", False):
            logger.info("Cache hit, skipping to response generator")
            return "response_generator"
        return "intent_router"

    # Connect the nodes - simplified version
    academic_graph.add_edge(START, "user_context_node")
    academic_graph.add_edge("user_context_node", "cache_check")
    academic_graph.add_edge("cache_check", "intent_router")
    academic_graph.add_edge("intent_router", "schema_retriever")
    academic_graph.add_edge("schema_retriever", "sql_generator")
    academic_graph.add_edge("sql_generator", "query_validator")
    academic_graph.add_edge("query_validator", "dba_guard")
    academic_graph.add_edge("dba_guard", "executor")
    academic_graph.add_edge("executor", "response_generator")
    academic_graph.add_edge("response_generator", "cache_update")
    academic_graph.add_edge("fallback_handler", "logger")
    academic_graph.add_edge("cache_update", "logger")
    academic_graph.add_edge("logger", END)

    # Compile the graph
    return academic_graph.compile()

# The academic workflow will be created when needed by importing create_academic_graph
