"""
NL2SQL Agent for the Academic Agent system.
Implements a LangGraph-based approach to convert natural language queries to SQL.
"""
import json
from typing import Dict, Any, List, TypedDict, Callable, Union

from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.models.state import AcademicAgentState
from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.utils.logging import logger
from src.database.supabase_client import get_schema_info

# Define the state for the NL2SQL graph
class NL2SQLState(TypedDict):
    question: str
    table_schemas: str
    sql: str
    reflect: List[str]
    accepted: bool
    revision: int
    max_revision: int
    user_context: Dict[str, Any]

def search_engineer_node(state: NL2SQLState) -> Dict[str, Any]:
    """
    Provides database schema information for SQL generation.

    Args:
        state (NL2SQLState): Current state

    Returns:
        Dict[str, Any]: Updated state with database schema
    """
    # Get schema information from Supabase
    schema_info = get_schema_info()

    # Format schema information for the SQL writer
    formatted_schema = format_schema_for_nl2sql(schema_info)

    # Update state with schema information
    state['table_schemas'] = formatted_schema

    return {"table_schemas": state['table_schemas']}

def senior_sql_writer_node(state: NL2SQLState) -> Dict[str, Any]:
    """
    Generates SQL query based on natural language question and database schema.

    Args:
        state (NL2SQLState): Current state

    Returns:
        Dict[str, Any]: Updated state with generated SQL
    """
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Create system prompt
    role_prompt = """
    Você é um especialista em SQL para sistemas acadêmicos. Sua tarefa é escrever **apenas** a consulta SQL que responda à pergunta do usuário. A consulta deve:

    - Usar a sintaxe SQL padrão.
    - Utilizar os nomes das tabelas e colunas conforme definidos no esquema do banco de dados.
    - Não incluir comentários, explicações ou qualquer texto adicional.
    - Não utilizar formatação de código ou markdown.
    - Retornar apenas a consulta SQL válida.
    - Usar parâmetros com a sintaxe :parametro para valores dinâmicos.
    - Usar {{RA}} para o número de matrícula do aluno.
    - NÃO usar {{user_id}} nas consultas, usar {{RA}} em vez disso.
    - Para campos de texto como 'status', 'nome', etc., SEMPRE use ILIKE ou LOWER() para comparações case-insensitive.
      Por exemplo: WHERE LOWER(status) = LOWER('vencido') ou WHERE status ILIKE '%vencido%'
    - Prefira usar ILIKE com '%texto%' para campos de status e outros campos de texto para evitar problemas de correspondência exata.
    """

    # Create instruction with schema and question
    instruction = f"Esquema do banco de dados:\n{state['table_schemas']}\n"

    # Add user context if available
    if 'user_context' in state and state['user_context']:
        instruction += f"Contexto do usuário:\n{json.dumps(state['user_context'], ensure_ascii=False, indent=2)}\n"

    # Add feedback from previous iterations if available
    if len(state['reflect']) > 0:
        instruction += f"Considere os seguintes feedbacks:\n{chr(10).join(state['reflect'])}\n"

    # Add the question
    instruction += f"Escreva a consulta SQL que responda à seguinte pergunta: {state['question']}\n"

    # Create messages for the LLM
    messages = [
        SystemMessage(content=role_prompt),
        HumanMessage(content=instruction)
    ]

    # Generate SQL query
    response = llm.invoke(messages)

    # Extract SQL from response
    sql_query = extract_sql_from_response(response.content)

    # Log the generated SQL
    logger.info(f"Generated SQL query: {sql_query}")
    print(f"\nSQL GERADO PELO AGENTE:\n{sql_query}\n")

    # Update state
    return {
        "sql": sql_query,
        "revision": state['revision'] + 1
    }

def senior_qa_engineer_node(state: NL2SQLState) -> Dict[str, Any]:
    """
    Validates the generated SQL query.

    Args:
        state (NL2SQLState): Current state

    Returns:
        Dict[str, Any]: Updated state with validation result
    """
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Create system prompt
    role_prompt = """
    Você é um engenheiro de QA especializado em SQL para sistemas acadêmicos. Sua tarefa é verificar se a consulta SQL fornecida responde corretamente à pergunta do usuário e segue as melhores práticas.

    Verifique:
    1. Se a consulta usa corretamente as tabelas e colunas do esquema
    2. Se a consulta responde à pergunta do usuário
    3. Se a consulta usa parâmetros corretamente (com :parametro ou {{parametro}})
    4. Se a consulta é segura e eficiente
    5. Se a consulta usa ILIKE ou LOWER() para comparações de texto, especialmente para campos como 'status', 'nome', etc.
       Por exemplo: WHERE LOWER(status) = LOWER('vencido') ou WHERE status ILIKE '%vencido%'

    Responda 'ACEITO' se a consulta estiver correta ou 'REJEITADO' se não estiver, seguido de uma explicação detalhada.
    Se a consulta não usar ILIKE ou LOWER() para comparações de texto, rejeite-a e sugira a correção.
    """

    # Create instruction
    instruction = f"Com base no seguinte esquema de banco de dados:\n{state['table_schemas']}\n"
    instruction += f"E na seguinte consulta SQL:\n{state['sql']}\n"
    instruction += f"Verifique se a consulta SQL pode completar a tarefa: {state['question']}\n"

    # Add user context if available
    if 'user_context' in state and state['user_context']:
        instruction += f"Contexto do usuário:\n{json.dumps(state['user_context'], ensure_ascii=False, indent=2)}\n"

    # Create messages for the LLM
    messages = [
        SystemMessage(content=role_prompt),
        HumanMessage(content=instruction)
    ]

    # Generate validation response
    response = llm.invoke(messages)

    # Check if the query is accepted
    is_accepted = 'ACEITO' in response.content.upper()

    # Log the validation result
    if is_accepted:
        logger.info("SQL validation passed")
    else:
        logger.info(f"SQL validation failed: {response.content}")

    # Update state
    return {"accepted": is_accepted}

def chief_dba_node(state: NL2SQLState) -> Dict[str, Any]:
    """
    Provides feedback to improve the SQL query.

    Args:
        state (NL2SQLState): Current state

    Returns:
        Dict[str, Any]: Updated state with feedback
    """
    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Create system prompt
    role_prompt = """
    Você é um DBA experiente especializado em sistemas acadêmicos. Sua tarefa é fornecer feedback detalhado para melhorar a consulta SQL fornecida.

    Considere:
    1. Otimização de performance (índices, joins, etc.)
    2. Segurança (prevenção de SQL injection)
    3. Legibilidade e manutenibilidade
    4. Uso correto de parâmetros
    5. Conformidade com o esquema do banco de dados

    Forneça recomendações específicas e detalhadas para melhorar a consulta.
    """

    # Create instruction
    instruction = f"Com base no seguinte esquema de banco de dados:\n{state['table_schemas']}\n"
    instruction += f"E na seguinte consulta SQL:\n{state['sql']}\n"
    instruction += f"Por favor, forneça recomendações úteis e detalhadas para ajudar a melhorar a consulta SQL para a tarefa: {state['question']}\n"

    # Add user context if available
    if 'user_context' in state and state['user_context']:
        instruction += f"Contexto do usuário:\n{json.dumps(state['user_context'], ensure_ascii=False, indent=2)}\n"

    # Create messages for the LLM
    messages = [
        SystemMessage(content=role_prompt),
        HumanMessage(content=instruction)
    ]

    # Generate feedback
    response = llm.invoke(messages)

    # Log the feedback
    logger.info(f"DBA feedback: {response.content}")

    # Update state
    return {"reflect": [response.content]}

def should_continue_revision(state: NL2SQLState) -> str:
    """
    Determines whether to continue revision or end the process.

    Args:
        state (NL2SQLState): Current state

    Returns:
        str: Next node or END
    """
    if state['accepted'] or state['revision'] >= state['max_revision']:
        return "end"
    else:
        return "revise"

def extract_sql_from_response(response_text: str) -> str:
    """
    Extracts SQL query from LLM response.

    Args:
        response_text (str): LLM response text

    Returns:
        str: Extracted SQL query
    """
    import re

    # Try to extract SQL from code blocks
    sql_pattern = r"```sql\s*(.*?)\s*```"
    matches = re.findall(sql_pattern, response_text, re.DOTALL)

    if matches:
        return matches[0].strip()

    # If no SQL code block, try to find any code block
    code_pattern = r"```\s*(.*?)\s*```"
    matches = re.findall(code_pattern, response_text, re.DOTALL)

    if matches:
        return matches[0].strip()

    # If no code blocks, try to extract SQL starting with SELECT
    select_pattern = r"(SELECT .*?)(;|$)"
    matches = re.findall(select_pattern, response_text, re.DOTALL | re.IGNORECASE)

    if matches:
        return matches[0][0].strip()

    # If all else fails, return the entire response
    return response_text.strip()

def format_schema_for_nl2sql(schema_info: Dict[str, Any]) -> str:
    """
    Formats database schema information for NL2SQL.

    Args:
        schema_info (Dict[str, Any]): Database schema information

    Returns:
        str: Formatted schema information
    """
    formatted_schema = ""

    # Check if schema_info has tables
    if "tables" not in schema_info:
        return "Esquema não disponível"

    # Format each table
    for table in schema_info["tables"]:
        table_name = table.get("name", "unknown")
        formatted_schema += f"Table: {table_name}\n"
        formatted_schema += "Columns:\n"

        # Format columns
        for column in table.get("columns", []):
            column_name = column.get("column_name", "unknown")
            data_type = column.get("data_type", "unknown")
            is_nullable = column.get("is_nullable", "YES")
            nullable_str = "NOT NULL" if is_nullable == "NO" else "NULL"

            formatted_schema += f" - {column_name} ({data_type}, {nullable_str})\n"

        # Format primary keys
        primary_keys = table.get("primary_keys", [])
        if primary_keys:
            formatted_schema += "Primary Keys: " + ", ".join(primary_keys) + "\n"

        # Format foreign keys
        foreign_keys = table.get("foreign_keys", [])
        if foreign_keys:
            formatted_schema += "Foreign Keys:\n"
            for fk in foreign_keys:
                column_name = fk.get("column_name", "unknown")
                foreign_table = fk.get("foreign_table_name", "unknown")
                foreign_column = fk.get("foreign_column_name", "unknown")
                formatted_schema += f" - {column_name} -> {foreign_table}.{foreign_column}\n"

        formatted_schema += "\n"

    return formatted_schema

def create_nl2sql_graph() -> Callable:
    """
    Creates and returns the NL2SQL graph.

    Returns:
        Callable: Compiled NL2SQL graph
    """
    # Create the graph
    builder = StateGraph(NL2SQLState)

    # Add nodes
    builder.add_node("search_engineer", search_engineer_node)
    builder.add_node("sql_writer", senior_sql_writer_node)
    builder.add_node("qa_engineer", senior_qa_engineer_node)
    builder.add_node("chief_dba", chief_dba_node)

    # Add edges
    builder.add_edge("search_engineer", "sql_writer")
    builder.add_edge("sql_writer", "qa_engineer")
    builder.add_edge("chief_dba", "sql_writer")

    # Add conditional edges
    builder.add_conditional_edges(
        "qa_engineer",
        lambda state: "end" if state['accepted'] or state['revision'] >= state['max_revision'] else "revise",
        {
            "end": END,
            "revise": "chief_dba"
        }
    )

    # Set entry point
    builder.set_entry_point("search_engineer")

    # Create a memory checkpointer
    memory_checkpointer = MemorySaver()

    # Compile the graph with the checkpointer
    return builder.compile(checkpointer=memory_checkpointer)

def nl2sql_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Converts natural language query to SQL using LangGraph.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with generated SQL
    """
    # Skip if we already have an error, coming from cache, or if we should skip SQL generation
    if state.get("error") or state.get("from_cache", False) or state.get("skip_sql_generation", False):
        # If we're skipping SQL generation due to web search, set a dummy SQL
        if state.get("skip_sql_generation", False):
            logger.info("Skipping SQL generation as requested by previous agent")
            state["generated_sql"] = "SELECT 1 AS dummy"
        return state

    try:
        # Create NL2SQL graph
        graph = create_nl2sql_graph()

        # Initialize NL2SQL state
        nl2sql_state = {
            'question': state["user_query"],
            'table_schemas': '',  # Will be filled by search_engineer_node
            'sql': '',
            'reflect': [],
            'accepted': False,
            'revision': 0,
            'max_revision': 2,
            'user_context': state["user_context"]
        }

        # Execute the graph
        thread = {"configurable": {"thread_id": state.get("user_id", "default")}}
        for s in graph.stream(nl2sql_state, thread):
            pass  # Processing is done internally

        # Get the final state
        final_state = graph.get_state(thread)

        # Update the original state with the generated SQL
        state["generated_sql"] = final_state.values['sql']

        # Log success
        logger.info(f"NL2SQL generated SQL: {state['generated_sql']}")

        return state

    except Exception as e:
        error_msg = f"Error in NL2SQL agent: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
        return state
