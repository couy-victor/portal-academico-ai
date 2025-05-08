"""
Socratic Tutor Module for the Academic Agent system.
Implements Socratic questioning techniques to promote critical thinking.
"""
import json
from typing import Dict, Any, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def generate_socratic_questions(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates Socratic questions to guide the student's thinking process.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with Socratic questions
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have subject and topic information
    if not state.get("subject") or not state.get("topic"):
        return state

    # Create prompt for Socratic questions
    prompt = ChatPromptTemplate.from_template("""
    Você é um tutor socrático especializado em {subject}, capaz de guiar estudantes através
    de um processo de descoberta usando perguntas estratégicas.

    Pergunta original do estudante: {query}
    Tópico específico: {topic}

    Gere uma série de perguntas socráticas que:
    1. Comecem com questões mais amplas e progridam para questões mais específicas
    2. Ajudem o estudante a descobrir a resposta por conta própria
    3. Estimulem o pensamento crítico e a reflexão
    4. Identifiquem e desafiem pressupostos
    5. Explorem implicações e consequências

    Para cada pergunta, forneça:
    - A pergunta em si
    - O propósito pedagógico da pergunta
    - Possíveis respostas do estudante
    - Perguntas de acompanhamento baseadas nas possíveis respostas

    Formato da resposta:
    ```json
    {
        "questions": [
            {
                "question": "pergunta_socrática",
                "purpose": "propósito_pedagógico",
                "possible_answers": [
                    {
                        "answer": "possível_resposta_1",
                        "follow_up": "pergunta_de_acompanhamento_1"
                    },
                    {
                        "answer": "possível_resposta_2",
                        "follow_up": "pergunta_de_acompanhamento_2"
                    }
                ]
            },
            ...
        ],
        "conclusion_guidance": "orientação_para_conclusão"
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state["subject"],
            "topic": state["topic"]
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
                "questions": [
                    {
                        "question": "O que você entende por este conceito?",
                        "purpose": "Avaliar o conhecimento prévio do estudante",
                        "possible_answers": []
                    }
                ],
                "conclusion_guidance": "Guiar o estudante a uma compreensão básica do conceito"
            }

        # Update state with Socratic questions
        state["socratic_questions"] = result.get("questions", [])
        state["socratic_conclusion"] = result.get("conclusion_guidance", "")

        # Log success
        logger.info(f"Generated {len(state['socratic_questions'])} Socratic questions for {state['subject']}/{state['topic']}")

    except Exception as e:
        error_msg = f"Error generating Socratic questions: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["socratic_questions_error"] = error_msg

    return state

def create_socratic_dialogue(state: AcademicAgentState) -> AcademicAgentState:
    """
    Creates a simulated Socratic dialogue to demonstrate the thinking process.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with Socratic dialogue
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have Socratic questions
    if not state.get("socratic_questions"):
        return state

    # Create prompt for Socratic dialogue
    prompt = ChatPromptTemplate.from_template("""
    Você é um tutor socrático especializado em {subject}, capaz de criar diálogos educacionais
    que demonstram o processo de pensamento crítico.

    Tópico específico: {topic}
    Perguntas socráticas disponíveis:
    {socratic_questions}

    Crie um diálogo socrático entre um tutor e um estudante que:
    1. Comece com a pergunta original do estudante
    2. Use as perguntas socráticas para guiar o estudante
    3. Mostre como o estudante desenvolve seu pensamento ao longo do diálogo
    4. Termine com o estudante chegando à conclusão por conta própria
    5. Inclua momentos de confusão, esclarecimento e descoberta

    O diálogo deve ser natural, educacional e demonstrar claramente o valor da abordagem socrática.

    Formato da resposta:
    ```json
    {
        "dialogue": [
            {
                "speaker": "estudante/tutor",
                "text": "fala_do_diálogo"
            },
            ...
        ],
        "key_insights": ["insight_1", "insight_2", ...],
        "learning_outcomes": ["outcome_1", "outcome_2", ...]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Format Socratic questions for the prompt
        socratic_questions_text = ""
        for i, q in enumerate(state["socratic_questions"]):
            socratic_questions_text += f"{i+1}. {q.get('question', '')}\n"
            socratic_questions_text += f"   Propósito: {q.get('purpose', '')}\n"

        # Prepare inputs
        inputs = {
            "subject": state["subject"],
            "topic": state["topic"],
            "socratic_questions": socratic_questions_text
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
                "dialogue": [
                    {"speaker": "tutor", "text": "Vamos explorar este conceito juntos."},
                    {"speaker": "estudante", "text": "Estou pronto para aprender."}
                ],
                "key_insights": ["Compreensão básica do conceito"],
                "learning_outcomes": ["Entendimento fundamental do tópico"]
            }

        # Update state with Socratic dialogue
        state["socratic_dialogue"] = result.get("dialogue", [])
        state["socratic_insights"] = result.get("key_insights", [])
        state["socratic_outcomes"] = result.get("learning_outcomes", [])

        # Log success
        logger.info(f"Created Socratic dialogue with {len(state['socratic_dialogue'])} exchanges")

    except Exception as e:
        error_msg = f"Error creating Socratic dialogue: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["socratic_dialogue_error"] = error_msg

    return state

def generate_socratic_response(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates a response that incorporates Socratic elements.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with Socratic response
    """
    # Skip if we already have a natural response
    if state.get("natural_response"):
        return state

    # Skip if we don't have the necessary Socratic elements
    if not state.get("socratic_questions") and not state.get("socratic_dialogue"):
        return state

    # Create prompt for Socratic response
    prompt = ChatPromptTemplate.from_template("""
    Você é um tutor socrático especializado em {subject}, capaz de criar respostas
    que estimulam o pensamento crítico e a descoberta.

    Pergunta original do estudante: {query}

    {explanation_section}

    {dialogue_section}

    {questions_section}

    Crie uma resposta que:
    1. Reconheça a pergunta do estudante
    2. Forneça uma breve introdução ao tópico
    3. Apresente um diálogo socrático que demonstre o processo de pensamento
    4. Inclua perguntas guiadas que o estudante pode explorar
    5. Encoraje o estudante a desenvolver seu próprio raciocínio
    6. Termine com uma conclusão que sintetize os principais insights

    A resposta deve ser educacional, envolvente e promover a autonomia intelectual do estudante.

    Resposta:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare explanation section
        explanation_section = ""
        if state.get("explanation"):
            explanation_section = f"Explicação do tópico:\n{state['explanation'][:500]}..."

        # Prepare dialogue section
        dialogue_section = ""
        if state.get("socratic_dialogue"):
            dialogue_section = "Diálogo socrático:\n"
            for exchange in state["socratic_dialogue"][:5]:  # Limit to first 5 exchanges
                speaker = exchange.get("speaker", "")
                text = exchange.get("text", "")
                dialogue_section += f"{speaker}: {text}\n"

        # Prepare questions section
        questions_section = ""
        if state.get("socratic_questions"):
            questions_section = "Perguntas socráticas:\n"
            for i, q in enumerate(state["socratic_questions"][:3]):  # Limit to first 3 questions
                questions_section += f"{i+1}. {q.get('question', '')}\n"

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state["subject"],
            "explanation_section": explanation_section,
            "dialogue_section": dialogue_section,
            "questions_section": questions_section
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with Socratic response
        state["socratic_response"] = response.content.strip()

        # Log success
        logger.info(f"Generated Socratic response: {state['socratic_response'][:100]}...")

    except Exception as e:
        error_msg = f"Error generating Socratic response: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["socratic_response_error"] = error_msg

    return state
