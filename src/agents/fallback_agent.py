"""
Fallback Agent for the Academic Agent system.
Responsible for handling errors and providing fallback responses.
"""
from typing import Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def fallback_handler(state: AcademicAgentState) -> AcademicAgentState:
    """
    Handles errors and provides fallback responses.
    
    Args:
        state (AcademicAgentState): Current state with error
        
    Returns:
        AcademicAgentState: Updated state with fallback response
    """
    error_message = state.get("error", "Erro desconhecido")
    
    # Categorize the error
    if "SQL syntax" in error_message:
        error_type = "sql_syntax"
    elif "permission denied" in error_message.lower():
        error_type = "permission"
    elif "timeout" in error_message.lower():
        error_type = "timeout"
    elif "schema" in error_message.lower():
        error_type = "schema"
    elif "not found" in error_message.lower():
        error_type = "not_found"
    else:
        error_type = "general"
    
    # Create prompt for fallback response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico que precisa lidar com um erro.
    
    Pergunta original do usuário: {query}
    Intenção detectada: {intent}
    Tipo de erro: {error_type}
    Mensagem de erro (não mostrar ao usuário): {error_message}
    
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
            "intent": state.get("intent", "desconhecida"),
            "error_type": error_type,
            "error_message": error_message
        }
        
        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Update state with fallback response
        state["natural_response"] = response.content.strip()
        
        # Add metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["fallback_triggered"] = True
        state["metadata"]["error_type"] = error_type
        
        logger.info(f"Generated fallback response for error type: {error_type}")
        
    except Exception as e:
        # If fallback generation fails, use a generic message
        logger.error(f"Error generating fallback response: {str(e)}")
        state["natural_response"] = "Desculpe, não consegui processar sua solicitação no momento. Por favor, tente novamente mais tarde ou reformule sua pergunta."
        
        # Add metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["fallback_triggered"] = True
        state["metadata"]["fallback_error"] = str(e)
    
    return state
