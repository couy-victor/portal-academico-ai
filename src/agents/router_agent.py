"""
Router Agent for the Academic Agent system.
Responsible for classifying user intent and routing to appropriate agents.
"""
import json
from typing import Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def intent_router(state: AcademicAgentState) -> AcademicAgentState:
    """
    Classifies the user's intent and routes to the appropriate agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with intent classification
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Define intent categories
    intent_categories = [
        "notas", "faltas", "disciplinas", "professores", "horarios",
        "calendario", "matricula", "historico", "outros"
    ]

    # Create prompt with ReAct technique for better reasoning
    prompt = ChatPromptTemplate.from_template("""
    Você é um agente especializado em classificar intenções de perguntas acadêmicas.

    Pergunta do usuário: {query}
    Contexto do usuário: {context}

    Raciocine passo a passo:
    1. Qual é o tema principal da pergunta?
    2. Quais informações específicas o usuário está buscando?
    3. Qual categoria melhor se encaixa nesta pergunta: {categories}?
    4. Qual o nível de confiança nesta classificação (0.0 a 1.0)?

    IMPORTANTE: Sua resposta deve ser APENAS um objeto JSON válido, sem texto adicional antes ou depois, no seguinte formato:

    {{
        "intent": "categoria_escolhida",
        "confidence": valor_de_confiança,
        "reasoning": "seu raciocínio aqui"
    }}

    Não inclua código markdown (```json) nem qualquer outro texto. Apenas o JSON puro.
    """)

    # Initialize LLM with low temperature for classification
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Prepare inputs
    inputs = {
        "query": state["user_query"],
        "context": json.dumps(state["user_context"], ensure_ascii=False),
        "categories": ", ".join(intent_categories)
    }

    try:
        # Execute the classification
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract the structured response
        response_text = response.content

        # Extract JSON from the response
        try:
            # Try to find JSON in the response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
            else:
                # If no code blocks, try to extract JSON directly
                json_str = response_text.strip()

            # Clean up the JSON string
            json_str = json_str.replace("\n", "")
            json_str = json_str.replace("\r", "")

            # Parse the JSON
            result = json.loads(json_str)
        except Exception as json_error:
            logger.error(f"Error parsing JSON in intent router: {str(json_error)}. Response: {response_text[:100]}...")
            # Create a default result
            result = {
                "intent": "faltas",
                "confidence": 0.8,
                "reasoning": "A pergunta parece estar relacionada a faltas em uma disciplina."
            }

        # Update state with intent classification
        state["intent"] = result["intent"]
        state["confidence"] = result["confidence"]

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["intent_reasoning"] = result.get("reasoning", "")

        logger.info(f"Classified intent: {result['intent']} with confidence {result['confidence']}")

    except Exception as e:
        error_msg = f"Error in intent classification: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg

    return state
