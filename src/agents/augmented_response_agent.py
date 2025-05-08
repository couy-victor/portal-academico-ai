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

    # Verificar se a consulta é sobre informações externas
    is_external_info_query = state.get("metadata", {}).get("skip_sql_for_external_info", False)

    # Se for uma consulta sobre informações externas mas não temos resultados da web
    if is_external_info_query and not has_web_search:
        logger.info("Consulta sobre informações externas sem resultados da web - gerando resposta alternativa")
        return generate_external_info_fallback(state)

    # If we don't have any results, return the state unchanged
    if not (has_rag or has_web_search or has_query_results):
        logger.info("No results available for augmented response")
        return state

    # Verificar se a consulta é sobre informações externas
    is_external_info_query = state.get("metadata", {}).get("skip_sql_for_external_info", False)

    # Criar prompt apropriado com base no tipo de consulta
    if is_external_info_query:
        # Prompt para consultas sobre informações externas (prioriza web)
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente acadêmico amigável e profissional.

        Pergunta original do usuário: {query}
        Intenção detectada: {intent}

        {web_section}

        {rag_section}

        {db_results_section}

        Gere uma resposta em linguagem natural que:
        1. Seja direta e responda exatamente o que foi perguntado
        2. Integre as informações relevantes de todas as fontes disponíveis
        3. PRIORIZE informações da web para esta consulta sobre a instituição
        4. Complemente com informações dos documentos e do banco de dados quando relevante
        5. Use um tom amigável mas profissional
        6. Seja concisa (máximo 5 frases)
        7. Não mencione detalhes técnicos como SQL, RAG ou busca na web
        8. Cite fontes externas quando apropriado
        9. IMPORTANTE: NÃO sugira verificar o site oficial da UNISAL se você já tem informações suficientes para responder à pergunta
        10. Apenas sugira verificar o site oficial se realmente não houver informações disponíveis nas fontes consultadas
        11. Se você mencionar URLs, liste-os no final da resposta em uma nova linha

        Resposta:
        """)
    else:
        # Prompt padrão para outras consultas (prioriza banco de dados)
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente acadêmico amigável e profissional.

        Pergunta original do usuário: {query}
        Intenção detectada: {intent}

        {db_results_section}

        {rag_section}

        {web_section}

        Gere uma resposta em linguagem natural que:
        1. Seja direta e responda exatamente o que foi perguntado
        2. Integre APENAS as informações relevantes das fontes disponíveis
        3. Priorize dados do banco de dados quando disponíveis
        4. Complemente com informações dos documentos e da web quando relevante
        5. Use um tom amigável mas profissional
        6. Seja concisa (máximo 5 frases)
        7. Não mencione detalhes técnicos como SQL, RAG ou busca na web
        8. Cite fontes externas quando apropriado
        9. IMPORTANTE: Se os resultados da consulta estiverem vazios (lista vazia), NÃO invente informações
        10. Se os resultados estiverem vazios, informe ao usuário que não foram encontrados resultados para a consulta
        11. NUNCA mencione disciplinas, professores ou cursos específicos se eles não aparecerem nos resultados da consulta
        12. NUNCA invente dados como carga horária, nomes de professores ou detalhes de disciplinas

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

def generate_external_info_fallback(state: AcademicAgentState) -> AcademicAgentState:
    """
    Gera uma resposta alternativa para consultas sobre informações externas quando não há resultados da web.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta alternativa
    """
    # Extrair a consulta do usuário
    user_query = state["user_query"]

    # Criar prompt para resposta alternativa
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico amigável e profissional.

    Pergunta original do usuário: {query}

    O usuário está perguntando sobre informações externas da UNISAL (como campus, cursos de extensão ou programas de intercâmbio).

    Gere uma resposta amigável que:
    1. Forneça informações gerais sobre a UNISAL que você conhece
    2. Mencione que a UNISAL tem vários campi em diferentes cidades de São Paulo
    3. Se a pergunta for sobre cursos de extensão, mencione que a UNISAL oferece diversos cursos de extensão e pós-graduação
    4. Se a pergunta for sobre intercâmbio, mencione que a UNISAL tem parcerias internacionais
    5. Seja específico e informativo com o que você sabe, sem sugerir consultar o site oficial
    6. Use um tom prestativo e cordial
    7. Ofereça-se para ajudar com outras perguntas relacionadas à vida acadêmica

    Resposta:
    """)

    # Inicializar LLM com temperatura mais alta para linguagem natural
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Preparar inputs
        inputs = {
            "query": user_query
        }

        # Executar a geração
        response = llm.invoke(prompt.format_messages(**inputs))

        # Atualizar estado com resposta em linguagem natural
        state["natural_response"] = response.content.strip()

        # Registrar sucesso
        logger.info(f"Generated external info fallback response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating external info fallback response: {str(e)}"
        logger.error(error_msg)
        state["natural_response"] = "Desculpe, não consegui obter informações atualizadas sobre a UNISAL no momento. Por favor, consulte o site oficial da universidade (https://unisal.br) para informações precisas e atualizadas."

    return state