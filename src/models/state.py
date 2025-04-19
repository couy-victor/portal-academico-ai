"""
State models for the Academic Agent system.
"""
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import NotRequired

class AcademicAgentState(TypedDict):
    """
    State model for the Academic Agent system.
    This represents the shared state that flows through the agent graph.
    """
    # Required fields
    user_query: str
    user_id: str
    user_context: Dict[str, Any]  # RA, curso, semestre atual, etc.

    # Optional fields populated during processing
    intent: NotRequired[str]  # classificação da intenção
    confidence: NotRequired[float]  # confiança na classificação
    schema_info: NotRequired[Dict[str, Any]]  # informações do schema
    generated_sql: NotRequired[str]  # SQL gerada
    validation_results: NotRequired[List[Dict[str, Any]]]  # resultados da validação
    query_results: NotRequired[List[Dict[str, Any]]]  # resultados da consulta
    error: NotRequired[str]  # qualquer erro que ocorra
    natural_response: NotRequired[str]  # resposta final
    from_cache: NotRequired[bool]  # indica se a resposta veio do cache

    # RAG fields
    rag_documents: NotRequired[List[Dict[str, Any]]]  # documentos recuperados pelo RAG
    rag_context: NotRequired[str]  # contexto extraído dos documentos

    # Tavily fields
    web_search_results: NotRequired[List[Dict[str, Any]]]  # resultados da busca na web
    web_search_context: NotRequired[str]  # contexto extraído da busca na web

    # Emotional Support fields
    emotional_state: NotRequired[str]  # estado emocional detectado
    emotional_issue: NotRequired[str]  # problema específico identificado
    emotional_strategies: NotRequired[List[Dict[str, Any]]]  # estratégias sugeridas
    emotional_resources: NotRequired[List[Dict[str, Any]]]  # recursos recomendados
    emotional_severity: NotRequired[str]  # nível de severidade (baixo, médio, alto)

    # Tutor fields
    subject: NotRequired[str]  # matéria identificada
    topic: NotRequired[str]  # tópico específico
    explanation: NotRequired[str]  # explicação gerada
    examples: NotRequired[List[Dict[str, Any]]]  # exemplos e exercícios
    comprehension_level: NotRequired[str]  # nível de compreensão do aluno

    # Academic Planning fields
    planning_goal: NotRequired[str]  # objetivo de planejamento
    planning_timeframe: NotRequired[str]  # período de tempo (curto, médio, longo prazo)
    planning_tasks: NotRequired[List[Dict[str, Any]]]  # tarefas planejadas
    planning_resources: NotRequired[List[Dict[str, Any]]]  # recursos para planejamento

    # Metadata for tracking and debugging
    metadata: NotRequired[Dict[str, Any]]  # metadados para rastreamento
