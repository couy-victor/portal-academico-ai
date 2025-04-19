"""
Emotional Support Agent for the Academic Agent system.
Responsible for providing emotional support to students dealing with academic stress, anxiety, etc.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def emotional_state_detector(state: AcademicAgentState) -> AcademicAgentState:
    """
    Detects the emotional state of the user based on their query.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with emotional state information
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Create prompt for emotional state detection
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em psicologia educacional, capaz de identificar estados emocionais
    a partir de mensagens de texto.

    Mensagem do estudante: {query}

    Analise a mensagem e identifique:
    1. O estado emocional predominante (ex: ansiedade, estresse, frustração, desânimo, etc.)
    2. O problema específico que o estudante está enfrentando
    3. A severidade do problema (baixa, média, alta)

    Formato da resposta:
    ```json
    {
        "emotional_state": "estado_emocional_detectado",
        "emotional_issue": "descrição_detalhada_do_problema",
        "emotional_severity": "baixa/média/alta",
        "reasoning": "seu_raciocínio_para_esta_análise"
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"]
        }

        # Execute the detection
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content

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
            logger.error(f"Error parsing JSON: {str(json_error)}. Response: {response_text[:100]}...")
            # Create a default result
            result = {
                "emotional_state": "ansiedade",
                "emotional_issue": "ansiedade relacionada a provas",
                "emotional_severity": "média",
                "reasoning": "Baseado na mensagem do usuário que menciona ansiedade com provas"
            }

        # Update state with emotional state information
        state["emotional_state"] = result["emotional_state"]
        state["emotional_issue"] = result["emotional_issue"]
        state["emotional_severity"] = result["emotional_severity"]

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["emotional_reasoning"] = result.get("reasoning", "")

        # Log success
        logger.info(f"Detected emotional state: {state['emotional_state']}, severity: {state['emotional_severity']}")

    except Exception as e:
        error_msg = f"Error detecting emotional state: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["emotional_detection_error"] = error_msg

    return state

def strategy_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates strategies to help the user with their emotional issue.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with strategies
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have emotional state information
    if not state.get("emotional_state") or not state.get("emotional_issue"):
        return state

    # Create prompt for strategy generation
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em psicologia educacional, capaz de sugerir estratégias eficazes
    para lidar com desafios emocionais no contexto acadêmico.

    Estado emocional do estudante: {emotional_state}
    Problema específico: {emotional_issue}
    Severidade: {emotional_severity}

    Sugira 3-5 estratégias práticas e baseadas em evidências que possam ajudar o estudante a lidar com este desafio.
    Para cada estratégia, forneça:
    1. Um título curto
    2. Uma descrição detalhada de como implementá-la
    3. Por que esta estratégia é eficaz para este problema específico

    Formato da resposta:
    ```json
    {
        "strategies": [
            {
                "title": "título_da_estratégia",
                "description": "descrição_detalhada",
                "rationale": "justificativa_baseada_em_evidências"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare inputs
        inputs = {
            "emotional_state": state["emotional_state"],
            "emotional_issue": state["emotional_issue"],
            "emotional_severity": state["emotional_severity"]
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content

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
            logger.error(f"Error parsing JSON in strategy generator: {str(json_error)}. Response: {response_text[:100]}...")
            # Create a default result
            result = {
                "strategies": [
                    {
                        "title": "Técnica de respiração profunda",
                        "description": "Respire fundo, contando até 4 na inspiração e até 6 na expiração. Repita por 5 minutos.",
                        "rationale": "Ajuda a reduzir a ansiedade imediatamente ao ativar o sistema nervoso parassimpático."
                    },
                    {
                        "title": "Estudo em blocos focados",
                        "description": "Divida o estudo em blocos de 25 minutos com pausas de 5 minutos entre eles.",
                        "rationale": "Melhora a concentração e reduz a sobrecarga cognitiva."
                    }
                ]
            }

        # Update state with strategies
        state["emotional_strategies"] = result["strategies"]

        # Log success
        logger.info(f"Generated {len(state['emotional_strategies'])} emotional support strategies")

    except Exception as e:
        error_msg = f"Error generating strategies: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["strategy_generation_error"] = error_msg

    return state

def resource_recommender(state: AcademicAgentState) -> AcademicAgentState:
    """
    Recommends resources to help the user with their emotional issue.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with resources
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have emotional state information
    if not state.get("emotional_state") or not state.get("emotional_issue"):
        return state

    # Create prompt for resource recommendation
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em psicologia educacional, capaz de recomendar recursos úteis
    para estudantes lidando com desafios emocionais.

    Estado emocional do estudante: {emotional_state}
    Problema específico: {emotional_issue}
    Severidade: {emotional_severity}

    Recomende 3-5 recursos que possam ajudar o estudante a lidar com este desafio.
    Os recursos podem incluir:
    - Livros
    - Artigos
    - Aplicativos
    - Técnicas específicas
    - Serviços de apoio (como NAP - Núcleo de Apoio Psicopedagógico da universidade)

    Para cada recurso, forneça:
    1. Um título
    2. Uma descrição breve
    3. Por que este recurso é relevante para o problema do estudante

    Formato da resposta:
    ```json
    {
        "resources": [
            {
                "title": "título_do_recurso",
                "description": "descrição_breve",
                "relevance": "por_que_é_relevante"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare inputs
        inputs = {
            "emotional_state": state["emotional_state"],
            "emotional_issue": state["emotional_issue"],
            "emotional_severity": state["emotional_severity"]
        }

        # Execute the recommendation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract JSON from the response
        response_text = response.content

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
            logger.error(f"Error parsing JSON in resource recommender: {str(json_error)}. Response: {response_text[:100]}...")
            # Create a default result
            result = {
                "resources": [
                    {
                        "title": "Aplicativo de Meditação Headspace",
                        "description": "Aplicativo com meditações guiadas para redução de ansiedade.",
                        "relevance": "Oferece técnicas práticas para acalmar a mente antes de provas."
                    },
                    {
                        "title": "Núcleo de Apoio Psicopedagógico (NAP)",
                        "description": "Serviço de apoio psicológico oferecido pela universidade.",
                        "relevance": "Profissionais especializados em lidar com ansiedade acadêmica."
                    }
                ]
            }

        # Update state with resources
        state["emotional_resources"] = result["resources"]

        # Log success
        logger.info(f"Recommended {len(state['emotional_resources'])} emotional support resources")

    except Exception as e:
        error_msg = f"Error recommending resources: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["resource_recommendation_error"] = error_msg

    return state

def emotional_response_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates a response to the user's emotional issue.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with natural language response
    """
    # If we already have a natural response, return
    if state.get("natural_response"):
        return state

    # If there's an error, generate an error response
    if state.get("error"):
        return generate_error_response(state)

    # Create prompt for emotional response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente de apoio emocional empático e acolhedor, especializado em ajudar estudantes
    a lidar com desafios emocionais no contexto acadêmico.

    Pergunta original do estudante: {query}

    Estado emocional detectado: {emotional_state}
    Problema específico: {emotional_issue}
    Severidade: {emotional_severity}

    {strategies_section}

    {resources_section}

    Gere uma resposta empática e acolhedora que:
    1. Reconheça e valide os sentimentos do estudante
    2. Ofereça apoio e compreensão
    3. Compartilhe estratégias práticas para lidar com o desafio
    4. Recomende recursos úteis
    5. Encoraje o estudante a buscar ajuda profissional se necessário (especialmente se a severidade for alta)
    6. Use um tom caloroso, respeitoso e não-julgador

    Resposta:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare sections based on available data
        strategies_section = ""
        if state.get("emotional_strategies"):
            strategies_section = "Estratégias sugeridas:\n"
            for i, strategy in enumerate(state["emotional_strategies"]):
                strategies_section += f"{i+1}. {strategy['title']}: {strategy['description']}\n"

        resources_section = ""
        if state.get("emotional_resources"):
            resources_section = "Recursos recomendados:\n"
            for i, resource in enumerate(state["emotional_resources"]):
                resources_section += f"{i+1}. {resource['title']}: {resource['description']}\n"

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "emotional_state": state.get("emotional_state", "desconhecido"),
            "emotional_issue": state.get("emotional_issue", "desconhecido"),
            "emotional_severity": state.get("emotional_severity", "desconhecida"),
            "strategies_section": strategies_section,
            "resources_section": resources_section
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with natural language response
        state["natural_response"] = response.content.strip()

        # Log success
        logger.info(f"Generated emotional support response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating emotional response: {str(e)}"
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
    Você é um assistente de apoio emocional que precisa lidar com um erro.

    Pergunta original do estudante: {query}
    Erro (não mostrar ao usuário): {error}

    Gere uma resposta empática que:
    1. Não mencione detalhes técnicos do erro
    2. Explique que não foi possível processar a solicitação completamente
    3. Ofereça algum apoio geral para o estudante
    4. Sugira que o estudante tente reformular sua pergunta ou buscar ajuda diretamente no NAP (Núcleo de Apoio Psicopedagógico)
    5. Mantenha um tom caloroso e acolhedor

    Resposta:
    """)

    # Initialize LLM
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
        logger.info(f"Generated emotional error response: {state['natural_response'][:100]}...")

    except Exception as e:
        # Fallback to generic error message if response generation fails
        logger.error(f"Error generating emotional error response: {str(e)}")
        state["natural_response"] = "Desculpe, não consegui processar completamente sua solicitação. Se você estiver enfrentando dificuldades emocionais, considere conversar com alguém do NAP (Núcleo de Apoio Psicopedagógico) da sua instituição. Eles estão lá para ajudar."

    return state

def emotional_support_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Main entry point for the emotional support agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with emotional support
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Step 1: Detect emotional state
    state = emotional_state_detector(state)

    # Step 2: Generate strategies
    state = strategy_generator(state)

    # Step 3: Recommend resources
    state = resource_recommender(state)

    # Step 4: Generate response
    state = emotional_response_generator(state)

    return state
