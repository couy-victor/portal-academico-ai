"""
Integrated Tavily Agent for the Academic Agent system.
This agent integrates with the academic agent to provide web search capabilities.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.agents.tavily_agent import perform_web_search, extract_search_query, extract_context_from_results
from src.utils.logging import logger

def should_use_tavily(state: AcademicAgentState) -> bool:
    """
    Determines if the query should use Tavily web search.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        bool: True if Tavily should be used, False otherwise
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return False

    user_query = state["user_query"].lower()

    # Keywords that suggest we need external information
    external_info_keywords = [
        "unisal", "universidade", "faculdade", "curso", "cursos",
        "graduação", "pós-graduação", "campus", "campi", "unidade",
        "instituição", "centro universitário", "salesiano", "salesiana",
        "inscrição", "vestibular", "processo seletivo", "bolsa", "bolsas",
        "enade", "mec", "avaliação", "ranking", "nota"
    ]

    # Palavras-chave específicas para filiais e cursos de extensão
    specific_keywords = [
        "filial", "filiais", "unidade", "unidades", "campus", "campi", "sede", "sedes",
        "extensão", "extensao", "curso livre", "cursos livres", "especialização",
        "especializacao", "pós-graduação", "pos-graduacao", "workshop", "palestra",
        "evento", "eventos", "calendário", "calendario", "programação", "programacao",
        "intercâmbio", "intercambio", "internacional", "exterior", "estrangeiro"
    ]

    # Verificar palavras-chave específicas primeiro
    for keyword in specific_keywords:
        if keyword in user_query:
            logger.info(f"Usando Tavily para consulta sobre {keyword}")
            # Marcar para pular SQL
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["skip_sql_for_external_info"] = True
            return True

    # Check if any of the keywords are in the query
    for keyword in external_info_keywords:
        if keyword in user_query:
            # Verificar se a consulta contém perguntas sobre quantidade, localização ou disponibilidade
            quantity_patterns = ["quantas", "quantos", "número de", "numero de", "total de", "possui", "tem", "existem", "disponível", "disponivel", "aberto"]
            if any(pattern in user_query for pattern in quantity_patterns):
                logger.info(f"Usando Tavily para consulta quantitativa sobre {keyword}")
                # Marcar para pular SQL
                if "metadata" not in state:
                    state["metadata"] = {}
                state["metadata"]["skip_sql_for_external_info"] = True
                return True
            return True

    # If the query is about general information that might not be in the database
    general_info_patterns = [
        "o que é", "como funciona", "quais são", "onde fica", "quando",
        "por que", "quem é", "história", "missão", "valores", "contato",
        "endereço", "telefone", "email", "site", "página", "redes sociais"
    ]

    for pattern in general_info_patterns:
        if pattern in user_query and any(kw in user_query for kw in external_info_keywords):
            logger.info(f"Usando Tavily para consulta de informação geral: {pattern}")
            # Marcar para pular SQL
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["skip_sql_for_external_info"] = True
            return True

    # Verificar se a consulta é sobre cálculo de notas (conceitual)
    calculo_nota_patterns = [
        "como é feito o cálculo", "como é calculado", "como calcular",
        "fórmula", "método de cálculo", "como é feito o calculo",
        "como funciona o cálculo", "como são calculadas", "como é a média"
    ]

    for pattern in calculo_nota_patterns:
        if pattern in user_query and ("nota" in user_query or "média" in user_query or "media" in user_query):
            # Marcar para usar RAG em vez de SQL
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["use_rag_for_conceptual"] = True
            return True

    return False

def integrate_tavily_search(state: AcademicAgentState) -> AcademicAgentState:
    """
    Integrates Tavily web search with the academic agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with web search results
    """
    # Check if we should use Tavily
    if not should_use_tavily(state):
        return state

    try:
        logger.info("Using Tavily web search for query")

        # Extract search query from user query
        search_query = extract_search_query(state)

        # Verificar se a consulta é sobre filiais/campus
        if any(kw in state["user_query"].lower() for kw in ["filial", "filiais", "unidade", "unidades", "campus", "campi"]):
            search_query = f"UNISAL quantos campi campus unidades filiais sedes tem localização endereços"
            # Forçar pular SQL
            state["skip_sql_generation"] = True
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["skip_sql_for_external_info"] = True
            logger.info(f"Forçando pular SQL para consulta sobre campus/filiais: {search_query}")

        # Verificar se a consulta é sobre cursos de extensão
        elif any(kw in state["user_query"].lower() for kw in ["extensão", "extensao", "curso livre", "cursos livres"]):
            search_query = f"UNISAL cursos de extensão disponíveis atualmente"
            # Forçar pular SQL
            state["skip_sql_generation"] = True
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["skip_sql_for_external_info"] = True
            logger.info(f"Forçando pular SQL para consulta sobre cursos de extensão: {search_query}")

        # Verificar se a consulta é sobre intercâmbio
        elif any(kw in state["user_query"].lower() for kw in ["intercâmbio", "intercambio", "internacional", "exterior"]):
            search_query = f"UNISAL programas de intercâmbio internacional disponíveis atualmente"
            # Forçar pular SQL
            state["skip_sql_generation"] = True
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["skip_sql_for_external_info"] = True
            logger.info(f"Forçando pular SQL para consulta sobre intercâmbio: {search_query}")

        # Add "UNISAL" to the search query if it's not already there and the query is about the institution
        elif "unisal" not in search_query.lower() and any(kw in state["user_query"].lower() for kw in ["curso", "faculdade", "universidade"]):
            search_query = f"UNISAL {search_query}"

        # Perform web search
        search_results = perform_web_search(search_query)

        # Extract relevant context from search results
        search_context = extract_context_from_results(search_results, state["user_query"])

        # Update state with search results and context
        state["web_search_results"] = search_results
        state["web_search_context"] = search_context

        # Set a flag to indicate that we used Tavily
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["used_tavily"] = True

        # Set a flag to skip SQL generation if the query is about general information
        # that doesn't require database access
        general_info_keywords = [
            "o que é", "como funciona", "quais são", "onde fica", "quando",
            "por que", "quem é", "história", "missão", "valores", "contato",
            "endereço", "telefone", "email", "site", "página", "redes sociais",
            "curso", "cursos", "graduação", "pós-graduação", "campus", "campi",
            "universidade", "faculdade", "instituição"
        ]

        if any(kw in state["user_query"].lower() for kw in general_info_keywords):
            # Set a dummy query result to skip SQL generation
            state["query_results"] = []
            state["skip_sql_generation"] = True
            state["skip_database_query"] = True
            logger.info("Skipping SQL generation for general information query")

        # Log success
        logger.info(f"Web search completed with {len(search_results)} results")

    except Exception as e:
        error_msg = f"Error in web search: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["web_search_error"] = error_msg

    return state
