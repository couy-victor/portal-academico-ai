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
            
        result = json.loads(json_str)
        
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
            
        result = json.loads(json_str)
        
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
    
    Explicação preparada: {explanation}
    
    {examples_section}
    
    Gere uma resposta tutorial completa que:
    1. Cumprimente o estudante de forma amigável
    2. Apresente a explicação de forma clara e estruturada
    3. Inclua exemplos práticos para ilustrar o conceito
    4. Forneça exercícios para praticar, com suas respectivas soluções
    5. Encoraje o estudante a fazer perguntas adicionais se necessário
    6. Use um tom educacional, paciente e encorajador
    
    Resposta:
    """)
    
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)
    
    try:
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
        
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "subject": state.get("subject", "desconhecida"),
            "explanation": state.get("explanation", "Não foi possível gerar uma explicação."),
            "examples_section": examples_section
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
    
    # Step 1: Classify subject and topic
    state = subject_classifier(state)
    
    # Step 2: Generate explanation
    state = explanation_generator(state)
    
    # Step 3: Generate examples and exercises
    state = example_generator(state)
    
    # Step 4: Generate response
    state = tutor_response_generator(state)
    
    return state
