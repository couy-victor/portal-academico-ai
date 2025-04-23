"""
SQL Generator Agent for the Academic Agent system.
Responsible for generating SQL queries based on user intent and database schema.
"""
import json
import re
from typing import Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def extract_sql_from_response(response_text: str) -> str:
    """
    Extracts SQL query from LLM response.

    Args:
        response_text (str): LLM response text

    Returns:
        str: Extracted SQL query
    """
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

    # If no code blocks, return the entire response
    return response_text.strip()

def validate_sql_syntax(sql: str) -> bool:
    """
    Performs basic SQL syntax validation.

    Args:
        sql (str): SQL query to validate

    Returns:
        bool: True if syntax is valid, False otherwise
    """
    # Check for basic SQL syntax
    sql_lower = sql.lower()

    # Must contain SELECT
    if "select" not in sql_lower:
        raise ValueError("Query must contain SELECT statement")

    # Check for balanced parentheses
    if sql.count('(') != sql.count(')'):
        raise ValueError("Unbalanced parentheses in query")

    # Check for common SQL injection patterns - but allow semicolons at the end
    dangerous_patterns = ["--", ";--", "/*", "*/", "@@", "@"]
    for pattern in dangerous_patterns:
        if pattern in sql:
            raise ValueError(f"Potentially unsafe SQL pattern detected: {pattern}")

    # Remove trailing semicolon if present
    if sql.strip().endswith(';'):
        sql = sql.strip()[:-1]

    return True

def sql_generator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Generates SQL query based on user intent and database schema.

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

    # Create prompt with ReAct technique and few-shot examples
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em SQL para sistemas acadêmicos.

    Pergunta do usuário: {query}
    Intenção detectada: {intent}
    Contexto do usuário: {context}

    Schema do banco de dados:
    {schema}

    Exemplos de consultas bem formadas:
    1. Pergunta: "Quantas faltas tenho em Anatomia?"
       SQL: SELECT COUNT(*) as total_faltas FROM presencas WHERE aluno_id = {{RA}} AND disciplina_id = (SELECT id FROM disciplinas WHERE nome = 'Anatomia' AND periodo_id = {{periodo_atual}})

    2. Pergunta: "Qual minha nota na prova 2 de Bioquímica?"
       SQL: SELECT valor FROM notas WHERE aluno_id = {{RA}} AND avaliacao_id = (SELECT id FROM avaliacoes WHERE nome = 'Prova 2' AND disciplina_id = (SELECT id FROM disciplinas WHERE nome = 'Bioquímica' AND periodo_id = {{periodo_atual}}))

    3. Pergunta: "Quais são minhas faltas em Teoria da Computação?"
       SQL: SELECT a.data, p.presente FROM aulas a JOIN presencas p ON a.id = p.aula_id WHERE p.aluno_id = {{RA}} AND a.disciplina_id = {{disciplina_id}}

    Raciocine passo a passo:
    1. Quais tabelas são relevantes para esta consulta?
    2. Quais joins são necessários?
    3. Quais condições de filtro devem ser aplicadas?
    4. Como garantir que a consulta seja eficiente (use índices, limite resultados)?
    5. Como parametrizar a consulta para evitar injeção SQL?

    Observações importantes:
    - Se o contexto do usuário contiver um campo 'disciplina_id', use-o diretamente nas consultas relacionadas a essa disciplina
    - IMPORTANTE: O número de matrícula do aluno é o campo 'RA' e deve ser usado diretamente nas consultas
    - Use {{RA}} para o número de matrícula do aluno e {{periodo_atual}} para o período atual
    - Nas tabelas do banco, o ID do aluno é armazenado na coluna 'aluno_id', mas você deve usar o RA do aluno
    - NÃO use {{user_id}} nas consultas, use {{RA}} em vez disso

    Gere apenas a consulta SQL final, sem explicações adicionais.

    ```sql
    """)

    # Initialize LLM with low temperature for SQL generation
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "intent": state.get("intent", "unknown"),
            "context": json.dumps(state["user_context"], ensure_ascii=False, indent=2),
            "schema": json.dumps(state["schema_info"], ensure_ascii=False, indent=2)
        }

        # Execute the generation
        response = llm.invoke(prompt.format_messages(**inputs))

        # Extract SQL from response
        sql_query = extract_sql_from_response(response.content)

        # Validate SQL syntax
        validate_sql_syntax(sql_query)

        # Update state with generated SQL
        state["generated_sql"] = sql_query

        # Log success with full SQL query for debugging
        logger.info(f"Generated SQL query: {sql_query}")
        print(f"\nSQL GERADO PELO AGENTE:\n{sql_query}\n")

    except Exception as e:
        error_msg = f"Error generating SQL: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg

    return state
