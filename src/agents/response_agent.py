"""
Response Generator Agent for the Academic Agent system.
Responsible for converting query results to natural language responses.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def response_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Converts query results to natural language responses.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with natural language response
    """
    # If we already have a natural response (from cache or fallback), return
    if state.get("natural_response"):
        return state

    # If there's an error, generate an error response
    if state.get("error"):
        return generate_error_response(state)

    # Check if we have web search results
    has_web_results = "web_search_context" in state and state["web_search_context"]

    # Create prompt for natural language response
    if has_web_results:
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente acadêmico amigável e profissional.

        Pergunta original do usuário: {query}
        Intenção detectada: {intent}

        Informações da web:
        {web_context}

        Resultados da consulta (se disponíveis):
        ```json
        {results}
        ```

        Gere uma resposta em linguagem natural que:
        1. Seja direta e responda exatamente o que foi perguntado
        2. Inclua os dados relevantes das informações da web e dos resultados da consulta (se disponíveis)
        3. Use um tom amigável mas profissional
        4. Seja informativa e completa
        5. Não mencione detalhes técnicos como SQL ou banco de dados
        6. Se a pergunta for sobre a UNISAL ou cursos, priorize as informações da web

        Resposta:
        """)
    else:
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente acadêmico amigável e profissional.

        Pergunta original do usuário: {query}
        Intenção detectada: {intent}
        Resultados da consulta:
        ```json
        {results}
        ```

        Gere uma resposta em linguagem natural que:
        1. Seja direta e responda exatamente o que foi perguntado
        2. Inclua APENAS os dados relevantes dos resultados da consulta
        3. Use um tom amigável mas profissional
        4. Seja concisa (máximo 3 frases)
        5. Não mencione detalhes técnicos como SQL ou banco de dados
        6. Se a pergunta for sobre faltas, seja preciso e mencione o número exato de faltas
        7. Se o número de faltas for 1, use "1 falta" (singular), se for 0 ou mais de 1, use "faltas" (plural)
        8. Sempre mencione o nome da disciplina na resposta, usando o campo "disciplina_nome" dos resultados
        9. IMPORTANTE: Se os resultados da consulta estiverem vazios (lista vazia), NÃO invente informações
        10. Se os resultados estiverem vazios, informe ao usuário que não foram encontrados resultados para a consulta
        11. NUNCA mencione disciplinas específicas se elas não aparecerem nos resultados da consulta

        Resposta:
        """)

    # Initialize LLM with higher temperature for natural language
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "intent": state.get("intent", "unknown"),
            "results": json.dumps(state.get("query_results", []), ensure_ascii=False, indent=2)
        }

        # Add web context if available
        if has_web_results:
            inputs["web_context"] = state["web_search_context"]

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with natural language response
        state["natural_response"] = response.content.strip()

        # Log success
        logger.info(f"Generated natural language response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
        return generate_error_response(state)

    return state

def generate_error_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates a friendly error response when something goes wrong.

    Args:
        state (AcademicAgentState): Current state with error

    Returns:
        AcademicAgentState: Updated state with error response
    """
    error_message = state.get("error", "Ocorreu um erro desconhecido.")

    # Create prompt for error response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico que precisa lidar com um erro.

    Pergunta original do usuário: {query}
    Erro técnico (não mostrar ao usuário): {error}

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
