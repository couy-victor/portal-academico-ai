"""
Main Router Agent for the Academic Agent system.
Responsible for routing queries to the appropriate specialized agent.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def main_router_agent(state: AcademicAgentState) -> Dict[str, Any]:
    """
    Routes queries to the appropriate specialized agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        Dict[str, Any]: Dictionary containing the next node to route to
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return {"next": "intent_router"}  # Default to academic route

    # Create prompt for main routing
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em classificação de consultas acadêmicas, capaz de identificar
    a categoria mais apropriada para cada pergunta.

    Pergunta do usuário: {query}

    Classifique esta pergunta em uma das seguintes categorias:

    1. academic: Consultas sobre informações acadêmicas estruturadas (notas, faltas, disciplinas, professores, horários, etc.)
    2. emotional_support: Pedidos de apoio emocional, ajuda com ansiedade, estresse, burnout, etc.
    3. tutor: Dúvidas sobre conteúdos específicos, pedidos de explicação sobre matérias, conceitos, etc.
    4. planning: Solicitações de ajuda com planejamento de estudos, organização de tempo, preparação para provas, etc.

    Raciocine passo a passo:
    1. Quais são as palavras-chave na pergunta?
    2. Qual é o objetivo principal do usuário?
    3. Que tipo de resposta seria mais útil?
    4. Qual categoria melhor se encaixa nesta pergunta?
    5. Qual o nível de confiança nesta classificação (0.0 a 1.0)?

    Formato da resposta:
    ```json
    {
        "category": "categoria_escolhida",
        "confidence": valor_de_confiança,
        "reasoning": "seu_raciocínio_aqui"
    }
    ```
    """)

    # Initialize LLM with low temperature for classification
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"]
        }

        # Execute the classification
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content
        json_str = response_text

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()

        result = json.loads(json_str)

        # Update state with routing information
        state["main_category"] = result["category"]
        state["main_confidence"] = result["confidence"]

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["main_routing_reasoning"] = result.get("reasoning", "")

        # Log success
        logger.info(f"Routed query to {state['main_category']} with confidence {state['main_confidence']}")

        # Return the appropriate next node based on the category
        category = result["category"]
        if category == "emotional_support":
            return {"next": "emotional_support"}
        elif category == "tutor":
            return {"next": "tutor"}
        elif category == "planning":
            return {"next": "planning"}
        else:  # Default to academic
            return {"next": "intent_router"}

    except Exception as e:
        error_msg = f"Error in main routing: {str(e)}"
        logger.error(error_msg)
        # Default to academic if there's an error
        state["main_category"] = "academic"
        state["main_confidence"] = 0.5

        # Store error in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["main_routing_error"] = error_msg

        # Default to academic route
        return {"next": "intent_router"}
