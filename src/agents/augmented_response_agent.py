"""
Augmented Response Agent for the Academic Agent system.
Responsible for generating responses augmented with RAG and web search results.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def augmented_response_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates responses augmented with RAG and web search results.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with augmented response
    """
    # If we already have a natural response (from cache or fallback), return
    if state.get("natural_response"):
        return state
    
    # If there's an error, generate an error response
    if state.get("error"):
        return generate_error_response(state)
    
    # Check if we have RAG or web search results
    has_rag = bool(state.get("rag_context"))
    has_web_search = bool(state.get("web_search_context"))
    has_query_results = bool(state.get("query_results"))
    
    # If we don't have any results, return the state unchanged
    if not (has_rag or has_web_search or has_query_results):
        logger.info("No results available for augmented response")
        return state
    
    # Create prompt for augmented response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico amigável e profissional.
    
    Pergunta original do usuário: {query}
    Intenção detectada: {intent}
    
    {db_results_section}
    
    {rag_section}
    
    {web_section}
    
    Gere uma resposta em linguagem natural que:
    1. Seja direta e responda exatamente o que foi perguntado
    2. Integre as informações relevantes de todas as fontes disponíveis
    3. Priorize dados do banco de dados quando disponíveis
    4. Complemente com informações dos documentos e da web quando relevante
    5. Use um tom amigável mas profissional
    6. Seja concisa (máximo 5 frases)
    7. Não mencione detalhes técnicos como SQL, RAG ou busca na web
    8. Cite fontes externas quando apropriado
    
    Resposta:
    """)
    
    # Initialize LLM with higher temperature for natural language
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)
    
    try:
        # Prepare sections based on available data
        db_results_section = ""
        if has_query_results:
            db_results_section = f"""
            Resultados da consulta ao banco de dados:
            ```json
            {json.dumps(state.get("query_results", []), ensure_ascii=False, indent=2)}
            ```
            """
        
        rag_section = ""
        if has_rag:
            rag_section = f"""
            Informações de documentos internos:
            {state.get("rag_context", "")}
            """
        
        web_section = ""
        if has_web_search:
            web_section = f"""
            Informações da web:
            {state.get("web_search_context", "")}
            """
        
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "intent": state.get("intent", "unknown"),
            "db_results_section": db_results_section,
            "rag_section": rag_section,
            "web_section": web_section
        }
        
        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Update state with natural language response
        state["natural_response"] = response.content.strip()
        
        # Log success
        logger.info(f"Generated augmented response: {state['natural_response'][:100]}...")
        
    except Exception as e:
        error_msg = f"Error generating augmented response: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
        return generate_error_response(state)
    
    return state

def generate_error_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates an error response.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with error response
    """
    # Extract error message
    error_message = state.get("error", "Erro desconhecido")
    
    # Create prompt for error response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico que precisa lidar com um erro.
    
    Pergunta original do usuário: {query}
    Erro (não mostrar ao usuário): {error}
    
    Gere uma resposta amigável que:
    1. Não mencione detalhes técnicos do erro
    2. Explique que não foi possível processar a solicitação
    3. Sugira uma alternativa ou reformulação da pergunta
    4. Mantenha um tom prestativo
    
    Resposta:
    """)
    
    # Initialize LLM with higher temperature for natural language
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)
    
    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "error": error_message
        }
        
        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Update state with error response
        state["natural_response"] = response.content.strip()
        
        # Log error response
        logger.info(f"Generated error response: {state['natural_response'][:100]}...")
        
    except Exception as e:
        # Fallback to generic error message if response generation fails
        logger.error(f"Error generating error response: {str(e)}")
        state["natural_response"] = "Desculpe, não consegui processar sua solicitação no momento. Por favor, tente novamente mais tarde ou reformule sua pergunta."
    
    return state
