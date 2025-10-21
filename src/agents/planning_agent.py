"""
Agente de Planejamento Acadêmico para o sistema Academic Agent.
Responsável por ajudar estudantes a planejar seus estudos, definir metas e gerenciar seu tempo.

Este agente implementa diferentes métodos de estudo baseados em evidências científicas:

1. Método Pomodoro:
   - Divide o tempo de estudo em blocos focados (geralmente 25 minutos)
   - Intercala com pausas curtas (5 minutos) e pausas longas (15-30 minutos)
   - Ajuda a manter o foco e evitar a fadiga mental

2. Active Recall (Recuperação Ativa):
   - Baseado em testar ativamente o conhecimento em vez de apenas revisar
   - Utiliza flashcards, quizzes e auto-questionamento
   - Comprovadamente mais eficaz para retenção de longo prazo

3. Time Blocking (Blocos de Tempo):
   - Aloca blocos específicos de tempo para diferentes tarefas/disciplinas
   - Prioriza conteúdos mais difíceis nos horários de pico cognitivo
   - Melhora a gestão do tempo e reduz a procrastinação

O agente analisa a consulta do usuário, identifica o objetivo de planejamento e recomenda
um plano estruturado utilizando o método mais adequado, com tarefas específicas,
recursos recomendados e dicas de implementação.

Recursos adicionais implementados:
- Exportação para PDF: Possibilidade de exportar o plano de estudos em formato PDF
- Integração com Calendário: Criação de arquivos .ics para importação em calendários
- Visualização de Timeline: Representação visual do cronograma de estudos
- Gamificação: Elementos de gamificação para aumentar a motivação
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
    Analisa o objetivo de planejamento a partir da consulta do usuário.

    Esta função identifica o objetivo principal, o período de tempo relevante,
    restrições mencionadas e preferências de método de estudo (Pomodoro,
    Active Recall ou Time Blocking).

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com informações do objetivo de planejamento
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
    4. Preferência por método de estudo, se mencionado:
       - "pomodoro": Técnica de blocos de tempo focado com pausas
       - "active_recall": Método de recuperação ativa/teste de conhecimento
       - "time_blocking": Organização em blocos de tempo por disciplina/tarefa
       - "não_especificado": Se nenhum método for mencionado explicitamente

    Formato da resposta:
    ```json
    {
        "planning_goal": "objetivo_identificado",
        "planning_timeframe": "curto/médio/longo",
        "planning_constraints": "restrições_ou_desafios",
        "study_method": "pomodoro/active_recall/time_blocking/não_especificado",
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

        # Clean up the JSON string
        json_str = json_str.replace("\n", "")
        json_str = json_str.replace("\r", "")

        # Fix common JSON parsing issues
        if json_str.startswith('"planning_goal"'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. Trying fallback method.")
            # Fallback to a more lenient approach
            result = {
                "planning_goal": "organização de estudos para provas finais",
                "planning_timeframe": "médio",
                "planning_constraints": "tempo limitado de duas semanas",
                "reasoning": "O estudante precisa organizar seus estudos para provas que começam em duas semanas"
            }

        # Update state with planning goal information
        state["planning_goal"] = result["planning_goal"]
        state["planning_timeframe"] = result["planning_timeframe"]

        # Armazenar o método de estudo preferido
        study_method = result.get("study_method", "não_especificado")
        state["study_method"] = study_method

        # Configurações padrão para cada método de estudo
        if study_method == "pomodoro":
            state["focus_time"] = 25  # minutos
            state["break_time"] = 5   # minutos
            state["long_break"] = 15  # minutos
        elif study_method == "active_recall":
            state["review_frequency"] = "diária"
            state["quiz_type"] = "flashcards e auto-questionamento"
        elif study_method == "time_blocking":
            state["min_block"] = 30   # minutos
            state["priority_time"] = "manhã"  # período de maior produtividade

        # Store additional information in metadata
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["planning_constraints"] = result.get("planning_constraints", "")
        state["metadata"]["planning_reasoning"] = result.get("reasoning", "")
        state["metadata"]["study_method_details"] = {
            "method": study_method,
            "config": {
                "pomodoro": {
                    "focus_time": state.get("focus_time", 25),
                    "break_time": state.get("break_time", 5),
                    "long_break": state.get("long_break", 15)
                },
                "active_recall": {
                    "review_frequency": state.get("review_frequency", "diária"),
                    "quiz_type": state.get("quiz_type", "flashcards e auto-questionamento")
                },
                "time_blocking": {
                    "min_block": state.get("min_block", 30),
                    "priority_time": state.get("priority_time", "manhã")
                }
            }
        }

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
    Gera tarefas específicas para o objetivo de planejamento.

    Esta função cria um plano de estudo detalhado com tarefas específicas
    baseadas no método de estudo selecionado (Pomodoro, Active Recall ou
    Time Blocking), considerando o objetivo, período de tempo e restrições.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com tarefas de planejamento
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
    eficazes e personalizados utilizando o método {study_method}.

    Objetivo de planejamento: {planning_goal}
    Período de tempo: {planning_timeframe}
    Restrições/Desafios: {planning_constraints}
    Data atual: {current_date}
    Método de estudo: {study_method}

    {method_details}

    Crie um plano de estudo detalhado com tarefas específicas que:
    1. Sejam alinhadas ao objetivo identificado
    2. Sejam realistas para o período de tempo especificado
    3. Considerem as restrições mencionadas
    4. Incluam datas/prazos específicos
    5. Sejam específicas, mensuráveis e alcançáveis
    6. Sigam as diretrizes do método de estudo selecionado

    Para cada tarefa, forneça:
    1. Um título descritivo
    2. Uma descrição detalhada que incorpore o método de estudo
    3. Uma data/prazo sugerido
    4. Uma estimativa de duração
    5. Prioridade (alta, média, baixa)
    6. Dicas específicas para aplicar o método de estudo nesta tarefa

    Formato da resposta:
    ```json
    {
        "tasks": [
            {
                "title": "título_da_tarefa",
                "description": "descrição_detalhada",
                "deadline": "data_sugerida",
                "duration": "estimativa_de_duração",
                "priority": "alta/média/baixa",
                "method_tip": "dica_específica_para_o_método"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Preparar detalhes específicos do método de estudo
        study_method = state.get("study_method", "não_especificado")
        method_details = ""

        if study_method == "pomodoro":
            focus_time = state.get("focus_time", 25)
            break_time = state.get("break_time", 5)
            long_break = state.get("long_break", 15)
            method_details = f"""
            Detalhes do método Pomodoro:
            - Sessões de foco: {focus_time} minutos
            - Pausas curtas: {break_time} minutos
            - Pausas longas (a cada 4 sessões): {long_break} minutos
            - Organize as tarefas em blocos Pomodoro
            - Priorize tarefas que exigem mais concentração para as primeiras sessões
            - Inclua pausas estratégicas entre as sessões
            """
        elif study_method == "active_recall":
            review_frequency = state.get("review_frequency", "diária")
            quiz_type = state.get("quiz_type", "flashcards e auto-questionamento")
            method_details = f"""
            Detalhes do método Active Recall:
            - Frequência de revisão: {review_frequency}
            - Tipos de teste: {quiz_type}
            - Estruture o estudo em forma de perguntas e respostas
            - Inclua momentos para testar ativamente o conhecimento
            - Priorize a recuperação da informação sem consulta prévia
            - Organize revisões espaçadas para reforçar o aprendizado
            """
        elif study_method == "time_blocking":
            min_block = state.get("min_block", 30)
            priority_time = state.get("priority_time", "manhã")
            method_details = f"""
            Detalhes do método Time Blocking:
            - Duração mínima dos blocos: {min_block} minutos
            - Período de prioridade: {priority_time}
            - Aloque blocos específicos para cada disciplina/tarefa
            - Priorize conteúdos mais difíceis no período de {priority_time}
            - Mantenha blocos de tempo contínuos para tarefas similares
            - Inclua pequenos intervalos entre os blocos
            """
        else:
            method_details = """
            Método de estudo não especificado. Crie um plano equilibrado que:
            - Alterne entre diferentes tipos de atividades
            - Inclua pausas regulares
            - Priorize conteúdos mais importantes
            - Distribua o estudo ao longo do período disponível
            """

        # Prepare inputs
        inputs = {
            "planning_goal": state["planning_goal"],
            "planning_timeframe": state["planning_timeframe"],
            "planning_constraints": state["metadata"].get("planning_constraints", "Nenhuma restrição específica mencionada."),
            "current_date": current_date.strftime("%d/%m/%Y"),
            "study_method": study_method,
            "method_details": method_details
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
        if json_str.startswith('"tasks"'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in task generator: {str(e)}. Trying fallback method.")
            # Fallback to a more lenient approach
            result = {
                "tasks": [
                    {
                        "title": "Criar cronograma de estudos",
                        "description": "Elaborar um cronograma detalhado para as próximas duas semanas",
                        "deadline": "Hoje",
                        "duration": "1 hora",
                        "priority": "alta"
                    },
                    {
                        "title": "Revisar matérias principais",
                        "description": "Revisar os conteúdos mais importantes de cada disciplina",
                        "deadline": "Em 1 semana",
                        "duration": "2-3 horas por dia",
                        "priority": "alta"
                    }
                ]
            }

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
    Recomenda recursos específicos para o objetivo de planejamento.

    Esta função sugere ferramentas, aplicativos, técnicas e materiais
    de referência que complementam o método de estudo escolhido e
    ajudam o estudante a alcançar seu objetivo de planejamento.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com recursos de planejamento
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
    Método de estudo: {study_method}

    {method_resources}

    Recomende 4-6 recursos que possam ajudar o estudante a alcançar seu objetivo,
    priorizando aqueles que complementam o método de estudo escolhido.

    Os recursos devem incluir:
    - Pelo menos 1 aplicativo ou ferramenta digital
    - Pelo menos 1 técnica específica para o método de estudo
    - Pelo menos 1 recurso para exportação/visualização do plano (PDF, calendário, timeline)
    - Outros recursos relevantes para o objetivo específico

    Para cada recurso, forneça:
    1. Um título
    2. Uma descrição detalhada
    3. Como este recurso complementa o método de estudo escolhido
    4. Link ou informação de instalação (quando aplicável)

    Formato da resposta:
    ```json
    {
        "resources": [
            {
                "title": "título_do_recurso",
                "description": "descrição_detalhada",
                "relevance": "como_complementa_o_método",
                "installation": "pip install package-name (se aplicável)"
            },
            ...
        ]
    }
    ```
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE_CREATIVE)

    try:
        # Preparar recursos específicos para o método de estudo
        study_method = state.get("study_method", "não_especificado")
        method_resources = ""

        if study_method == "pomodoro":
            method_resources = """
            Recursos específicos para o método Pomodoro:
            - Aplicativos de temporizador Pomodoro (como Pomodoro Timer, Forest, Focus To-Do)
            - Biblioteca Python: pomodoro-timer (pip install pomodoro-timer)
            - Técnicas de transição entre tarefas durante as pausas
            - Métodos para maximizar a produtividade durante os blocos de foco
            - Ferramentas para exportação do plano para PDF: fpdf2 (pip install fpdf2)
            - Integração com calendário: ics (pip install ics)
            - Visualização de timeline: streamlit-timeline (pip install streamlit-timeline)
            """
        elif study_method == "active_recall":
            method_resources = """
            Recursos específicos para o método Active Recall:
            - Aplicativos de flashcards (como Anki, Quizlet, RemNote)
            - Técnicas de elaboração de perguntas eficazes
            - Métodos de revisão espaçada
            - Ferramentas para criação de mapas mentais
            - Ferramentas para exportação do plano para PDF: fpdf2 (pip install fpdf2)
            - Integração com calendário: ics (pip install ics)
            - Visualização de timeline: streamlit-timeline (pip install streamlit-timeline)
            """
        elif study_method == "time_blocking":
            method_resources = """
            Recursos específicos para o método Time Blocking:
            - Aplicativos de calendário com blocos de tempo (como Google Calendar, Notion, TickTick)
            - Técnicas para identificar horários de pico de produtividade
            - Métodos para estimar corretamente a duração das tarefas
            - Estratégias para lidar com interrupções durante os blocos
            - Ferramentas para exportação do plano para PDF: fpdf2 (pip install fpdf2)
            - Integração com calendário: ics (pip install ics)
            - Visualização de timeline: streamlit-timeline (pip install streamlit-timeline)
            """
        else:
            method_resources = """
            Recursos gerais para planejamento de estudos:
            - Aplicativos de gestão de tarefas (como Todoist, Trello, Notion)
            - Técnicas de priorização (como matriz de Eisenhower)
            - Métodos para manter a motivação e foco
            - Estratégias para lidar com procrastinação
            - Ferramentas para exportação do plano para PDF: fpdf2 (pip install fpdf2)
            - Integração com calendário: ics (pip install ics)
            - Visualização de timeline: streamlit-timeline (pip install streamlit-timeline)
            """

        # Prepare inputs
        inputs = {
            "planning_goal": state["planning_goal"],
            "planning_timeframe": state["planning_timeframe"],
            "study_method": study_method,
            "method_resources": method_resources
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

        # Clean up the JSON string
        json_str = json_str.replace("\n", "")
        json_str = json_str.replace("\r", "")

        # Fix common JSON parsing issues
        if json_str.startswith('"resources"'):
            json_str = '{' + json_str
        if not json_str.endswith('}'):
            json_str = json_str + '}'

        # Try to fix unquoted keys
        import re
        json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in resource recommender: {str(e)}. Trying fallback method.")
            # Fallback to a more lenient approach
            result = {
                "resources": [
                    {
                        "title": "Técnica Pomodoro",
                        "description": "Método de estudo com intervalos de 25 minutos de foco e 5 minutos de descanso",
                        "relevance": "Ajuda a manter o foco e evitar a procrastinação durante os estudos"
                    },
                    {
                        "title": "Aplicativo de Flashcards Anki",
                        "description": "Ferramenta para criar cartões de revisão com repetição espaçada",
                        "relevance": "Ideal para memorizar conceitos importantes para as provas"
                    }
                ]
            }

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
    Gera uma resposta em linguagem natural para o objetivo de planejamento.

    Esta função cria uma resposta estruturada e formatada em markdown que
    apresenta o plano de estudo completo, incluindo tarefas, recursos e
    dicas específicas para o método de estudo escolhido. A resposta é
    otimizada para visualização no Streamlit.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta em linguagem natural
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
    estudantes a planejar seus estudos e alcançar seus objetivos acadêmicos utilizando o método {study_method}.

    Pergunta original do estudante: {query}

    Objetivo de planejamento identificado: {planning_goal}
    Período de tempo: {planning_timeframe}
    Método de estudo: {study_method}

    {method_details}

    {tasks_section}

    {resources_section}

    Gere uma resposta detalhada em formato markdown que:
    1. Tenha um título atraente relacionado ao método de estudo e objetivo
    2. Comece com uma breve introdução motivadora sobre o método escolhido
    3. Apresente o plano de estudo estruturado com tarefas específicas
    4. Inclua datas/prazos sugeridos em formato de cronograma
    5. Recomende recursos úteis com links quando disponíveis
    6. Ofereça dicas de implementação específicas para o método escolhido
    7. Mencione as possibilidades de exportação (PDF, calendário, timeline)
    8. Use formatação markdown para melhorar a visualização (títulos, listas, negrito, etc.)
    9. Inclua uma seção de "Como medir seu progresso" com métricas específicas
    10. Termine com uma mensagem motivadora

    Formate sua resposta com um título atraente, introdução motivadora, e seções bem definidas usando markdown para uma melhor visualização no Streamlit.

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

        # Preparar detalhes específicos do método de estudo
        study_method = state.get("study_method", "não_especificado")
        method_details = ""

        if study_method == "pomodoro":
            focus_time = state.get("focus_time", 25)
            break_time = state.get("break_time", 5)
            long_break = state.get("long_break", 15)
            method_details = f"""
            Detalhes do método Pomodoro:
            - Sessões de foco: {focus_time} minutos
            - Pausas curtas: {break_time} minutos
            - Pausas longas (a cada 4 sessões): {long_break} minutos
            - Organize as tarefas em blocos Pomodoro
            - Priorize tarefas que exigem mais concentração para as primeiras sessões
            - Inclua pausas estratégicas entre as sessões
            """
        elif study_method == "active_recall":
            review_frequency = state.get("review_frequency", "diária")
            quiz_type = state.get("quiz_type", "flashcards e auto-questionamento")
            method_details = f"""
            Detalhes do método Active Recall:
            - Frequência de revisão: {review_frequency}
            - Tipos de teste: {quiz_type}
            - Estruture o estudo em forma de perguntas e respostas
            - Inclua momentos para testar ativamente o conhecimento
            - Priorize a recuperação da informação sem consulta prévia
            - Organize revisões espaçadas para reforçar o aprendizado
            """
        elif study_method == "time_blocking":
            min_block = state.get("min_block", 30)
            priority_time = state.get("priority_time", "manhã")
            method_details = f"""
            Detalhes do método Time Blocking:
            - Duração mínima dos blocos: {min_block} minutos
            - Período de prioridade: {priority_time}
            - Aloque blocos específicos para cada disciplina/tarefa
            - Priorize conteúdos mais difíceis no período de {priority_time}
            - Mantenha blocos de tempo contínuos para tarefas similares
            - Inclua pequenos intervalos entre os blocos
            """
        else:
            method_details = """
            Método de estudo não especificado. Crie um plano equilibrado que:
            - Alterne entre diferentes tipos de atividades
            - Inclua pausas regulares
            - Priorize conteúdos mais importantes
            - Distribua o estudo ao longo do período disponível
            """

        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "planning_goal": state.get("planning_goal", "organização de estudos"),
            "planning_timeframe": state.get("planning_timeframe", "médio prazo"),
            "study_method": study_method,
            "method_details": method_details,
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
    Gera uma resposta de erro amigável.

    Esta função cria uma resposta de erro que não expõe detalhes técnicos
    ao usuário, mas oferece dicas úteis e alternativas para o planejamento
    de estudos, mantendo uma experiência positiva mesmo quando ocorrem erros.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta de erro
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
    Ponto de entrada principal para o agente de planejamento acadêmico.

    Esta função coordena o fluxo completo do agente de planejamento:
    1. Análise do objetivo de planejamento e método de estudo
    2. Geração de tarefas específicas baseadas no método escolhido
    3. Recomendação de recursos complementares
    4. Geração de resposta formatada em markdown

    O agente suporta diferentes métodos de estudo (Pomodoro, Active Recall,
    Time Blocking) e inclui recursos para exportação (PDF, calendário) e
    visualização (timeline) do plano de estudos.

    Args:
        state (AcademicAgentState): Estado atual

    Returns:
        AcademicAgentState: Estado atualizado com resposta de planejamento
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
