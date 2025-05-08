"""
Adaptive Tutor Module for the Academic Agent system.
Enhances the tutor agent with adaptive learning capabilities.
"""
import json
from typing import Dict, Any, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def assess_prior_knowledge(state: AcademicAgentState) -> AcademicAgentState:
    """
    Assesses the student's prior knowledge based on their query and interaction history.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with prior knowledge assessment
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Create prompt for knowledge assessment
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em avaliação educacional, capaz de identificar o nível de conhecimento
    prévio de um estudante com base em sua pergunta e interações anteriores.

    Pergunta do estudante: {query}

    {interaction_history}

    Avalie o nível de conhecimento prévio do estudante sobre o tópico, considerando:
    1. A terminologia utilizada na pergunta
    2. A complexidade dos conceitos mencionados
    3. As referências a outros conceitos relacionados
    4. O histórico de interações (se disponível)

    Formato da resposta:
    ```json
    {
        "knowledge_level": "iniciante/intermediário/avançado",
        "confidence": 0.1-1.0,
        "gaps": ["conceito_1", "conceito_2"],
        "strengths": ["conceito_3", "conceito_4"],
        "recommended_approach": "descrição_da_abordagem_recomendada",
        "reasoning": "seu_raciocínio_para_esta_avaliação"
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare interaction history if available
        interaction_history = ""
        if "metadata" in state and "interaction_history" in state["metadata"]:
            history = state["metadata"]["interaction_history"]
            interaction_history = "Histórico de interações:\n"
            for i, interaction in enumerate(history):
                interaction_history += f"{i+1}. Pergunta: {interaction.get('query', '')}\n"
                if "response" in interaction:
                    interaction_history += f"   Resposta: {interaction.get('response', '')[:200]}...\n"

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "interaction_history": interaction_history
        }

        # Execute the assessment
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content
        json_str = response_text

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()

        # Clean up the JSON string
        json_str = json_str.replace("\n", "")
        json_str = json_str.replace("\r", "")

        # Ensure we have valid JSON
        if not json_str.startswith('{'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Remove any trailing commas before closing brackets (common JSON error)
        json_str = json_str.replace(',}', '}').replace(',]', ']')

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        # Parse the JSON
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. JSON string: {json_str}")
            # Fallback to a default result
            result = {
                "knowledge_level": "iniciante",
                "confidence": 0.7,
                "gaps": [],
                "strengths": [],
                "recommended_approach": "Explicar conceitos básicos primeiro"
            }

        # Update state with knowledge assessment
        state["prior_knowledge"] = {
            "level": result.get("knowledge_level", "iniciante"),
            "confidence": result.get("confidence", 0.7),
            "gaps": result.get("gaps", []),
            "strengths": result.get("strengths", []),
            "recommended_approach": result.get("recommended_approach", "")
        }

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["knowledge_assessment_reasoning"] = result.get("reasoning", "")

        # Log success
        logger.info(f"Assessed prior knowledge: {state['prior_knowledge']['level']} (confidence: {state['prior_knowledge']['confidence']})")

    except Exception as e:
        error_msg = f"Error assessing prior knowledge: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["knowledge_assessment_error"] = error_msg

        # Set default knowledge level
        state["prior_knowledge"] = {
            "level": "iniciante",
            "confidence": 0.5,
            "gaps": [],
            "strengths": [],
            "recommended_approach": "Explicar conceitos básicos primeiro"
        }

    return state

def generate_multi_level_explanation(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates explanations at multiple levels of complexity.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with multi-level explanations
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have subject and topic information
    if not state.get("subject") or not state.get("topic"):
        return state

    # Create prompt for multi-level explanation
    prompt = ChatPromptTemplate.from_template("""
    Você é um professor especialista em {subject}, capaz de explicar conceitos em múltiplos níveis de complexidade.

    Pergunta do estudante: {query}
    Tópico específico: {topic}
    Nível de conhecimento prévio: {knowledge_level}
    Lacunas de conhecimento identificadas: {knowledge_gaps}
    Pontos fortes identificados: {knowledge_strengths}

    Gere explicações em três níveis de complexidade:

    1. NÍVEL BÁSICO: Uma explicação simples e acessível para iniciantes, usando analogias cotidianas e linguagem simples.

    2. NÍVEL INTERMEDIÁRIO: Uma explicação mais detalhada que introduz terminologia específica da área e alguns conceitos mais avançados.

    3. NÍVEL AVANÇADO: Uma explicação aprofundada que aborda nuances, exceções e conexões com outros conceitos avançados da área.

    Para cada nível, inclua:
    - Conceitos-chave
    - Exemplos ilustrativos
    - Conexões com outros tópicos relevantes

    Formato da resposta:
    ```json
    {
        "basic": {
            "explanation": "explicação_básica",
            "key_concepts": ["conceito_1", "conceito_2"],
            "examples": ["exemplo_1", "exemplo_2"]
        },
        "intermediate": {
            "explanation": "explicação_intermediária",
            "key_concepts": ["conceito_1", "conceito_2"],
            "examples": ["exemplo_1", "exemplo_2"]
        },
        "advanced": {
            "explanation": "explicação_avançada",
            "key_concepts": ["conceito_1", "conceito_2"],
            "examples": ["exemplo_1", "exemplo_2"]
        },
        "recommended_level": "básico/intermediário/avançado"
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Get knowledge level and gaps
        knowledge_level = "iniciante"
        knowledge_gaps = []
        knowledge_strengths = []

        if state.get("prior_knowledge"):
            knowledge_level = state["prior_knowledge"].get("level", "iniciante")
            knowledge_gaps = state["prior_knowledge"].get("gaps", [])
            knowledge_strengths = state["prior_knowledge"].get("strengths", [])

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state["subject"],
            "topic": state["topic"],
            "knowledge_level": knowledge_level,
            "knowledge_gaps": ", ".join(knowledge_gaps) if knowledge_gaps else "Nenhuma identificada",
            "knowledge_strengths": ", ".join(knowledge_strengths) if knowledge_strengths else "Nenhum identificado"
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content
        json_str = response_text

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()

        # Clean up the JSON string
        json_str = json_str.replace("\n", "")
        json_str = json_str.replace("\r", "")

        # Ensure we have valid JSON
        if not json_str.startswith('{'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Remove any trailing commas before closing brackets (common JSON error)
        json_str = json_str.replace(',}', '}').replace(',]', ']')

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        # Parse the JSON
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. JSON string: {json_str}")
            # Fallback to a default result
            result = {
                "basic": {"explanation": "Explicação básica não disponível", "key_concepts": [], "examples": []},
                "intermediate": {"explanation": "Explicação intermediária não disponível", "key_concepts": [], "examples": []},
                "advanced": {"explanation": "Explicação avançada não disponível", "key_concepts": [], "examples": []},
                "recommended_level": "básico"
            }

        # Update state with multi-level explanations
        state["multi_level_explanation"] = {
            "basic": result.get("basic", {}),
            "intermediate": result.get("intermediate", {}),
            "advanced": result.get("advanced", {}),
            "recommended_level": result.get("recommended_level", knowledge_level)
        }

        # Set the primary explanation based on the recommended level
        recommended_level = result.get("recommended_level", knowledge_level)
        if recommended_level == "avançado":
            state["explanation"] = result.get("advanced", {}).get("explanation", "")
        elif recommended_level == "intermediário":
            state["explanation"] = result.get("intermediate", {}).get("explanation", "")
        else:
            state["explanation"] = result.get("basic", {}).get("explanation", "")

        # Log success
        logger.info(f"Generated multi-level explanations with recommended level: {recommended_level}")

    except Exception as e:
        error_msg = f"Error generating multi-level explanations: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["multi_level_explanation_error"] = error_msg

    return state
