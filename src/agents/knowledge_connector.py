"""
Knowledge Connector Module for the Academic Agent system.
Connects new concepts with the student's existing knowledge.
"""
import json
from typing import Dict, Any, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def identify_related_concepts(state: AcademicAgentState) -> AcademicAgentState:
    """
    Identifies concepts related to the current topic that the student likely already knows.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with related concepts
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have subject and topic information
    if not state.get("subject") or not state.get("topic"):
        return state

    # Create prompt for related concepts
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em mapeamento de conhecimento em {subject}, capaz de identificar
    conexões entre diferentes conceitos e tópicos.

    Tópico atual: {topic}
    Nível acadêmico estimado: {academic_level}

    Identifique:
    1. Conceitos fundamentais que um estudante provavelmente já conhece e que estão relacionados a este tópico
    2. Conceitos de outras disciplinas que podem ser conectados a este tópico
    3. Experiências cotidianas que podem servir como analogias para este tópico
    4. Conhecimentos prévios específicos necessários para compreender este tópico

    Para cada conceito, forneça:
    - Nome do conceito
    - Breve descrição
    - Como se relaciona com o tópico atual
    - Nível de relevância (alta, média, baixa)

    Formato da resposta:
    ```json
    {
        "prerequisite_concepts": [
            {
                "name": "nome_do_conceito",
                "description": "breve_descrição",
                "relation": "como_se_relaciona",
                "relevance": "alta/média/baixa"
            },
            ...
        ],
        "interdisciplinary_concepts": [
            {
                "name": "nome_do_conceito",
                "discipline": "disciplina_relacionada",
                "description": "breve_descrição",
                "relation": "como_se_relaciona",
                "relevance": "alta/média/baixa"
            },
            ...
        ],
        "everyday_analogies": [
            {
                "analogy": "descrição_da_analogia",
                "explanation": "como_se_relaciona_com_o_tópico",
                "effectiveness": "alta/média/baixa"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Determine academic level
        academic_level = "ensino médio"
        if "user_context" in state and "curso" in state["user_context"]:
            curso = state["user_context"]["curso"].lower()
            if "graduação" in curso or "superior" in curso:
                academic_level = "graduação"
            elif "pós" in curso or "mestrado" in curso or "doutorado" in curso:
                academic_level = "pós-graduação"

        # Prepare inputs
        inputs = {
            "subject": state["subject"],
            "topic": state["topic"],
            "academic_level": academic_level
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
                "prerequisite_concepts": [
                    {"name": "Conceito básico", "description": "Fundamento da área", "relation": "Pré-requisito", "relevance": "alta"}
                ],
                "interdisciplinary_concepts": [
                    {"name": "Conceito relacionado", "discipline": "Área relacionada", "description": "Conexão interdisciplinar", "relation": "Complementar", "relevance": "média"}
                ],
                "everyday_analogies": [
                    {"analogy": "Analogia cotidiana", "explanation": "Explicação da analogia", "effectiveness": "alta"}
                ]
            }

        # Update state with related concepts
        state["related_concepts"] = {
            "prerequisites": result.get("prerequisite_concepts", []),
            "interdisciplinary": result.get("interdisciplinary_concepts", []),
            "analogies": result.get("everyday_analogies", [])
        }

        # Log success
        logger.info(f"Identified related concepts for {state['subject']}/{state['topic']}")

    except Exception as e:
        error_msg = f"Error identifying related concepts: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["related_concepts_error"] = error_msg

    return state

def create_concept_map(state: AcademicAgentState) -> AcademicAgentState:
    """
    Creates a textual concept map connecting the current topic with related concepts.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with concept map
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have related concepts
    if not state.get("related_concepts"):
        return state

    # Create prompt for concept map
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em mapas conceituais educacionais, capaz de criar representações
    visuais de como diferentes conceitos se relacionam.

    Tópico central: {topic}
    Disciplina: {subject}

    Conceitos relacionados:
    {related_concepts}

    Crie um mapa conceitual textual que:
    1. Tenha o tópico central como ponto focal
    2. Conecte os conceitos relacionados de forma hierárquica e significativa
    3. Mostre as relações entre os diferentes conceitos
    4. Destaque as conexões interdisciplinares
    5. Inclua analogias cotidianas como pontos de referência

    O mapa deve ser claro, organizado e educacionalmente útil.

    Formato da resposta:
    ```json
    {
        "concept_map": "representação_textual_do_mapa_conceitual",
        "central_concept": {
            "name": "nome_do_conceito_central",
            "description": "breve_descrição"
        },
        "primary_connections": [
            {
                "concept": "nome_do_conceito",
                "relation": "tipo_de_relação",
                "description": "descrição_da_conexão"
            },
            ...
        ],
        "secondary_connections": [
            {
                "from": "conceito_origem",
                "to": "conceito_destino",
                "relation": "tipo_de_relação",
                "description": "descrição_da_conexão"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Format related concepts for the prompt
        related_concepts_text = "Pré-requisitos:\n"
        for concept in state["related_concepts"]["prerequisites"]:
            related_concepts_text += f"- {concept.get('name', '')}: {concept.get('description', '')}\n"

        related_concepts_text += "\nConceitos interdisciplinares:\n"
        for concept in state["related_concepts"]["interdisciplinary"]:
            related_concepts_text += f"- {concept.get('name', '')} ({concept.get('discipline', '')}): {concept.get('description', '')}\n"

        related_concepts_text += "\nAnalogias cotidianas:\n"
        for analogy in state["related_concepts"]["analogies"]:
            related_concepts_text += f"- {analogy.get('analogy', '')}: {analogy.get('explanation', '')}\n"

        # Prepare inputs
        inputs = {
            "subject": state["subject"],
            "topic": state["topic"],
            "related_concepts": related_concepts_text
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
                "concept_map": f"Mapa conceitual para {state['topic']} em {state['subject']}",
                "central_concept": {
                    "name": state['topic'],
                    "description": "Conceito central do tópico"
                },
                "primary_connections": [
                    {"concept": "Conceito relacionado", "relation": "relaciona-se com", "description": "Conexão primária"}
                ],
                "secondary_connections": [
                    {"from": "Conceito A", "to": "Conceito B", "relation": "influencia", "description": "Conexão secundária"}
                ]
            }

        # Update state with concept map
        state["concept_map"] = {
            "text_representation": result.get("concept_map", ""),
            "central_concept": result.get("central_concept", {}),
            "primary_connections": result.get("primary_connections", []),
            "secondary_connections": result.get("secondary_connections", [])
        }

        # Log success
        logger.info(f"Created concept map for {state['subject']}/{state['topic']}")

    except Exception as e:
        error_msg = f"Error creating concept map: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["concept_map_error"] = error_msg

    return state

def generate_bridging_explanation(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates an explanation that bridges prior knowledge with new concepts.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with bridging explanation
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    # Skip if we don't have concept map
    if not state.get("concept_map"):
        return state

    # Create prompt for bridging explanation
    prompt = ChatPromptTemplate.from_template("""
    Você é um professor especialista em {subject}, capaz de criar explicações que conectam
    o conhecimento prévio dos estudantes com novos conceitos.

    Pergunta original do estudante: {query}
    Tópico: {topic}

    Mapa conceitual:
    {concept_map}

    Crie uma explicação que:
    1. Comece com conceitos que o estudante provavelmente já conhece
    2. Use analogias cotidianas para introduzir o tópico
    3. Construa gradualmente a compreensão, conectando o familiar com o novo
    4. Destaque conexões interdisciplinares relevantes
    5. Termine com uma síntese que integre todos os conceitos

    A explicação deve ser clara, envolvente e construída sobre o conhecimento prévio do estudante.

    Explicação:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Prepare concept map for the prompt
        concept_map_text = state["concept_map"]["text_representation"]

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state["subject"],
            "topic": state["topic"],
            "concept_map": concept_map_text
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Update state with bridging explanation
        state["bridging_explanation"] = response.content.strip()

        # If we don't have a regular explanation yet, use this one
        if not state.get("explanation"):
            state["explanation"] = state["bridging_explanation"]

        # Log success
        logger.info(f"Generated bridging explanation for {state['subject']}/{state['topic']}")

    except Exception as e:
        error_msg = f"Error generating bridging explanation: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["bridging_explanation_error"] = error_msg

    return state
