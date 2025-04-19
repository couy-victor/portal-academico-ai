"""
Test script to run the academic agent with a specific RA and disciplina.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import process_query
from src.agents.router_agent import intent_router
from src.agents.sql_generator_agent import sql_generator
from src.models.state import AcademicAgentState

# Load environment variables
load_dotenv()

def test_ra_specific():
    """
    Tests the academic agent with a specific RA and disciplina.
    """
    # Clear the cache to force schema retrieval
    from src.utils.cache import clear_cache
    clear_cache()
    print("Testing academic agent with specific RA and disciplina...")

    # Define a test query
    test_query = "Quantas faltas eu tenho em Teoria da Computação?"

    # Define user context with RA, user_id and disciplina_id
    user_context = {
        "RA": "201268",
        "user_id": "201268",  # Adicionando user_id igual ao RA
        "disciplina_id": "3e5e23c8-87d5-521e-90df-eecb69a8330a",
        "nome_disciplina": "Teoria da Computação"
    }

    print(f"\nQuery: {test_query}")
    print(f"User Context: {json.dumps(user_context, indent=2, ensure_ascii=False)}")

    # Test intent classification
    print("\n--- Testing Intent Classification ---")
    try:
        # Create initial state
        initial_state: AcademicAgentState = {
            "user_query": test_query,
            "user_id": "201268",
            "user_context": user_context
        }

        # Run router agent
        result_state = intent_router(initial_state)

        # Print results
        print(f"Intent: {result_state.get('intent', 'unknown')}")
        print(f"Confidence: {result_state.get('confidence', 0.0):.2f}")

        if "metadata" in result_state and "intent_reasoning" in result_state["metadata"]:
            print(f"Reasoning: {result_state['metadata']['intent_reasoning']}")
    except Exception as e:
        print(f"Error in intent classification: {str(e)}")

    # Test SQL generation
    print("\n--- Testing SQL Generation ---")
    try:
        # Create initial state with sample schema
        initial_state: AcademicAgentState = {
            "user_query": test_query,
            "user_id": "201268",
            "user_context": user_context,
            "intent": "faltas",
            "schema_info": {
                "tables": [
                    {
                        "name": "alunos",
                        "columns": [
                            {"column_name": "ra", "data_type": "varchar", "is_nullable": "NO"},
                            {"column_name": "pessoa_id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "curso_id", "data_type": "uuid", "is_nullable": "NO"}
                        ],
                        "primary_keys": ["ra"],
                        "foreign_keys": [
                            {"column_name": "pessoa_id", "foreign_table_name": "pessoas", "foreign_column_name": "id"},
                            {"column_name": "curso_id", "foreign_table_name": "cursos", "foreign_column_name": "id"}
                        ]
                    },
                    {
                        "name": "matriculas",
                        "columns": [
                            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "ra", "data_type": "varchar", "is_nullable": "NO"},
                            {"column_name": "disciplina_id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "periodo_letivo_id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "faltas", "data_type": "integer", "is_nullable": "YES"},
                            {"column_name": "status", "data_type": "varchar", "is_nullable": "YES"}
                        ],
                        "primary_keys": ["id"],
                        "foreign_keys": [
                            {"column_name": "ra", "foreign_table_name": "alunos", "foreign_column_name": "ra"},
                            {"column_name": "disciplina_id", "foreign_table_name": "disciplinas", "foreign_column_name": "id"},
                            {"column_name": "periodo_letivo_id", "foreign_table_name": "periodos_letivos", "foreign_column_name": "id"}
                        ]
                    },
                    {
                        "name": "disciplinas",
                        "columns": [
                            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "nome", "data_type": "varchar", "is_nullable": "NO"},
                            {"column_name": "codigo", "data_type": "varchar", "is_nullable": "YES"},
                            {"column_name": "curso_id", "data_type": "uuid", "is_nullable": "NO"}
                        ],
                        "primary_keys": ["id"],
                        "foreign_keys": [
                            {"column_name": "curso_id", "foreign_table_name": "cursos", "foreign_column_name": "id"}
                        ]
                    },
                    {
                        "name": "periodos_letivos",
                        "columns": [
                            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                            {"column_name": "ano", "data_type": "integer", "is_nullable": "NO"},
                            {"column_name": "semestre", "data_type": "integer", "is_nullable": "NO"},
                            {"column_name": "status", "data_type": "varchar", "is_nullable": "YES"}
                        ],
                        "primary_keys": ["id"],
                        "foreign_keys": []
                    }
                ]
            }
        }

        # Run SQL generator agent
        result_state = sql_generator(initial_state)

        # Print results
        print("\nGenerated SQL:")
        print(result_state.get("generated_sql", "No SQL generated"))
    except Exception as e:
        print(f"Error in SQL generation: {str(e)}")

    # Test full process
    print("\n--- Testing Full Process ---")
    try:
        # Process the query
        result = process_query(
            user_query=test_query,
            user_id="201268",
            user_context=user_context
        )

        # Print the result
        print("\nFull Process Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Print the response
        print(f"\nResponse: {result.get('response', '')}")
    except Exception as e:
        print(f"Error in full process: {str(e)}")

if __name__ == "__main__":
    test_ra_specific()
