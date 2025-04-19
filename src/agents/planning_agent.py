"""
Academic Planning Agent for the Academic Agent system.
Responsible for helping students plan their studies, set goals, and manage their time.
"""
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_TEMPERATURE_CREATIVE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def planning_goal_analyzer(state: AcademicAgentState) -> AcademicAgentState:
    """
    Analyzes the planning goal from the user's query.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with planning goal information
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    # Create prompt for planning goal analysis
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em planejamento acadêmico, capaz de identificar objetivos
    e necessidades de planejamento a partir de mensagens de estudantes.
    
    Mensagem do estudante: {query}
    
    Analise a mensagem e identifique:
    1. O objetivo principal de planejamento (ex: preparação para prova, organização de estudos, etc.)
    2. O período de tempo relevante (curto prazo: dias, médio prazo: semanas, longo prazo: meses)
    3. Quaisquer restrições ou desafios mencionados pelo estudante
    
    Formato da resposta:
    ```json
    {
        "planning_goal": "objetivo_identificado",
        "planning_timeframe": "curto/médio/longo",
        "planning_constraints": "restrições_ou_desafios",
        "reasoning": "seu_raciocínio_para_esta_análise"
    }
    ```
    """)
    
    # Initialize LLM with low temperature for analysis
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"]
        }
        
        # Execute the analysis
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Extract JSON from the response
        response_text = response.content
        json_str = response_text
        
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
            
        result = json.loads(json_str)
        
        # Update state with planning goal information
        state["planning_goal"] = result["planning_goal"]
        state["planning_timeframe"] = result["planning_timeframe"]
        
        # Store additional information in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["planning_constraints"] = result.get("planning_constraints", "")
        state["metadata"]["planning_reasoning"] = result.get("reasoning", "")
        
        # Log success
        logger.info(f"Analyzed planning goal: {state['planning_goal']}, timeframe: {state['planning_timeframe']}")
        
    except Exception as e:
        error_msg = f"Error analyzing planning goal: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["planning_goal_analysis_error"] = error_msg
    
    return state

def task_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates tasks for the planning goal.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with planning tasks
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    # Skip if we don't have planning goal information
    if not state.get("planning_goal") or not state.get("planning_timeframe"):
        return state
    
    # Get current date for reference
    current_date = datetime.now()
    
    # Create prompt for task generation
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em planejamento acadêmico, capaz de criar planos de estudo
    eficazes e personalizados.
    
    Objetivo de planejamento: {planning_goal}
    Período de tempo: {planning_timeframe}
    Restrições/Desafios: {planning_constraints}
    Data atual: {current_date}
    
    Crie um plano de estudo detalhado com tarefas específicas que:
    1. Sejam alinhadas ao objetivo identificado
    2. Sejam realistas para o período de tempo especificado
    3. Considerem as restrições mencionadas
    4. Incluam datas/prazos específicos
    5. Sejam específicas, mensuráveis e alcançáveis
    
    Para cada tarefa, forneça:
    1. Um título descritivo
    2. Uma descrição detalhada
    3. Uma data/prazo sugerido
    4. Uma estimativa de duração
    5. Prioridade (alta, média, baixa)
    
    Formato da resposta:
    ```json
    {
        "tasks": [
            {
                "title": "título_da_tarefa",
                "description": "descrição_detalhada",
                "deadline": "data_sugerida",
                "duration": "estimativa_de_duração",
                "priority": "alta/média/baixa"
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
            "planning_goal": state["planning_goal"],
            "planning_timeframe": state["planning_timeframe"],
            "planning_constraints": state["metadata"].get("planning_constraints", "Nenhuma restrição específica mencionada."),
            "current_date": current_date.strftime("%d/%m/%Y")
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
        
        # Update state with planning tasks
        state["planning_tasks"] = result["tasks"]
        
        # Log success
        logger.info(f"Generated {len(state['planning_tasks'])} planning tasks")
        
    except Exception as e:
        error_msg = f"Error generating planning tasks: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["task_generation_error"] = error_msg
    
    return state

def resource_recommender(state: AcademicAgentState) -> AcademicAgentState:
    """
    Recommends resources for the planning goal.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with planning resources
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    # Skip if we don't have planning goal information
    if not state.get("planning_goal") or not state.get("planning_timeframe"):
        return state
    
    # Create prompt for resource recommendation
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em planejamento acadêmico, capaz de recomendar recursos úteis
    para ajudar estudantes a alcançarem seus objetivos de estudo.
    
    Objetivo de planejamento: {planning_goal}
    Período de tempo: {planning_timeframe}
    
    Recomende 3-5 recursos que possam ajudar o estudante a alcançar seu objetivo.
    Os recursos podem incluir:
    - Ferramentas de gestão de tempo (apps, técnicas)
    - Métodos de estudo
    - Materiais de referência
    - Técnicas de produtividade
    - Estratégias de organização
    
    Para cada recurso, forneça:
    1. Um título
    2. Uma descrição breve
    3. Como este recurso pode ajudar especificamente com o objetivo do estudante
    
    Formato da resposta:
    ```json
    {
        "resources": [
            {
                "title": "título_do_recurso",
                "description": "descrição_breve",
                "relevance": "como_ajuda_com_o_objetivo"
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
            "planning_goal": state["planning_goal"],
            "planning_timeframe": state["planning_timeframe"]
        }
        
        # Execute the recommendation
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Extract JSON from the response
        response_text = response.content
        json_str = response_text
        
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
            
        result = json.loads(json_str)
        
        # Update state with planning resources
        state["planning_resources"] = result["resources"]
        
        # Log success
        logger.info(f"Recommended {len(state['planning_resources'])} planning resources")
        
    except Exception as e:
        error_msg = f"Error recommending planning resources: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["resource_recommendation_error"] = error_msg
    
    return state

def planning_response_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates a response with the planning information.
    
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
    
    # Create prompt for planning response
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente de planejamento acadêmico organizado e motivador, especializado em ajudar
    estudantes a planejar seus estudos e alcançar seus objetivos acadêmicos.
    
    Pergunta original do estudante: {query}
    
    Objetivo de planejamento identificado: {planning_goal}
    Período de tempo: {planning_timeframe}
    
    {tasks_section}
    
    {resources_section}
    
    Gere uma resposta detalhada que:
    1. Reconheça o objetivo do estudante
    2. Apresente um plano de estudo estruturado com tarefas específicas
    3. Inclua datas/prazos sugeridos
    4. Recomende recursos úteis
    5. Ofereça dicas de implementação do plano
    6. Use um tom organizado, motivador e encorajador
    
    Resposta:
    """)
    
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)
    
    try:
        # Prepare sections based on available data
        tasks_section = ""
        if state.get("planning_tasks"):
            tasks_section = "Plano de estudo sugerido:\n"
            for i, task in enumerate(state["planning_tasks"]):
                tasks_section += f"{i+1}. {task['title']} (Prazo: {task['deadline']}, Prioridade: {task['priority']})\n"
                tasks_section += f"   {task['description']}\n"
                tasks_section += f"   Duração estimada: {task['duration']}\n\n"
        
        resources_section = ""
        if state.get("planning_resources"):
            resources_section = "Recursos recomendados:\n"
            for i, resource in enumerate(state["planning_resources"]):
                resources_section += f"{i+1}. {resource['title']}: {resource['description']}\n"
                resources_section += f"   Relevância: {resource['relevance']}\n\n"
        
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "planning_goal": state.get("planning_goal", "organização de estudos"),
            "planning_timeframe": state.get("planning_timeframe", "médio prazo"),
            "tasks_section": tasks_section,
            "resources_section": resources_section
        }
        
        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))
        
        # Update state with natural language response
        state["natural_response"] = response.content.strip()
        
        # Log success
        logger.info(f"Generated planning response: {state['natural_response'][:100]}...")
        
    except Exception as e:
        error_msg = f"Error generating planning response: {str(e)}"
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
    Você é um assistente de planejamento acadêmico que precisa lidar com um erro.
    
    Pergunta original do estudante: {query}
    Erro (não mostrar ao usuário): {error}
    
    Gere uma resposta organizada que:
    1. Não mencione detalhes técnicos do erro
    2. Explique que não foi possível processar a solicitação completamente
    3. Ofereça algumas dicas gerais de planejamento acadêmico
    4. Sugira que o estudante tente reformular sua pergunta com mais detalhes
    5. Mantenha um tom organizado e prestativo
    
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
        logger.info(f"Generated planning error response: {state['natural_response'][:100]}...")
        
    except Exception as e:
        # Fallback to generic error message if response generation fails
        logger.error(f"Error generating planning error response: {str(e)}")
        state["natural_response"] = "Desculpe, não consegui processar completamente sua solicitação de planejamento. Tente fornecer mais detalhes sobre seus objetivos de estudo, prazos e quaisquer restrições que você tenha."
    
    return state

def planning_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Main entry point for the planning agent.
    
    Args:
        state (AcademicAgentState): Current state
        
    Returns:
        AcademicAgentState: Updated state with planning response
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state
    
    # Step 1: Analyze planning goal
    state = planning_goal_analyzer(state)
    
    # Step 2: Generate tasks
    state = task_generator(state)
    
    # Step 3: Recommend resources
    state = resource_recommender(state)
    
    # Step 4: Generate response
    state = planning_response_generator(state)
    
    return state
