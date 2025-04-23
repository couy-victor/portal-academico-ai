"""
Query Validator Agent for the Academic Agent system.
Responsible for validating SQL queries for correctness and safety.
"""
import json
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.utils.logging import logger

def query_validator(state: AcademicAgentState) -> AcademicAgentState:
    """
    Validates the generated SQL query for correctness and safety.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with validation results
    """
    # Skip if we already have an error, coming from cache, or if we should skip validation
    if state.get("error") or state.get("from_cache", False) or state.get("skip_sql_generation", False):
        # If we're skipping validation due to web search, set empty validation results
        if state.get("skip_sql_generation", False):
            logger.info("Skipping SQL validation as requested by previous agent")
            state["validation_results"] = []
        return state

    # Create prompt for SQL validation
    prompt = ChatPromptTemplate.from_template("""
    Você é um especialista em validação de consultas SQL para sistemas acadêmicos.

    Pergunta original do usuário: {query}
    Intenção detectada: {intent}
    Consulta SQL gerada:
    ```sql
    {sql}
    ```

    Schema do banco de dados:
    {schema}

    Avalie a consulta SQL quanto a:
    1. Correção sintática
    2. Uso correto de tabelas e colunas conforme o schema
    3. Joins apropriados
    4. Condições de filtro adequadas
    5. Segurança (proteção contra SQL injection)
    6. Performance (uso de índices, limitação de resultados)

    Se encontrar problemas, sugira correções específicas.

    IMPORTANTE: Sua resposta deve ser APENAS um objeto JSON válido, sem texto adicional antes ou depois, no seguinte formato:

    {{
        "is_valid": true,
        "issues": [
            {{"type": "syntax/schema/security/performance", "description": "descrição do problema", "suggestion": "sugestão de correção"}}
        ],
        "corrected_sql": "consulta SQL corrigida (se aplicável)"
    }}

    Não inclua código markdown (```json) nem qualquer outro texto. Apenas o JSON puro.
    """)

    # Initialize LLM with low temperature for validation
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    try:
        # Prepare inputs
        inputs = {
            "query": state["user_query"],
            "intent": state.get("intent", "unknown"),
            "sql": state["generated_sql"],
            "schema": json.dumps(state["schema_info"], ensure_ascii=False, indent=2)
        }

        # Execute the validation
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
            validation_result = json.loads(json_str)
        except Exception as json_error:
            logger.error(f"Error parsing JSON in validator: {str(json_error)}. Response: {response_text[:100]}...")
            # Create a default result
            validation_result = {
                "is_valid": True,
                "issues": [],
                "corrected_sql": state["generated_sql"]
            }

        # Update state with validation results
        state["validation_results"] = validation_result.get("issues", [])

        # If validation failed, update SQL with corrected version
        if not validation_result.get("is_valid", True) and "corrected_sql" in validation_result:
            state["generated_sql"] = validation_result["corrected_sql"]
            logger.info(f"SQL corrected after validation: {validation_result['corrected_sql'][:100]}...")

        # Log validation results
        if validation_result.get("is_valid", True):
            logger.info("SQL validation passed")
        else:
            logger.warning(f"SQL validation found {len(validation_result.get('issues', []))} issues")

    except Exception as e:
        error_msg = f"Error validating SQL: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg

    return state
