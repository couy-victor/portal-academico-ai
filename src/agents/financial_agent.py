"""
Agente financeiro para o Portal Acadêmico AI.
Responsável por consultas relacionadas a boletos, mensalidades, etc.
"""
import json
import os
import base64
from typing import Dict, Any, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger
from src.utils.boleto_generator import obter_boletos_vencidos

def detect_financial_intent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Detecta a intenção financeira na consulta do usuário.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com informações financeiras
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Create prompt for financial intent detection
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em análise de consultas financeiras acadêmicas.

    Consulta do usuário: {query}

    Analise a consulta e identifique:
    1. Se está relacionada a boletos, mensalidades, pagamentos ou finanças
    2. Se o usuário está perguntando sobre boletos vencidos
    3. Se o usuário está solicitando o código ou download de boletos

    Formato da resposta:
    ```json
    {
        "is_financial": true/false,
        "about_overdue_bills": true/false,
        "requesting_bill_code": true/false,
        "requesting_bill_download": true/false,
        "confidence": valor_entre_0_e_1,
        "reasoning": "seu_raciocínio_aqui"
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"]
        }

        # Execute the detection
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content
        json_str = response_text

        try:
            # Tentar extrair JSON de blocos de código
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()

            # Tentar carregar o JSON
            result = json.loads(json_str)
        except Exception as json_error:
            logger.warning(f"Error parsing JSON from LLM response: {str(json_error)}. Trying fallback method.")

            # Método alternativo: criar um JSON padrão
            result = {
                "is_financial": True if "boleto" in state["user_query"].lower() or "financ" in state["user_query"].lower() or "pagamento" in state["user_query"].lower() else False,
                "about_overdue_bills": True if "vencido" in state["user_query"].lower() or "pendente" in state["user_query"].lower() else False,
                "requesting_bill_code": True if "codigo" in state["user_query"].lower() or "código" in state["user_query"].lower() else False,
                "requesting_bill_download": True if "baixar" in state["user_query"].lower() or "download" in state["user_query"].lower() or "enviar" in state["user_query"].lower() else False,
                "confidence": 0.7,
                "reasoning": "Determinado por análise de palavras-chave como fallback."
            }

        # Update state with financial intent information
        state["is_financial"] = result["is_financial"]
        state["about_overdue_bills"] = result.get("about_overdue_bills", False)
        state["requesting_bill_code"] = result.get("requesting_bill_code", False)
        state["requesting_bill_download"] = result.get("requesting_bill_download", False)
        state["financial_confidence"] = result.get("confidence", 0.5)

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["financial_reasoning"] = result.get("reasoning", "")

        # Log success
        logger.info(f"Detected financial intent: {state['is_financial']} with confidence {state['financial_confidence']}")

    except Exception as e:
        error_msg = f"Error detecting financial intent: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["financial_intent_error"] = error_msg

        # Set default values
        state["is_financial"] = False
        state["about_overdue_bills"] = False
        state["requesting_bill_code"] = False
        state["requesting_bill_download"] = False
        state["financial_confidence"] = 0.0

    return state

def process_overdue_bills(state: AcademicAgentState) -> AcademicAgentState:
    """
    Processa consultas sobre boletos vencidos.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com informações de boletos
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if not a financial query about overdue bills
    if not state.get("is_financial", False) or not state.get("about_overdue_bills", False):
        return state

    try:
        # Obter RA do aluno
        ra = state.get("user_id", "")
        if not ra:
            # Se não tiver RA, usar um valor padrão
            ra = "123456"

        # Obter nome do aluno (fictício para demonstração)
        nome_aluno = "Estudante da UNISAL"

        # Obter boletos vencidos
        boletos = obter_boletos_vencidos(ra, nome_aluno, quantidade=3)

        # Atualizar estado com informações dos boletos
        state["boletos_vencidos"] = boletos
        state["tem_boletos_vencidos"] = len(boletos) > 0
        state["quantidade_boletos_vencidos"] = len(boletos)

        # Preparar códigos dos boletos para resposta
        codigos_boletos = [boleto["codigo"] for boleto in boletos]
        state["codigos_boletos"] = codigos_boletos

        # Preparar caminhos dos PDFs
        caminhos_pdfs = [boleto["pdf_path"] for boleto in boletos]
        state["caminhos_pdfs_boletos"] = caminhos_pdfs

        # Log success
        logger.info(f"Processed {len(boletos)} overdue bills for RA {ra}")

    except Exception as e:
        error_msg = f"Error processing overdue bills: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["overdue_bills_error"] = error_msg

    return state

def generate_financial_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Gera uma resposta para consultas financeiras.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta natural
    """
    # Skip if we already have a natural response
    if state.get("natural_response"):
        return state

    # Skip if not a financial query
    if not state.get("is_financial", False):
        return state

    # Create prompt for financial response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente acadêmico especializado em assuntos financeiros.

    Consulta do usuário: {query}

    Informações financeiras:
    - Tem boletos vencidos: {tem_boletos_vencidos}
    - Quantidade de boletos vencidos: {quantidade_boletos_vencidos}
    - Códigos dos boletos: {codigos_boletos}

    {download_info}

    Gere uma resposta natural e informativa que:
    1. Responda diretamente à pergunta do usuário
    2. Forneça informações precisas sobre os boletos vencidos, se aplicável
    3. Mencione os códigos dos boletos, se o usuário solicitou
    4. Informe sobre a possibilidade de baixar os boletos, se aplicável
    5. Use um tom profissional e prestativo

    Resposta:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare download info
        download_info = ""
        if state.get("requesting_bill_download", False) and state.get("tem_boletos_vencidos", False):
            download_info = "Os boletos podem ser baixados através do Portal Acadêmico."

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "tem_boletos_vencidos": state.get("tem_boletos_vencidos", False),
            "quantidade_boletos_vencidos": state.get("quantidade_boletos_vencidos", 0),
            "codigos_boletos": ", ".join(state.get("codigos_boletos", [])) if state.get("codigos_boletos") else "Nenhum",
            "download_info": download_info
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with natural language response
        state["natural_response"] = response.content.strip()

        # Add PDF information for Streamlit interface
        if state.get("requesting_bill_download", False) and state.get("tem_boletos_vencidos", False):
            state["has_pdf_attachments"] = True
            state["pdf_attachments"] = state.get("caminhos_pdfs_boletos", [])

        # Log success
        logger.info(f"Generated financial response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating financial response: {str(e)}"
        logger.error(error_msg)
        # Set error state
        state["error"] = error_msg
        state["natural_response"] = "Desculpe, não foi possível processar sua consulta financeira no momento. Por favor, tente novamente mais tarde ou entre em contato com o setor financeiro da instituição."

    return state

def financial_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Agente financeiro principal.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta financeira
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Step 1: Detect financial intent
    state = detect_financial_intent(state)

    # If not a financial query, return
    if not state.get("is_financial", False):
        return state

    # Step 2: Process overdue bills if applicable
    if state.get("about_overdue_bills", False):
        state = process_overdue_bills(state)

    # Step 3: Generate financial response
    state = generate_financial_response(state)

    return state
