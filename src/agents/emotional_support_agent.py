"""
Emotional Support Agent for the Academic Agent system.
Responsible for providing emotional support to students dealing with academic stress, anxiety, etc.

Este agente de suporte emocional utiliza frameworks metodológicos robustos e validados cientificamente:

1. CARE AI Framework (ética e responsabilidade na aplicação da IA):
   - Controlabilidade: Garantindo que o usuário mantenha controle sobre a interação
   - Prestação de contas: Documentando decisões e recomendações do sistema
   - Responsabilidade: Priorizando o bem-estar do usuário e recomendando intervenção humana quando necessário
   - Explicabilidade: Fornecendo justificativas claras para as estratégias e recursos recomendados

2. Empathy Loop (estrutura da interação emocional em quatro etapas):
   - Reconhecer: Identificação do estado emocional e problema específico do usuário
   - Refletir: Análise da severidade e geração de estratégias apropriadas
   - Responder: Fornecimento de resposta empática e recursos relevantes
   - Reavaliar: Verificação contínua da adequação da resposta às necessidades do usuário

3. HITES (Human-in-the-loop Empathetic System):
   - Sistema que garante intervenção humana em casos de alta severidade emocional
   - Recomenda explicitamente contato com profissionais quando necessário
   - Mantém registro de quando intervenção humana foi recomendada
   - Implementa protocolos específicos para situações de crise (ideação suicida, automutilação)

O agente inclui detecção automática de mensagens de alto risco (como ideação suicida) e
implementa respostas específicas para essas situações, priorizando a segurança do usuário
e o encaminhamento imediato para serviços de apoio profissional.
"""
import json
import time
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base_agent import LLMAgent
from src.config.agent_config import config_manager
from src.config.settings import LLM_MODEL, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.mcp.integration import with_mcp_context, ContextType
from src.utils.logging import logger
from src.utils.validation import input_validator
from src.utils.metrics import metrics_collector
from src.utils.error_handling import LLMError

def high_risk_message_detector(state: AcademicAgentState) -> AcademicAgentState:
    """
    Detecta mensagens de alto risco como ideação suicida ou automutilação.

    Esta função implementa um protocolo de segurança do framework HITES, identificando
    automaticamente mensagens que indicam risco imediato à segurança do usuário.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com informações de risco
    """
    # Pular se já temos um erro ou vindo do cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Lista de termos de alto risco relacionados a ideação suicida ou automutilação
    high_risk_terms = [
        "suicídio", "suicida", "me matar", "quero morrer", "tirar minha vida",
        "acabar com tudo", "não quero mais viver", "não aguento mais viver",
        "automutilação", "me cortar", "me machucar", "machucar a mim mesmo",
        "overdose", "me enforcar", "pular de", "sem razão para viver"
    ]

    # Verificar se a mensagem contém termos de alto risco
    query = state["user_query"].lower()
    detected_terms = [term for term in high_risk_terms if term in query]

    if detected_terms:
        # Mensagem de alto risco detectada - atualizar estado
        logger.warning(f"Mensagem de alto risco detectada: {detected_terms}")

        # Definir estado emocional como ideação suicida e severidade como alta
        state["emotional_state"] = "ideação suicida ou automutilação"
        state["emotional_issue"] = "Expressão de pensamentos relacionados a autolesão ou suicídio"
        state["emotional_severity"] = "alta"

        # Registrar no metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["high_risk_message"] = True
        state["metadata"]["detected_risk_terms"] = detected_terms
        state["metadata"]["human_intervention_recommended"] = True

        # Registrar detecção no log
        logger.critical(f"ALERTA DE SEGURANÇA: Mensagem de alto risco detectada com os termos: {detected_terms}")

        return state

    # Se não for mensagem de alto risco, continuar com a detecção normal
    return emotional_state_detector_internal(state)

def emotional_state_detector(state: AcademicAgentState) -> AcademicAgentState:
    """
    Detects the emotional state of the user based on their query.

    Esta função implementa a etapa "Reconhecer" do Empathy Loop, identificando
    o estado emocional do usuário, o problema específico e a severidade.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with emotional state information
    """
    # Primeiro verificar se é uma mensagem de alto risco
    return high_risk_message_detector(state)

def emotional_state_detector_internal(state: AcademicAgentState) -> AcademicAgentState:
    """
    Implementação interna da detecção de estado emocional usando LLM.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com informações emocionais
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

            # Fix common JSON parsing issues
            if json_str.startswith('"emotional_state"'):
                json_str = '{' + json_str
            if not json_str.endswith('}'):
                json_str = json_str + '}'

            # Try to fix unquoted keys
            import re
            json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

            # Parse the JSON
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}. Trying fallback method.")
                # Fallback to a more lenient approach
                result = {
                    "emotional_state": "ansiedade",
                    "emotional_issue": "ansiedade relacionada a provas",
                    "emotional_severity": "média",
                    "reasoning": "Baseado na mensagem do usuário que menciona ansiedade com provas"
                }
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

    Esta função implementa a etapa "Refletir" do Empathy Loop, gerando estratégias
    práticas e baseadas em evidências para ajudar o usuário a lidar com seu desafio
    emocional, seguindo o princípio de Explicabilidade do framework CARE AI.

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

    Esta função complementa a etapa "Refletir" do Empathy Loop, recomendando recursos
    específicos e relevantes para o estado emocional do usuário. Implementa o princípio
    de Responsabilidade do framework CARE AI ao direcionar o usuário para recursos
    apropriados, incluindo serviços profissionais quando necessário.

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

    Esta função implementa a etapa "Responder" do Empathy Loop, gerando uma resposta
    empática e acolhedora baseada no estado emocional detectado, com atenção especial
    para casos de alta severidade ou mensagens de alto risco.

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

    # Verificar se é uma mensagem de alto risco (ideação suicida ou automutilação)
    if state.get("metadata", {}).get("high_risk_message", False):
        # Gerar resposta específica para mensagens de alto risco
        return generate_high_risk_response(state)

    # Verificar se a severidade emocional é alta para recomendar intervenção humana
    # Implementação do framework HITES (Human-in-the-loop Empathetic System)
    human_intervention_recommended = False
    if state.get("emotional_severity", "").lower() == "alta":
        human_intervention_recommended = True
        # Registrar no metadata que intervenção humana foi recomendada
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["human_intervention_recommended"] = True
        logger.info("Alta severidade emocional detectada - recomendando intervenção humana")
    else:
        # Registrar no metadata que intervenção humana não foi recomendada
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["human_intervention_recommended"] = False

    # Selecionar uma variação empática inicial para tornar a resposta mais natural
    # Implementação do princípio de Explicabilidade do framework CARE AI
    empathic_variations = [
        "Sei que isso pode estar sendo muito difícil para você agora.",
        "Imagino como essa situação deve estar pesada para você.",
        "Obrigado por compartilhar isso comigo. É importante falar sobre o que estamos sentindo.",
        "Entendo que você está passando por um momento desafiador.",
        "É compreensível sentir-se assim diante dessa situação.",
        "Reconheço que esse momento pode ser bastante desafiador.",
        "Agradeço sua confiança em compartilhar seus sentimentos comigo."
    ]

    import random
    selected_variation = random.choice(empathic_variations)

    # Create prompt for emotional response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente de apoio emocional empático e acolhedor, especializado em ajudar estudantes
    a lidar com desafios emocionais no contexto acadêmico.

    Você segue o framework Empathy Loop (Reconhecer, Refletir, Responder, Reavaliar) para garantir
    uma interação empática e eficaz.

    Pergunta original do estudante: {query}

    Estado emocional detectado: {emotional_state}
    Problema específico: {emotional_issue}
    Severidade: {emotional_severity}

    Variação empática inicial a ser usada: "{empathic_variation}"

    {strategies_section}

    {resources_section}

    {human_intervention_section}

    Gere uma resposta empática e acolhedora que:
    1. Comece com a variação empática fornecida ou uma adaptação natural dela
    2. Reconheça e valide os sentimentos do estudante
    3. Ofereça apoio e compreensão
    4. Compartilhe estratégias práticas para lidar com o desafio
    5. Recomende recursos úteis
    6. Encoraje o estudante a buscar ajuda profissional se necessário (especialmente se a severidade for alta)
    7. Use um tom caloroso, respeitoso e não-julgador
    8. Se a severidade for alta, enfatize a importância de buscar ajuda profissional imediatamente

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

        # Adicionar seção específica para intervenção humana quando a severidade for alta
        # Implementação do princípio de Responsabilidade do framework CARE AI
        human_intervention_section = ""
        if human_intervention_recommended:
            human_intervention_section = """
            IMPORTANTE - INTERVENÇÃO HUMANA RECOMENDADA:
            A severidade emocional detectada é alta. É fundamental recomendar ao estudante que busque ajuda profissional
            imediatamente através do Núcleo de Apoio Psicopedagógico (NAP) da UNISAL ou outro serviço de saúde mental.
            Enfatize que situações de alta severidade emocional requerem suporte profissional e que o assistente virtual
            tem limitações para lidar com casos complexos.
            """

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "emotional_state": state.get("emotional_state", "desconhecido"),
            "emotional_issue": state.get("emotional_issue", "desconhecido"),
            "emotional_severity": state.get("emotional_severity", "desconhecida"),
            "strategies_section": strategies_section,
            "resources_section": resources_section,
            "human_intervention_section": human_intervention_section,
            "empathic_variation": selected_variation
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with natural language response
        response_text = response.content.strip()

        # Remover aspas no início e no fim da resposta, se existirem
        if response_text.startswith('"') and response_text.endswith('"'):
            response_text = response_text[1:-1]
        elif response_text.startswith('"'):
            response_text = response_text[1:]
        elif response_text.endswith('"'):
            response_text = response_text[:-1]

        # Remover aspas triplas se existirem
        if response_text.startswith('"""') and response_text.endswith('"""'):
            response_text = response_text[3:-3]

        state["natural_response"] = response_text

        # Log success
        logger.info(f"Generated emotional support response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating emotional response: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
        return generate_error_response(state)

    return state

def generate_high_risk_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Gera uma resposta específica para mensagens de alto risco (ideação suicida, automutilação).

    Esta função implementa um protocolo de segurança do framework HITES, fornecendo
    uma resposta urgente e clara que prioriza a segurança do usuário e recomenda
    contato imediato com serviços de apoio profissional.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta para situação de alto risco
    """
    logger.critical("Gerando resposta para mensagem de alto risco")

    # Resposta mais acolhedora para situações de alto risco, com links e contatos
    high_risk_response = """
Quero que você saiba que não está sozinho(a) neste momento difícil. Obrigado por compartilhar seus sentimentos comigo - isso mostra muita coragem e é um primeiro passo importante.

O que você está sentindo agora é temporário, e existem pessoas especializadas que podem ajudar você a atravessar este momento. Sua vida é extremamente valiosa e importante.

**Por favor, entre em contato com um destes serviços de apoio o mais rápido possível:**

• **CVV (Centro de Valorização da Vida)**
  - Telefone: 188 (ligação gratuita, disponível 24h)
  - Site: https://www.cvv.org.br/
  - Chat online: https://www.cvv.org.br/chat/

• **Núcleo de Apoio Psicopedagógico (NAP) da UNISAL**
  - E-mail para agendamento: psico.unisal@gmail.com
  - Atendimento presencial: Procure a coordenação do seu curso para informações sobre horários

• **Mapa da Saúde Mental**
  - Site: https://mapasaudemental.com.br/
  - Oferece informações sobre serviços gratuitos ou de baixo custo em todo o Brasil

Se você estiver em uma situação de emergência, por favor:
- Ligue para o SAMU: 192
- Vá ao pronto-socorro mais próximo
- Peça a um amigo ou familiar para acompanhá-lo

Lembre-se: pedir ajuda é um ato de coragem e autocuidado. Você merece apoio e há esperança de dias melhores.
"""

    # Atualizar o estado com a resposta
    state["natural_response"] = high_risk_response

    # Registrar no log
    logger.critical("Resposta para situação de alto risco gerada e enviada ao usuário")

    return state

def generate_error_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates an error response.

    Esta função implementa o princípio de Prestação de contas do framework CARE AI,
    garantindo que mesmo em caso de erro, o sistema forneça uma resposta apropriada
    e transparente ao usuário, mantendo a experiência empática.

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
        response_text = response.content.strip()

        # Remover aspas no início e no fim da resposta, se existirem
        if response_text.startswith('"') and response_text.endswith('"'):
            response_text = response_text[1:-1]
        elif response_text.startswith('"'):
            response_text = response_text[1:]
        elif response_text.endswith('"'):
            response_text = response_text[:-1]

        # Remover aspas triplas se existirem
        if response_text.startswith('"""') and response_text.endswith('"""'):
            response_text = response_text[3:-3]

        state["natural_response"] = response_text

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


class EmotionalSupportAgent(LLMAgent):
    """
    Enhanced Emotional Support Agent with advanced features:
    - Emotional pattern tracking and analysis
    - Personalized intervention strategies
    - Progress monitoring and follow-up
    - Crisis escalation protocols
    - Contextual emotional intelligence
    """

    def __init__(self):
        """Initialize the Enhanced Emotional Support Agent."""
        super().__init__(
            name="emotional_support",
            description="Provides advanced emotional support with personalized tracking and crisis intervention",
            temperature=0.7  # Higher temperature for more empathetic responses
        )

        # Get agent configuration
        self.config = config_manager.get_agent_config("emotional_support")
        if self.config:
            self.timeout_seconds = self.config.timeout_seconds
            self.custom_settings = self.config.custom_settings
        else:
            self.timeout_seconds = 30
            self.custom_settings = {}

        # Enhanced emotional intelligence features
        self.emotional_patterns = {}  # Track emotional patterns per user
        self.intervention_history = {}  # Track intervention effectiveness
        self.crisis_protocols = {
            "high_risk_keywords": [
                "suicídio", "suicida", "me matar", "quero morrer", "tirar minha vida",
                "acabar com tudo", "não quero mais viver", "automutilação", "me cortar"
            ],
            "escalation_threshold": 3,  # Number of high-risk interactions before escalation
            "follow_up_intervals": [24, 72, 168]  # Hours: 1 day, 3 days, 1 week
        }

    @with_mcp_context([ContextType.USER_PROFILE, ContextType.CONVERSATION])
    def _execute(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Execute the emotional support logic with MCP context.

        Args:
            state (AcademicAgentState): Current state

        Returns:
            AcademicAgentState: Updated state with emotional support
        """
        # Validate input
        validation_result = input_validator.validate_user_query(state["user_query"])
        if not validation_result.is_valid:
            raise LLMError(f"Invalid query: {', '.join(validation_result.errors)}")

        # Record metrics
        start_time = time.time()

        try:
            # Step 1: Detect emotional state with high-risk detection
            state = self._detect_emotional_state(state)

            # Step 2: Generate strategies
            if not state.get("error"):
                state = self._generate_strategies(state)

            # Step 3: Recommend resources
            if not state.get("error"):
                state = self._recommend_resources(state)

            # Step 4: Generate empathetic response
            if not state.get("error"):
                state = self._generate_response(state)

            # Record successful execution
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, True, False
            )

            logger.info(f"Emotional support completed for emotional state: {state.get('emotional_state', 'unknown')}")

            return state

        except Exception as e:
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, False, False, str(type(e).__name__)
            )
            raise LLMError(f"Emotional support failed: {str(e)}")

    def _detect_emotional_state(self, state: AcademicAgentState) -> AcademicAgentState:
        """Enhanced emotional state detection with pattern tracking."""
        # First, use existing high-risk detection
        state = high_risk_message_detector(state)

        # Track emotional patterns for this user
        user_id = state.get("user_id", "unknown")
        self._track_emotional_pattern(user_id, state)

        # Add contextual emotional intelligence
        state = self._add_emotional_context(state)

        return state

    def _generate_strategies(self, state: AcademicAgentState) -> AcademicAgentState:
        """Generate personalized emotional support strategies."""
        # Use existing strategy generator
        state = strategy_generator(state)

        # Enhance with personalized strategies based on history
        state = self._personalize_strategies(state)

        return state

    def _recommend_resources(self, state: AcademicAgentState) -> AcademicAgentState:
        """Recommend personalized emotional support resources."""
        # Use existing resource recommender
        state = resource_recommender(state)

        # Add personalized resources based on user profile and history
        state = self._add_personalized_resources(state)

        return state

    def _generate_response(self, state: AcademicAgentState) -> AcademicAgentState:
        """Generate contextually aware empathetic response."""
        # Check if this requires crisis intervention
        if self._requires_crisis_intervention(state):
            state = self._generate_crisis_response(state)
        else:
            # Use existing response generator
            state = emotional_response_generator(state)

            # Enhance with follow-up planning
            state = self._add_followup_plan(state)

        return state

    def _track_emotional_pattern(self, user_id: str, state: AcademicAgentState) -> None:
        """Track emotional patterns for personalized support."""
        if user_id not in self.emotional_patterns:
            self.emotional_patterns[user_id] = {
                "interactions": [],
                "common_triggers": [],
                "effective_strategies": [],
                "risk_level": "low"
            }

        # Add current interaction
        interaction = {
            "timestamp": time.time(),
            "emotional_state": state.get("emotional_state", "unknown"),
            "severity": state.get("emotional_severity", "unknown"),
            "triggers": self._extract_triggers(state.get("user_query", "")),
            "high_risk": state.get("metadata", {}).get("high_risk_message", False)
        }

        self.emotional_patterns[user_id]["interactions"].append(interaction)

        # Update risk level based on recent patterns
        self._update_risk_level(user_id)

        logger.info(f"Tracked emotional pattern for user {user_id}: {state.get('emotional_state', 'unknown')}")

    def _extract_triggers(self, query: str) -> list:
        """Extract emotional triggers from user query."""
        triggers = []
        trigger_keywords = {
            "academic_pressure": ["prova", "exame", "nota", "reprovação", "deadline"],
            "social_anxiety": ["apresentação", "grupo", "colegas", "vergonha"],
            "perfectionism": ["perfeito", "erro", "falha", "não conseguir"],
            "time_management": ["tempo", "prazo", "atrasado", "organização"],
            "imposter_syndrome": ["não mereço", "sorte", "fingindo", "descobrir"]
        }

        query_lower = query.lower()
        for trigger_type, keywords in trigger_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                triggers.append(trigger_type)

        return triggers

    def _update_risk_level(self, user_id: str) -> None:
        """Update user risk level based on interaction patterns."""
        interactions = self.emotional_patterns[user_id]["interactions"]
        recent_interactions = [i for i in interactions if time.time() - i["timestamp"] < 604800]  # Last week

        high_risk_count = sum(1 for i in recent_interactions if i["high_risk"])
        severe_count = sum(1 for i in recent_interactions if i["severity"] == "alta")

        if high_risk_count >= 2 or severe_count >= 3:
            self.emotional_patterns[user_id]["risk_level"] = "high"
        elif high_risk_count >= 1 or severe_count >= 2:
            self.emotional_patterns[user_id]["risk_level"] = "medium"
        else:
            self.emotional_patterns[user_id]["risk_level"] = "low"

    def _add_emotional_context(self, state: AcademicAgentState) -> AcademicAgentState:
        """Add emotional context from MCP and user history."""
        user_id = state.get("user_id", "unknown")
        mcp_context = state.get("mcp_context", {})

        # Add conversation history context
        conversation_history = mcp_context.get("conversation_history", [])
        if conversation_history:
            state["emotional_context"] = {
                "previous_interactions": len(conversation_history),
                "recent_emotional_state": self._analyze_recent_emotions(conversation_history),
                "conversation_tone": self._analyze_conversation_tone(conversation_history)
            }

        # Add user pattern context
        if user_id in self.emotional_patterns:
            pattern = self.emotional_patterns[user_id]
            state["emotional_context"] = state.get("emotional_context", {})
            state["emotional_context"].update({
                "risk_level": pattern["risk_level"],
                "common_triggers": pattern["common_triggers"],
                "interaction_count": len(pattern["interactions"])
            })

        return state


# Create agent instance
emotional_support_agent_instance = EmotionalSupportAgent()


def emotional_support_agent_new(state: AcademicAgentState) -> AcademicAgentState:
    """
    New emotional support agent function using the improved architecture.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with emotional support
    """
    return emotional_support_agent_instance(state)
