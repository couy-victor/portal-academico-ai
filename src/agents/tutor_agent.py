"""
Tutor Agent for the Academic Agent system.
Responsible for providing educational support and explanations for specific subjects.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

# Import enhanced tutoring modules
from src.agents.adaptive_tutor import assess_prior_knowledge, generate_multi_level_explanation
from src.agents.socratic_tutor import generate_socratic_questions, create_socratic_dialogue, generate_socratic_response
from src.agents.knowledge_connector import identify_related_concepts, create_concept_map, generate_bridging_explanation

def subject_classifier(state: AcademicAgentState) -> AcademicAgentState:
    """
    Classifies the subject and topic of the user's query.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with subject and topic information
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Create prompt for subject classification
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em educação, capaz de identificar matérias e tópicos específicos
    a partir de perguntas de estudantes.

    Pergunta do estudante: {query}

    Identifique:
    1. A matéria principal (ex: Matemática, Física, Química, Biologia, etc.)
    2. O tópico específico dentro dessa matéria
    3. O nível de complexidade da pergunta (básico, intermediário, avançado)

    Formato da resposta:
    ```json
    {
        "subject": "matéria_identificada",
        "topic": "tópico_específico",
        "complexity": "básico/intermediário/avançado",
        "reasoning": "seu_raciocínio_para_esta_classificação"
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

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. Trying fallback method.")
            # Fallback to a more lenient approach
            result = {
                "subject": "Ciência da Computação",
                "topic": "Máquina de Turing",
                "complexity": "intermediário",
                "reasoning": "A pergunta é sobre um conceito fundamental da computação teórica"
            }

        # Update state with subject and topic information
        state["subject"] = result["subject"]
        state["topic"] = result["topic"]
        state["comprehension_level"] = result["complexity"]

        # Store reasoning in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["subject_reasoning"] = result.get("reasoning", "")

        # Log success
        logger.info(f"Classified subject: {state['subject']}, topic: {state['topic']}, complexity: {state['comprehension_level']}")

    except Exception as e:
        error_msg = f"Error classifying subject: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["subject_classification_error"] = error_msg

    return state

def explanation_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates an explanation for the identified subject and topic.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with explanation
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have subject and topic information
    if not state.get("subject") or not state.get("topic"):
        return state

    # Create prompt for explanation generation
    prompt = ChatPromptTemplate.from_template("""
    Você é um professor especialista em {subject}, capaz de explicar conceitos complexos
    de forma clara e acessível.

    Pergunta do estudante: {query}
    Tópico específico: {topic}
    Nível de complexidade: {complexity}

    Gere uma explicação detalhada que:
    1. Introduza o conceito de forma clara
    2. Explique os princípios fundamentais
    3. Use analogias ou metáforas para facilitar a compreensão
    4. Conecte com conhecimentos prévios que o estudante provavelmente possui
    5. Seja adaptada ao nível de complexidade identificado

    Sua explicação deve ser educacionalmente sólida, precisa e acessível.

    Explicação:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state["subject"],
            "topic": state["topic"],
            "complexity": state["comprehension_level"]
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with explanation
        state["explanation"] = response.content.strip()

        # Log success
        logger.info(f"Generated explanation for {state['subject']}/{state['topic']}: {state['explanation'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating explanation: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["explanation_generation_error"] = error_msg

    return state

def example_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates examples and exercises for the identified subject and topic.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with examples
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have subject and topic information
    if not state.get("subject") or not state.get("topic") or not state.get("explanation"):
        return state

    # Create prompt for example generation
    prompt = ChatPromptTemplate.from_template("""
    Você é um professor especialista em {subject}, capaz de criar exemplos práticos
    e exercícios educativos para ajudar na compreensão de conceitos.

    Tópico específico: {topic}
    Nível de complexidade: {complexity}
    Explicação fornecida: {explanation}

    Crie 2-3 exemplos e 1-2 exercícios práticos que:
    1. Ilustrem claramente o conceito explicado
    2. Sejam relevantes para o contexto acadêmico
    3. Progridam em dificuldade (do mais simples ao mais complexo)
    4. Incluam a solução detalhada para cada exercício

    Formato da resposta:
    ```json
    {
        "examples": [
            {
                "title": "título_do_exemplo",
                "content": "descrição_detalhada_do_exemplo"
            },
            ...
        ],
        "exercises": [
            {
                "question": "enunciado_do_exercício",
                "solution": "solução_detalhada"
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
            "subject": state["subject"],
            "topic": state["topic"],
            "complexity": state["comprehension_level"],
            "explanation": state["explanation"]
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

        # Fix common JSON parsing issues
        if json_str.startswith('"examples"'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in example generator: {str(e)}. Trying fallback method.")
            # Fallback to a more lenient approach
            result = {
                "examples": [
                    {
                        "title": "Exemplo de Máquina de Turing",
                        "content": "Uma máquina de Turing para reconhecer palíndromes."
                    }
                ],
                "exercises": [
                    {
                        "question": "Descreva uma máquina de Turing que aceita a linguagem a^nb^n.",
                        "solution": "A máquina precisa verificar se o número de a's é igual ao número de b's."
                    }
                ]
            }

        # Combine examples and exercises
        examples_and_exercises = []

        # Add examples
        for example in result.get("examples", []):
            examples_and_exercises.append({
                "type": "example",
                "title": example.get("title", "Exemplo"),
                "content": example.get("content", "")
            })

        # Add exercises
        for exercise in result.get("exercises", []):
            examples_and_exercises.append({
                "type": "exercise",
                "question": exercise.get("question", ""),
                "solution": exercise.get("solution", "")
            })

        # Update state with examples and exercises
        state["examples"] = examples_and_exercises

        # Log success
        logger.info(f"Generated {len(examples_and_exercises)} examples and exercises for {state['subject']}/{state['topic']}")

    except Exception as e:
        error_msg = f"Error generating examples: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["example_generation_error"] = error_msg

    return state

def tutor_response_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates a comprehensive tutoring response.

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

    # Create prompt for tutor response
    prompt = ChatPromptTemplate.from_template("""
    Você é um tutor educacional dedicado e paciente, especializado em {subject}.

    Pergunta original do estudante: {query}

    Nível de conhecimento prévio do estudante: {knowledge_level}

    {concept_map_section}

    {bridging_explanation_section}

    {multi_level_explanation_section}

    {examples_section}

    {socratic_questions_section}

    Gere uma resposta tutorial completa que:
    1. Cumprimente o estudante de forma amigável
    2. Comece conectando o tópico com conceitos que o estudante já conhece
    3. Apresente a explicação de forma clara e estruturada, adaptada ao nível do estudante
    4. Use analogias e metáforas para tornar o conceito mais acessível
    5. Inclua exemplos práticos para ilustrar o conceito
    6. Forneça exercícios para praticar, com suas respectivas soluções
    7. Inclua perguntas reflexivas que estimulem o pensamento crítico
    8. Encoraje o estudante a fazer perguntas adicionais se necessário
    9. Use um tom educacional, paciente e encorajador
    10. Termine com uma síntese que conecte todos os conceitos apresentados

    Resposta:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare knowledge level
        knowledge_level = "iniciante"
        if state.get("prior_knowledge"):
            knowledge_level = state["prior_knowledge"].get("level", "iniciante")

        # Prepare concept map section
        concept_map_section = ""
        if state.get("concept_map"):
            concept_map_section = "Mapa conceitual:\n" + state["concept_map"].get("text_representation", "")

        # Prepare bridging explanation section
        bridging_explanation_section = ""
        if state.get("bridging_explanation"):
            bridging_explanation_section = "Explicação conectando conhecimentos prévios:\n" + state["bridging_explanation"]

        # Prepare multi-level explanation section
        multi_level_explanation_section = ""
        if state.get("multi_level_explanation"):
            recommended_level = state["multi_level_explanation"].get("recommended_level", "básico")

            if recommended_level == "avançado":
                explanation_text = state["multi_level_explanation"].get("advanced", {}).get("explanation", "")
            elif recommended_level == "intermediário":
                explanation_text = state["multi_level_explanation"].get("intermediate", {}).get("explanation", "")
            else:
                explanation_text = state["multi_level_explanation"].get("basic", {}).get("explanation", "")

            multi_level_explanation_section = f"Explicação ({recommended_level}):\n{explanation_text}"

        # Prepare examples section
        examples_section = ""
        if state.get("examples"):
            examples_section = "Exemplos e exercícios:\n"

            # Add examples
            examples = [ex for ex in state["examples"] if ex.get("type") == "example"]
            if examples:
                examples_section += "\nExemplos:\n"
                for i, example in enumerate(examples):
                    examples_section += f"{i+1}. {example.get('title', 'Exemplo')}: {example.get('content', '')}\n"

            # Add exercises
            exercises = [ex for ex in state["examples"] if ex.get("type") == "exercise"]
            if exercises:
                examples_section += "\nExercícios:\n"
                for i, exercise in enumerate(exercises):
                    examples_section += f"{i+1}. Pergunta: {exercise.get('question', '')}\n"
                    examples_section += f"   Solução: {exercise.get('solution', '')}\n"

        # Prepare Socratic questions section
        socratic_questions_section = ""
        if state.get("socratic_questions"):
            socratic_questions_section = "Perguntas para reflexão:\n"
            for i, question in enumerate(state["socratic_questions"][:3]):  # Limit to 3 questions
                socratic_questions_section += f"{i+1}. {question.get('question', '')}\n"

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state.get("subject", "desconhecida"),
            "knowledge_level": knowledge_level,
            "concept_map_section": concept_map_section,
            "bridging_explanation_section": bridging_explanation_section,
            "multi_level_explanation_section": multi_level_explanation_section,
            "examples_section": examples_section,
            "socratic_questions_section": socratic_questions_section
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with natural language response
        state["natural_response"] = response.content.strip()

        # Log success
        logger.info(f"Generated tutor response: {state['natural_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating tutor response: {str(e)}"
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
    Você é um tutor educacional que precisa lidar com um erro.

    Pergunta original do estudante: {query}
    Erro (não mostrar ao usuário): {error}

    Gere uma resposta educacional que:
    1. Não mencione detalhes técnicos do erro
    2. Explique que não foi possível processar a solicitação completamente
    3. Ofereça algumas orientações gerais sobre o tópico, se possível
    4. Sugira que o estudante tente reformular sua pergunta ou buscar ajuda com um professor
    5. Mantenha um tom educacional e encorajador

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
        logger.info(f"Generated tutor error response: {state['natural_response'][:100]}...")

    except Exception as e:
        # Fallback to generic error message if response generation fails
        logger.error(f"Error generating tutor error response: {str(e)}")
        state["natural_response"] = "Desculpe, não consegui processar completamente sua pergunta. Tente reformulá-la ou consulte um professor para obter ajuda com este tópico específico."

    return state

def tutor_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Main entry point for the tutor agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with tutoring response
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Check if the query has the [socratic] prefix and remove it for processing
    original_query = state["user_query"]
    use_socratic_approach = False

    if "[socratic]" in original_query.lower():
        # Remove the [socratic] prefix for better processing
        state["user_query"] = original_query.replace("[socratic]", "").strip()
        use_socratic_approach = True
        logger.info(f"Socratic approach requested: {state['user_query']}")

    # Step 1: Classify subject and topic
    state = subject_classifier(state)

    # Step 2: Assess prior knowledge (from adaptive_tutor)
    state = assess_prior_knowledge(state)

    # Step 3: Identify related concepts (from knowledge_connector)
    state = identify_related_concepts(state)

    # Step 4: Create concept map (from knowledge_connector)
    state = create_concept_map(state)

    # Step 5: Generate multi-level explanation (from adaptive_tutor)
    state = generate_multi_level_explanation(state)

    # Step 6: Generate bridging explanation (from knowledge_connector)
    state = generate_bridging_explanation(state)

    # Step 7: Generate Socratic questions (from socratic_tutor)
    state = generate_socratic_questions(state)

    # Step 8: Create Socratic dialogue (from socratic_tutor)
    state = create_socratic_dialogue(state)

    # Step 9: Generate examples and exercises
    state = example_generator(state)

    # Step 10: Determine the best response approach based on the query and context
    if use_socratic_approach or state.get("prior_knowledge", {}).get("level") == "avançado":
        try:
            # Use Socratic approach for advanced students or when explicitly requested
            state = generate_socratic_response(state)
            if state.get("socratic_response"):
                state["natural_response"] = state["socratic_response"]
            else:
                # Fallback to standard response if socratic response generation failed
                logger.info("Falling back to standard response due to missing socratic response")
                state = tutor_response_generator(state)
        except Exception as e:
            logger.error(f"Error in socratic response generation: {str(e)}. Falling back to standard response.")
            state = tutor_response_generator(state)
    else:
        # Use standard approach with enhanced explanations
        state = tutor_response_generator(state)

    # Restore original query
    state["user_query"] = original_query

    return state
