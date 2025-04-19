"""
Tavily Web Search Agent for the Academic Agent system.
Responsible for searching the web for relevant information.
"""
import json
from typing import Dict, Any, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from src.config.settings import TAVILY_API_KEY, TAVILY_MAX_RESULTS, TAVILY_SEARCH_DEPTH, LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

# Initialize Tavily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def tavily_search_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Searches the web for information relevant to the user's query.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with web search results
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    try:
        # Extract search query from user query
        search_query = extract_search_query(state)
        
        # Perform web search
        search_results = perform_web_search(search_query)
        
        # Extract relevant context from search results
        search_context = extract_context_from_results(search_results, state["user_query"])
        
        # Update state with search results and context
        state["web_search_results"] = search_results
        state["web_search_context"] = search_context
        
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

def extract_search_query(state: AcademicAgentState) -> str:
    """
    Extracts a search query from the user's query.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        str: Search query
    """
    # If the intent is already known, use it to guide the search
    intent = state.get("intent", "")
    user_query = state["user_query"]
    
    # For simple queries, just use the user query directly
    if len(user_query.split()) <= 10:
        return user_query
    
    # For more complex queries, use LLM to extract a search query
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente especializado em extrair consultas de busca eficazes.
    
    Pergunta original do usuário: {query}
    Intenção detectada: {intent}
    
    Extraia uma consulta de busca concisa (máximo 10 palavras) que captura a essência da pergunta do usuário.
    A consulta deve ser otimizada para busca na web e deve incluir palavras-chave relevantes.
    
    Consulta de busca:
    """)
    
    # Initialize LLM with low temperature for deterministic output
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    # Prepare inputs
    inputs = {
        "query": user_query,
        "intent": intent
    }
    
    # Execute the extraction
    response = llm.invoke(prompt.format_messages(**inputs))
    
    # Extract the search query
    search_query = response.content.strip()
    
    # Log the extracted search query
    logger.info(f"Extracted search query: {search_query}")
    
    return search_query

def perform_web_search(search_query: str) -> List[Dict[str, Any]]:
    """
    Performs a web search using Tavily API.
    
    Args:
        search_query (str): Search query
        
    Returns:
        List[Dict[str, Any]]: Search results
    """
    try:
        # Perform search
        search_response = tavily_client.search(
            query=search_query,
            search_depth=TAVILY_SEARCH_DEPTH,
            max_results=TAVILY_MAX_RESULTS
        )
        
        # Extract results
        results = search_response.get("results", [])
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0)
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error in Tavily search: {str(e)}")
        raise

def extract_context_from_results(search_results: List[Dict[str, Any]], user_query: str) -> str:
    """
    Extracts relevant context from search results.
    
    Args:
        search_results (List[Dict[str, Any]]): Search results
        user_query (str): User's query
        
    Returns:
        str: Extracted context
    """
    if not search_results:
        return ""
    
    # Combine all search results into a single context
    combined_context = ""
    for i, result in enumerate(search_results):
        combined_context += f"[{i+1}] {result['title']}\n"
        combined_context += f"URL: {result['url']}\n"
        combined_context += f"Conteúdo: {result['content'][:500]}...\n\n"
    
    # For simple cases, just return the combined context
    if len(search_results) <= 2:
        return combined_context
    
    # For more results, use LLM to extract the most relevant information
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente especializado em extrair informações relevantes de resultados de busca na web.
    
    Pergunta do usuário: {query}
    
    Resultados da busca:
    {results}
    
    Extraia as informações mais relevantes dos resultados acima que ajudam a responder à pergunta do usuário.
    Organize as informações de forma coerente e concisa.
    Cite a fonte (número do resultado) para cada informação extraída.
    
    Informações relevantes:
    """)
    
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    # Prepare inputs
    inputs = {
        "query": user_query,
        "results": combined_context
    }
    
    # Execute the extraction
    response = llm.invoke(prompt.format_messages(**inputs))
    
    # Extract the context
    extracted_context = response.content.strip()
    
    return extracted_context
