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
from src.agents.nl2sql_agent import nl2sql_agent
from src.agents.validator_agent import query_validator
from src.agents.dba_guard_agent import dba_guard
from src.agents.executor_agent import executor_agent
from src.agents.response_agent import response_generator
from src.agents.fallback_agent import fallback_handler
from src.agents.logger_agent import logger_agent
from src.agents.integrated_tavily_agent import integrate_tavily_search
# Agentes adicionais para funcionalidades expandidas
from src.agents.rag_agent import rag_agent
from src.agents.augmented_response_agent import augmented_response_agent
from src.agents.main_router_agent import main_router_agent
from src.agents.emotional_support_agent import emotional_support_agent
from src.agents.tutor_agent import tutor_agent
from src.agents.planning_agent import planning_agent
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
    academic_graph.add_node("main_router", main_router_agent)  # Roteador principal
    academic_graph.add_node("intent_router", intent_router)
    academic_graph.add_node("emotional_support", emotional_support_agent)  # Agente de suporte emocional
    academic_graph.add_node("tutor", tutor_agent)  # Agente de tutoria
    academic_graph.add_node("planning", planning_agent)  # Agente de planejamento
    academic_graph.add_node("tavily_search", integrate_tavily_search)
    academic_graph.add_node("rag_retrieval", rag_agent)  # Adicionar nó RAG
    academic_graph.add_node("schema_retriever", schema_retriever)
    # Use the new NL2SQL agent instead of the old SQL generator
    academic_graph.add_node("sql_generator", nl2sql_agent)
    academic_graph.add_node("query_validator", query_validator)
    academic_graph.add_node("dba_guard", dba_guard)
    academic_graph.add_node("executor", executor_agent)
    academic_graph.add_node("response_generator", augmented_response_agent)  # Usar o agente de resposta aumentada
    academic_graph.add_node("fallback_handler", fallback_handler)
    academic_graph.add_node("cache_update", update_cache)
    academic_graph.add_node("logger", logger_agent)

    # Define routing function
    def route_from_cache(state: AcademicAgentState) -> Dict[str, Any]:
        """Routes based on cache hit."""
        if state.get("from_cache", False):
            logger.info("Cache hit, skipping to response generator")
            return {"next": "response_generator"}
        return {"next": "main_router"}  # Vai para o roteador principal em vez do intent_router

    # Define conditional edges for main router
    academic_graph.add_conditional_edges(
        "main_router",
        lambda state: main_router_agent(state)["next"],  # Extrair a chave "next" do dicionário retornado
        {
            "emotional_support": "emotional_support",
            "tutor": "tutor",
            "planning": "planning",
            "intent_router": "intent_router"  # Rota padrão para consultas acadêmicas
        }
    )

    # Connect the nodes - simplified version
    academic_graph.add_edge(START, "user_context_node")
    academic_graph.add_edge("user_context_node", "cache_check")

    # Adicionar roteamento condicional a partir do cache_check
    academic_graph.add_conditional_edges(
        "cache_check",
        lambda state: route_from_cache(state)["next"],  # Extrair a chave "next" do dicionário retornado
        {
            "response_generator": "response_generator",
            "main_router": "main_router"
        }
    )

    # Fluxo para o agente acadêmico
    academic_graph.add_edge("intent_router", "tavily_search")
    academic_graph.add_edge("tavily_search", "rag_retrieval")
    academic_graph.add_edge("rag_retrieval", "schema_retriever")
    academic_graph.add_edge("schema_retriever", "sql_generator")
    academic_graph.add_edge("sql_generator", "query_validator")
    academic_graph.add_edge("query_validator", "dba_guard")
    academic_graph.add_edge("dba_guard", "executor")
    academic_graph.add_edge("executor", "response_generator")

    # Fluxo para os agentes especializados
    academic_graph.add_edge("emotional_support", "response_generator")
    academic_graph.add_edge("tutor", "response_generator")
    academic_graph.add_edge("planning", "response_generator")

    # Fluxo final comum
    academic_graph.add_edge("response_generator", "cache_update")
    academic_graph.add_edge("fallback_handler", "logger")
    academic_graph.add_edge("cache_update", "logger")
    academic_graph.add_edge("logger", END)

    # Compile the graph
    return academic_graph.compile()

# The academic workflow will be created when needed by importing create_academic_graph
